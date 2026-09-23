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

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit(
        "§8.5 needs ANTHROPIC_API_KEY. Tool use is the part of the API that "
        "genuinely differs between providers, so this section uses the "
        "Anthropic SDK directly rather than the book's ask() wrapper. "
        "Everything above runs on either key.")

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
