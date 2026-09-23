"""The `ask()` wrapper from Appendix A, plus the provider plumbing.

The body of `ask()` is identical to the listing printed in Appendix A. The only
addition is `_call`, which picks a backend so the examples run whether you have
an Anthropic key or an OpenRouter one.
"""
import os

from dotenv import load_dotenv

load_dotenv()

# If your key file lives outside the repo, point PEB_ENV_FILE at it rather than
# copying the file in. One key file, one place to rotate it.
if os.getenv("PEB_ENV_FILE"):
    load_dotenv(os.environ["PEB_ENV_FILE"], override=False)

# Model ids as the book names them. The OpenRouter column is how the
# measurements were gathered; see Chapter 2 §2.5 on why that is an exploration
# tool and not what you should ship against.
MODELS = {
    "claude-opus-5":    ("claude-opus-5",     "anthropic/claude-opus-5"),
    "claude-sonnet-5":  ("claude-sonnet-5",   "anthropic/claude-sonnet-5"),
    "claude-haiku-4.5": ("claude-haiku-4-5-20251001", "anthropic/claude-haiku-4.5"),
    "gpt-5.6-terra":    (None,                "openai/gpt-5.6-terra"),
    "gemini-3.7-flash": (None,                "google/gemini-3.7-flash"),
}


def backend():
    """Which provider the examples will use, decided once."""
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("OPENROUTER_API_KEY"):
        return "openrouter"
    raise RuntimeError(
        "No key found. Copy .env.example to .env and set ANTHROPIC_API_KEY "
        "(or OPENROUTER_API_KEY to reproduce the book's own runs).")


_clients = {}


def _client(kind):
    if kind not in _clients:
        if kind == "anthropic":
            import anthropic
            _clients[kind] = anthropic.Anthropic()
        else:
            from openai import OpenAI
            _clients[kind] = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.environ["OPENROUTER_API_KEY"])
    return _clients[kind]


class Blocked(RuntimeError):
    """The platform refused the request before the model ran.

    Worth its own type. A blocked call is not a model behaviour and must never
    be scored as one -- counting it as "the model did not comply" would be a
    finding about a guardrail reported as a finding about a model.
    """


class _Usage:
    """Uniform usage object, so callers read the same fields either way."""

    def __init__(self, input_tokens, output_tokens):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    def __repr__(self):
        return f"Usage(in={self.input_tokens}, out={self.output_tokens})"


# The book used different models for different experiments, and says so in each
# chapter. A script defaults to the one its chapter used; PEB_MODEL overrides.
DEFAULT_MODEL = os.getenv("PEB_MODEL", "claude-opus-5")


def ask(prompt, model=None, max_tokens=2000, system=None, **kw):
    """Call the model and fail loudly on the two silent failures from Chapter 2.

    Returns (text, usage). Returning usage alongside the text is deliberate:
    see Chapter 1 §1.6.
    """
    kind = backend()
    model = model or DEFAULT_MODEL
    anthropic_id, openrouter_id = MODELS.get(model, (model, model))

    if kind == "anthropic":
        if anthropic_id is None:
            raise RuntimeError(
                f"{model} is not an Anthropic model. Use OPENROUTER_API_KEY "
                f"for the cross-provider comparisons.")
        msgs = [{"role": "user", "content": prompt}]
        if system:
            kw["system"] = system
        r = _client(kind).messages.create(
            model=anthropic_id, max_tokens=max_tokens, messages=msgs, **kw)
        text = "".join(b.text for b in r.content if b.type == "text")
        stop, usage = r.stop_reason, _Usage(r.usage.input_tokens, r.usage.output_tokens)
    else:
        msgs = ([{"role": "system", "content": system}] if system else []) + \
               [{"role": "user", "content": prompt}]
        r = _client(kind).chat.completions.create(
            model=openrouter_id, max_tokens=max_tokens, messages=msgs, **kw)
        if not getattr(r, "choices", None):
            # An aggregator can return a body with no choices at all -- an
            # upstream error surfaced as a 200. §2.5 on why that is the
            # aggregator's failure mode specifically.
            raise RuntimeError(f"No choices in response: {getattr(r, 'error', r)!r}")
        choice = r.choices[0]
        # A platform content filter is a THIRD outcome, distinct from a model
        # refusal and from a successful call. It has no usage and no text, and
        # collapsing it into either one loses the only fact that matters: the
        # request never reached the model.
        if choice.finish_reason == "content_filter":
            raise Blocked(getattr(choice.message, "refusal", None)
                          or "blocked by a platform content filter")
        text = choice.message.content or ""
        stop = "max_tokens" if choice.finish_reason == "length" else choice.finish_reason
        # usage can be absent on a response that still carries text. Defaulting
        # it to zero is fine ONLY when there is text; when there is neither text
        # nor usage, the call did not happen and zero is a lie. Returning that
        # quietly is the exact bug §13.1 opens with -- a silent failure the
        # caller scores as a pass -- so it raises instead.
        u = getattr(r, "usage", None)
        if u is None and not text.strip():
            try:
                body = r.model_dump()
            except Exception:
                body = repr(r)
            raise RuntimeError(
                f"Empty response with no usage: the call did not produce "
                f"anything. Full body: {body}")
        usage = _Usage(getattr(u, "prompt_tokens", 0) or 0,
                       getattr(u, "completion_tokens", 0) or 0) if u else _Usage(0, 0)

    # The two guard clauses from Appendix A, verbatim in spirit.
    if stop == "max_tokens" and not text.strip():
        raise RuntimeError(
            f"Empty response: the output budget ({max_tokens}) was consumed by "
            f"thinking. Raise max_tokens or lower effort. See §2.3.")
    if stop == "max_tokens":
        raise RuntimeError(f"Truncated at {max_tokens} tokens. See §2.3.")
    if not text.strip():
        # Whatever the stop reason, an empty string is not an answer. §13.1:
        # if your checker can return nothing, treat nothing as a failure.
        raise RuntimeError(f"Empty response (stop_reason={stop!r}). See §13.1.")

    return text, usage
