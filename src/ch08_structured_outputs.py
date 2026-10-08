# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Chapter 8 — Structured Outputs and Tool Use
#
# | § | what it shows |
# |---|---|
# | 8.1 | "reply with JSON only", and what actually comes back |
# | 8.2 | the same request with a schema |
# | 8.4 | a tool definition is a prompt, and the description is the prompt |
# | 8.5 | the tool loop |
#
# Tool use is where provider APIs genuinely differ, so §8.5 uses the Anthropic
# SDK directly rather than the book's `ask()` wrapper. It needs
# `ANTHROPIC_API_KEY`.

# %%
import json
import re

from peb import ask
from peb.fixtures import REVIEW

# %% [markdown]
# ## §8.1 "Reply with JSON only" is a request, not a guarantee

# %%
naive = """Extract order_ref and fault_count from this review as JSON.
Reply with JSON only.

Review: Drip tray warped after a week. Order ref KL-449021."""

clean = 0
for i in range(8):
    text, _ = ask(naive, max_tokens=4000)
    stripped = text.strip()
    clean += stripped.startswith("{") and stripped.endswith("}")
    if i == 0:
        print(f"first reply: {stripped[:70]!r}")

print(f"\nparsed without repair: {clean}/8 — the code fences are the usual culprit.")

# %% [markdown]
# ## §8.2 The same extraction, with a schema
#
# Note `"type": ["string", "null"]` on `order_ref`. A field that is allowed to
# be absent needs somewhere to *put* that absence, or the model invents a
# plausible value — §6.4's escape hatch, in schema form.

# %%
schema = {
    "type": "object",
    "properties": {
        "order_ref":       {"type": ["string", "null"],
                            "description": "Format KL- followed by six digits, or null"},
        "days_to_deliver": {"type": ["integer", "null"]},
        "fault_count":     {"type": "integer"},
        "faults":          {"type": "array", "items": {"type": "string"}},
        "sentiment":       {"type": "string",
                            "enum": ["positive", "negative", "mixed"]},
    },
    "required": ["order_ref", "days_to_deliver", "fault_count",
                 "faults", "sentiment"],
    "additionalProperties": False,
}

prompt = (f"Extract the fields defined by this JSON Schema from the review.\n"
          f"Reply with one JSON object and nothing else.\n\n"
          f"Schema:\n{json.dumps(schema, indent=2)}\n\nReview: ```{REVIEW}```")

ok = 0
for _ in range(8):
    text, _ = ask(prompt, max_tokens=4000)
    m = re.search(r"\{.*\}", text, re.S)
    try:
        ok += set(schema["required"]) <= set(json.loads(m.group(0)))
    except Exception:
        pass

print(f"valid against required keys: {ok}/8")

# %% [markdown]
# ## §8.4 A tool definition is a prompt
#
# The `description` is doing the work. Both of these say when to use the tool
# *and* when not to — the same two clauses a skill description needs (§11.2).

# %%
get_order = {
    "name": "get_order",
    "description": ("Look up exactly one order using its full reference. "
                    "The reference format is KL- followed by six digits. "
                    "Use only when the user has supplied such a reference."),
    "strict": True,   # §8.5: without this the schema is advisory
    "input_schema": {
        "type": "object",
        "properties": {"order_ref": {"type": "string"}},
        "required": ["order_ref"],
        "additionalProperties": False,
    },
}

search_orders = {
    "name": "search_orders",
    "description": ("Search orders by customer name, product or date range when no "
                    "order reference is available. Returns up to 20 matches."),
    "strict": True,   # §8.5: without this the schema is advisory
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
        "additionalProperties": False,
    },
}

ORDERS = {"KL-449021": {"ref": "KL-449021", "product": "Nordic 400",
                        "ordered": "2026-03-03", "delivered": "2026-03-11"}}


def run_tool(name, args):
    if name == "get_order":
        return json.dumps(ORDERS.get(args["order_ref"], {"error": "not found"}))
    if name == "search_orders":
        return json.dumps(list(ORDERS.values()))
    return json.dumps({"error": f"unknown tool {name}"})


# %% [markdown]
# ## §8.5 The tool loop
#
# Two details worth copying: every tool result for one turn goes back in a
# **single** user message, and an error is returned *as a result* rather than
# raised — the model can recover from a result it can read.

# %%
import os

# Skip, do not exit. SystemExit here killed every experiment appended after this
# cell -- the three §8.3-8.5 experiments ran zero times and the script still
# reported success, which is §13.1's silent-pass failure in the harness itself.
HAVE_ANTHROPIC = bool(os.getenv("ANTHROPIC_API_KEY"))
if not HAVE_ANTHROPIC:
    print("§8.5's native tool loop needs ANTHROPIC_API_KEY and is SKIPPED. Tool "
          "use is the part of the API that genuinely differs between providers. "
          "Everything else in this chapter runs on either key.")

if HAVE_ANTHROPIC:
    import anthropic

    client = anthropic.Anthropic()

    messages = [{"role": "user",
                 "content": "What did I order on KL-449021, and when did it arrive?"}]
    turns = 0

    while True:
        response = client.messages.create(
            model="claude-opus-5", max_tokens=4000,
            tools=[get_order, search_orders],
            messages=messages,
        )
        if response.stop_reason != "tool_use":
            break
        turns += 1
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"-> {block.name}({block.input})")
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": run_tool(block.name, block.input),
                })
        messages.append({"role": "user", "content": results})

    final = "".join(b.text for b in response.content if b.type == "text")
    print(f"\nafter {turns} tool turn(s): {final.strip()[:240]}")

# %% [markdown]
# ## The three experiments §8.3–8.5 publish
#
# Provenance for all three: `claude-opus-5`, default sampling, run date in
# `outputs/run-log.jsonl`, scoring in this file.
#
# One design note the chapter leaves unrecoverable. §8.5 says "six queries that
# clearly want one or the other", then reports denominators of 20, 20 and 30.
# Six queries cannot give 20 or 30 without a repeat count, and none is stated.
# Five repeats over six queries gives 30, so that is what runs here; nothing
# produces 20, so the first attempt's denominator could not be reconstructed.

# %%
import collections
import json
import re

from peb import ask
from peb.checks import wilson

MODEL = "claude-opus-5"
RUNS = 8

# %% [markdown]
# ### §8.3 An enum is not a suggestion
#
# The same classification twice: once asking in prose for one of three labels,
# once giving the same three as a schema enum. Scored on whether the reply is
# exactly one of the permitted values.

# %%
LABELS = ["positive", "negative", "mixed"]
TEXTS = [
    "It arrived. It is a kettle. It boils water.",
    "Not what I hoped for, though I suppose it does the job.",
    "Fine I guess?? idk, works ok, delivery was whatever",
]

PROSE = ("Classify the sentiment of this review as positive, negative or mixed.\n"
         "Reply with the label only.\n\nReview: ```{t}```")

SCHEMA = {"type": "object",
          "properties": {"sentiment": {"type": "string", "enum": LABELS}},
          "required": ["sentiment"],
          "additionalProperties": False}

# NOT an f-string or .format() target: the schema contains braces, and
# str.format reads them as placeholders. KeyError: '\n  "type"'.
ENUM = ("Classify the sentiment of this review.\n"
        "Reply with one JSON object matching this schema and nothing else.\n\n"
        + json.dumps(SCHEMA, indent=2) + "\n\nReview: ```<<T>>```")


def exact_label(text):
    return text.strip().strip(".\"'`").lower() in LABELS


def schema_label(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return False
    try:
        return json.loads(m.group(0)).get("sentiment") in LABELS
    except Exception:
        return False


for label, template, scorer in (("prose, 'reply with the label only'", PROSE, exact_label),
                                ("the same three as a schema enum", ENUM, schema_label)):
    ok = 0
    for t in TEXTS:
        for _ in range(RUNS):
            prompt = (template.replace("<<T>>", t) if "<<T>>" in template
                      else template.format(t=t))
            ok += scorer(ask(prompt, model=MODEL, max_tokens=4000)[0])
    n = len(TEXTS) * RUNS
    lo, hi = wilson(ok, n)
    print(f"{label:<36} {ok:>2}/{n}   95% CI [{lo:.0%}, {hi:.0%}]")

print("\nPublished in §8.3: eight runs each.")

# %% [markdown]
# ### §8.4 A nested schema
#
# Four levels deep. The question is whether the shape survives, not whether the
# values are right.

# %%
NESTED = {
    "type": "object",
    "properties": {
        "order": {
            "type": "object",
            "properties": {
                "ref": {"type": "string"},
                "delivery": {
                    "type": "object",
                    "properties": {
                        "promised_days": {"type": "integer"},
                        "actual_days": {"type": "integer"},
                        "breach": {
                            "type": "object",
                            "properties": {
                                "is_breach": {"type": "boolean"},
                                "days_over": {"type": "integer"},
                            },
                            "required": ["is_breach", "days_over"],
                        },
                    },
                    "required": ["promised_days", "actual_days", "breach"],
                },
            },
            "required": ["ref", "delivery"],
        },
    },
    "required": ["order"],
}


def shape_ok(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return False
    try:
        o = json.loads(m.group(0))
        b = o["order"]["delivery"]["breach"]
        return isinstance(b["is_breach"], bool) and isinstance(b["days_over"], int)
    except Exception:
        return False


from peb.fixtures import REVIEW

prompt = ("Extract the order and delivery detail from the review.\n"
          "Reply with one JSON object matching this schema and nothing else.\n"
          "Promised delivery is 3 days.\n\n"
          + json.dumps(NESTED, indent=2) + f"\n\nReview: ```{REVIEW}```")

ok = sum(shape_ok(ask(prompt, model=MODEL, max_tokens=4000)[0]) for _ in range(6))
lo, hi = wilson(ok, 6)
print(f"four-level nested shape intact   {ok}/6   95% CI [{lo:.0%}, {hi:.0%}]")
print("Published in §8.4: 6 of 6.")

# %% [markdown]
# ### §8.5 Tool descriptions are prompts
#
# Two tools, six queries, five repeats — 30 trials per condition. The only thing
# that changes between conditions is the `description` field.
#
# The tool *names* are deliberately opaque in both conditions. Naming them
# `get_stock` and `get_order_status` would let the model route on the label and
# the experiment would measure nothing — which is the confound §9.4 reports
# catching.

# %%
_SAME = "Looks up information in the system and returns what it finds."
VAGUE = [
    {"name": "tool_a", "description": _SAME},
    {"name": "tool_b", "description": _SAME},   # byte-identical, deliberately
]
PRECISE = [
    {"name": "tool_a", "description": ("Return the current warehouse stock level for one "
                                       "product code, e.g. CEM-22. Use when the user asks "
                                       "how many of something is held. Do not use for "
                                       "orders or deliveries.")},
    {"name": "tool_b", "description": ("Return the delivery status of one order using its "
                                       "reference, format KL- plus six digits. Use when the "
                                       "user asks where an order is. Do not use for stock "
                                       "levels.")},
]

QUERIES = [
    ("How many units of CEM-22 are in the warehouse?", "tool_a"),
    ("Where has order KL-449021 got to?", "tool_b"),
    ("Do we have any TIM-04 left?", "tool_a"),
    ("Has KL-318402 been delivered yet?", "tool_b"),
    ("What is our stock level for SAN-11?", "tool_a"),
    ("I need the status of order KL-900145.", "tool_b"),
]
REPEATS = 5

for label, tools in (("identical vague descriptions", VAGUE),
                     ("precise descriptions", PRECISE)):
    right = 0
    picked = collections.Counter()
    for q, want in QUERIES:
        for _ in range(REPEATS):
            text, _ = ask(f"Choose exactly one tool and reply with its name only.\n\n"
                          f"{json.dumps(tools, indent=2)}\n\nRequest: {q}",
                          model=MODEL, max_tokens=4000)
            got = text.strip().split()[0].strip(".,'\"`") if text.strip() else "no call"
            got = got if got in ("tool_a", "tool_b") else "no call at all"
            picked[got] += 1
            right += got == want
    n = len(QUERIES) * REPEATS
    lo, hi = wilson(right, n)
    detail = "  ".join(f"{k} {v}" for k, v in sorted(picked.items()))
    print(f"{label:<30} {right}/{n}   {detail}")
    print(f"{'':<30} 95% CI [{lo:.0%}, {hi:.0%}]")

print("\nPublished in §8.5: 23/30 then 30/30.")
