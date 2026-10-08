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


def _log(model, max_tokens, prompt, text, usage, stop):
    """Append one line per call to PEB_RUN_LOG, if it is set.

    The book asks every result to carry its model, date and sample size. This is
    where those come from: a JSONL record per call, which the run summary reads
    back. Off unless the variable is set, so it changes nothing by default.
    """
    path = os.getenv("PEB_RUN_LOG")
    if not path:
        return
    import datetime, json, traceback
    # Which chapter script is calling, taken from the stack rather than passed in.
    script = "unknown"
    for frame in traceback.extract_stack()[:-2][::-1]:
        name = os.path.basename(frame.filename)
        if name.startswith(("ch", "appendix")):
            script = name
            break
    rec = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "script": script,
        "model": model,
        "backend": backend(),
        "max_tokens": max_tokens,
        "stop_reason": stop,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "prompt_chars": len(prompt),
        "reply_chars": len(text),
    }
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")


def ask(prompt, model=None, max_tokens=2000, system=None, raise_on_empty=True, **kw):
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
            # Log it before raising. A blocked call is an outcome, and leaving it
            # out of the record makes the sample size in the log disagree with
            # the sample size the experiment actually attempted.
            _log(model, max_tokens, prompt, "", _Usage(0, 0), "content_filter")
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

    # §2.3 demonstrates these guards, which means one script has to be able to
    # see past them: raise_on_empty=False returns the starved reply so the
    # chapter can print its stop_reason and token count. Nothing else should
    # use it -- the whole argument of §13.1 is that silence must be a failure.
    if not raise_on_empty:
        _log(model, max_tokens, prompt, text, usage, stop)
        return text, usage, stop

    # The three guard clauses from Appendix A.
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

    _log(model, max_tokens, prompt, text, usage, stop)
    return text, usage


# --- the tool loop ----------------------------------------------------------
# Chapters 8 and 9 both need a real loop: tools declared to the API, a tool_use
# block back, a tool_result returned, and another turn. The shipped ch09 script
# had none of that -- it pasted the tool definition in as text and evaluated the
# reply locally, which cannot produce a multi-call trace and cannot return an
# error to the model. §9.2's central claim depends on the latter.

def _to_openai_tool(t):
    """Anthropic tool shape -> OpenAI/OpenRouter shape."""
    return {"type": "function",
            "function": {"name": t["name"],
                         "description": t["description"],
                         "parameters": t["input_schema"]}}


def run_tools(prompt, tools, run_tool, model=None, max_tokens=2000,
              max_turns=3, system=None, trace=None):
    """Run an agent loop and return (final_text, turns, usage_totals).

    `run_tool(name, args) -> str` executes one call. Errors should be RETURNED
    as a string, not raised: §9.2's finding is that a model recovers from an
    error it can read, and it cannot read an exception.

    `max_turns` is a hard cap. An uncapped agent loop is an outage, §12.3.
    `trace` is an optional list that receives one dict per turn.
    """
    kind = backend()
    model = model or DEFAULT_MODEL
    anthropic_id, openrouter_id = MODELS.get(model, (model, model))
    tin = tout = turns = 0

    if kind == "anthropic":
        import anthropic
        client = _client(kind)
        msgs = [{"role": "user", "content": prompt}]
        kw = {"system": system} if system else {}
        for _ in range(max_turns):
            r = client.messages.create(model=anthropic_id, max_tokens=max_tokens,
                                       tools=tools, messages=msgs, **kw)
            tin += r.usage.input_tokens; tout += r.usage.output_tokens
            if r.stop_reason != "tool_use":
                text = "".join(b.text for b in r.content if b.type == "text")
                return text, turns, _Usage(tin, tout)
            turns += 1
            msgs.append({"role": "assistant", "content": r.content})
            results = []
            for b in r.content:
                if b.type == "tool_use":
                    out = run_tool(b.name, b.input)
                    if trace is not None:
                        trace.append({"turn": turns, "tool": b.name,
                                      "args": b.input, "result": out})
                    results.append({"type": "tool_result", "tool_use_id": b.id,
                                    "content": out})
            msgs.append({"role": "user", "content": results})
        return "", turns, _Usage(tin, tout)

    # OpenRouter / OpenAI-compatible
    import json as _json
    client = _client(kind)
    msgs = ([{"role": "system", "content": system}] if system else []) + \
           [{"role": "user", "content": prompt}]
    oa_tools = [_to_openai_tool(t) for t in tools]
    for _ in range(max_turns):
        r = client.chat.completions.create(model=openrouter_id, max_tokens=max_tokens,
                                           tools=oa_tools, messages=msgs)
        if not getattr(r, "choices", None):
            raise RuntimeError(f"No choices: {getattr(r, 'error', r)!r}")
        u = getattr(r, "usage", None)
        if u:
            tin += u.prompt_tokens or 0; tout += u.completion_tokens or 0
        m = r.choices[0].message
        if not getattr(m, "tool_calls", None):
            return (m.content or ""), turns, _Usage(tin, tout)
        turns += 1
        msgs.append({"role": "assistant", "content": m.content,
                     "tool_calls": [{"id": c.id, "type": "function",
                                     "function": {"name": c.function.name,
                                                  "arguments": c.function.arguments}}
                                    for c in m.tool_calls]})
        for c in m.tool_calls:
            try:
                args = _json.loads(c.function.arguments or "{}")
            except Exception as e:
                args, out = {}, f"error: could not parse arguments: {e}"
            else:
                out = run_tool(c.function.name, args)
            if trace is not None:
                trace.append({"turn": turns, "tool": c.function.name,
                              "args": args, "result": out})
            msgs.append({"role": "tool", "tool_call_id": c.id, "content": out})
    return "", turns, _Usage(tin, tout)
