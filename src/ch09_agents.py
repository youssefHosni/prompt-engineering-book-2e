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
# # Chapter 9 — From Chains to Agents
#
# | § | what it shows |
# |---|---|
# | 9.1 | one general tool beats five specific ones |
# | 9.4 | routing — and the confound that ruined the first version |
#
# The §9.4 confound is worth stating up front: the first version named the tools
# `get_hours`, `get_order_status` and `get_stock`. The model was reading the
# labels, not the descriptions, so the experiment measured nothing. The names
# here are deliberately opaque.

# %%
import json

from peb import ask
from peb.checks import evaluate

ROWS = [
    {"depot": "Leeds",  "pallets": 120, "product": "cement"},
    {"depot": "Leeds",  "pallets": 80,  "product": "timber"},
    {"depot": "Hull",   "pallets": 140, "product": "cement"},
    {"depot": "Hull",   "pallets": 60,  "product": "sand"},
    {"depot": "Oldham", "pallets": 72,  "product": "timber"},
]

# %% [markdown]
# ## §9.1 One general tool over a fixed table
#
# `evaluate()` restricts rather than isolates. That is a speed bump, not a
# sandbox — §15.4 is the honest version, and anything real runs somewhere it
# cannot reach your filesystem.

# %%
run_python = {
    "name": "run_python",
    "description": ("Evaluate a single Python expression over the depot log and "
                    "return its value. The variable `rows` is a list of dicts, "
                    "each with keys: depot (str), pallets (int), product (str). "
                    "Only an expression, not statements."),
    "input_schema": {
        "type": "object",
        "properties": {"code": {"type": "string"}},
        "required": ["code"],
    },
}

questions = [
    "How many pallets of cement in total?",
    "Which depot moved the most pallets?",
    "What was the average customer satisfaction score for cement deliveries?",
]

for q in questions:
    prompt = (f"You may call one tool.\n\nTool: {json.dumps(run_python)}\n\n"
              f"Question: {q}\n\nReply with JSON: "
              f'{{"code": "<expression>"}} or {{"answer": "<why you cannot>"}}')
    text, _ = ask(prompt, max_tokens=4000)
    try:
        call = json.loads(text[text.index("{"):text.rindex("}") + 1])
    except Exception:
        print(f"{q}\n  unparseable: {text.strip()[:60]!r}\n")
        continue
    if "code" in call:
        print(f"{q}\n  code   {call['code'][:70]}\n  result {evaluate(call['code'], ROWS)}\n")
    else:
        print(f"{q}\n  declined: {call['answer'][:70]}\n")

# %% [markdown]
# The third question has no answer in the data, and that is the point: a tool
# that can compute anything will happily compute nonsense unless declining is an
# available move.
#
# ## §9.4 Routing on descriptions, not on names

# %%
ROUTING_TOOLS = [
    {"name": "tool_a", "description": "Return the current stock level for one product code."},
    {"name": "tool_b", "description": "Return the delivery status of one order reference."},
    {"name": "tool_c", "description": "Return the opening hours of one depot."},
]

ROUTING_CASES = [
    ("Is the Leeds depot open on Saturday?", "tool_c"),
    ("Where has order KL-449021 got to?",    "tool_b"),
    ("How many units of CEM-22 do we hold?", "tool_a"),
]

right = 0
for q, expect in ROUTING_CASES:
    prompt = (f"Choose exactly one tool. Reply with its name only.\n\n"
              f"{json.dumps(ROUTING_TOOLS, indent=2)}\n\nRequest: {q}")
    text, _ = ask(prompt, max_tokens=4000)
    got = text.strip().split()[0].strip(".,'\"") if text.strip() else ""
    right += (got == expect)
    print(f"{q[:44]:<46} -> {got:<8} (want {expect})")

print(f"\n{right}/{len(ROUTING_CASES)} correct.")
