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

# The real log, not a five-row stub. §2.6 and §9.1 both rest on it, and they
# share a ground truth, so neither can be re-run without it.
from peb.depot_log import DEPOT_LOG as ROWS, as_text

TRUTH_ENTRIES = sum(1 for r in ROWS if r["product"] == "cement")
TRUTH_PALLETS = sum(r["pallets"] for r in ROWS if r["product"] == "cement")
print(f"log: {len(ROWS)} rows   cement: {TRUTH_ENTRIES} entries, "
      f"{TRUTH_PALLETS} pallets   (§9.1 ground truth: 56, 2812)")

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
        # §8.3 says to set this, and ch09's definition did not.
        "additionalProperties": False,
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


# %% [markdown]
# ## §9.1 The same question, two architectures
#
# Chapter 2 pasted 520 rows into the prompt and asked the model to aggregate
# them. It could not. Here the model gets one tool and the rows stay out of the
# context entirely.
#
# This is a real loop: the tool is declared to the API, the model returns a
# tool-use block, the result goes back as a tool result, and the model answers
# from it. The earlier version of this script pasted the tool definition in as
# text and evaluated the reply locally, which cannot produce a multi-call trace
# and — more importantly — cannot return an error to the model. §9.2 depends on
# exactly that.

# %%
from peb import run_tools

TOOL = {
    "name": "run_python",
    "description": ("Evaluate a single Python expression over the depot log and "
                    "return its value. The variable `rows` is a list of dicts, "
                    "each with keys: depot (str), pallets (int), product (str). "
                    "Only an expression, not statements."),
    "input_schema": {
        "type": "object",
        "properties": {"code": {"type": "string"}},
        "required": ["code"],
        "additionalProperties": False,
    },
}

QUESTION = ("How many entries in the depot log record a cement delivery, and how "
            "many pallets of cement in total? Use the tool. Answer as "
            "'entries=<n>, pallets=<n>'.")


def tool(name, args):
    return evaluate(args.get("code", ""), ROWS)


trace = []
# A generous cap, as §9.4 argues: well above what a healthy run needs, with
# alerting on runs that approach it. Exhausting it raises; it does not return
# an empty answer.
answer, turns, usage = run_tools(QUESTION, [TOOL], tool, max_tokens=2000,
                                 max_turns=10, trace=trace)

for t in trace:
    print(f"call {t['turn']}:  {t['args'].get('code','')[:88]}")
    print(f"   ->    {t['result'][:88]}")
print(f"\nfinal:   {answer.strip()[:120]}")
print(f"turns:   {turns}   input tokens: {usage.input_tokens}")

import re as _re
nums = [int(n) for n in _re.findall(r"\d+", answer.replace(",", ""))]
correct = TRUTH_ENTRIES in nums and TRUTH_PALLETS in nums
print(f"correct: {correct}   (truth {TRUTH_ENTRIES}, {TRUTH_PALLETS})")

# %% [markdown]
# ### The cost of the two architectures
#
# The comparison §9.1 publishes is the rows-in-prompt run against the one-tool
# run. The first number is what Chapter 2 spent to get an empty string.

# %%
log_text = as_text()
# A reasoning model given 520 rows to aggregate spends a great deal of the
# output budget thinking, so this needs headroom. The §2.3 guard fired at 2000.
_, u_ctx = ask(f"{log_text}\n\n{QUESTION}", max_tokens=8000)
print(f"rows in prompt    input tokens {u_ctx.input_tokens:>7}")
print(f"one tool          input tokens {usage.input_tokens:>7}")
print(f"ratio             {u_ctx.input_tokens / max(usage.input_tokens, 1):>7.1f}x")
print("\nPublished in §9.1: 21,226 against 1,195. This log is a reconstruction,")
print("so the absolute figures differ; the ratio is the finding.")

# %% [markdown]
# ## §9.2 An error returned as a tool result
#
# The claim is that the model recovers from an error *because the error came
# back as a tool result it could read*. That is testable: give it a tool that
# fails on the first call, and watch whether the second call differs.

# %%
calls = {"n": 0}


def flaky(name, args):
    calls["n"] += 1
    if calls["n"] == 1:
        # A realistic first failure: the model guesses a column that is not there.
        return "error: KeyError('tonnage') -- valid keys are depot, pallets, product"
    return evaluate(args.get("code", ""), ROWS)


trace2 = []
answer2, turns2, _ = run_tools(QUESTION.replace("pallets", "tonnage of pallets"),
                               [TOOL], flaky, max_tokens=2000, max_turns=10,
                               trace=trace2)

for t in trace2:
    print(f"call {t['turn']}:  {t['args'].get('code','')[:84]}")
    print(f"   ->    {t['result'][:84]}")
print(f"\nturns: {turns2}")
if turns2 >= 2:
    first, second = trace2[0]["args"].get("code", ""), trace2[1]["args"].get("code", "")
    print(f"the second call differs from the first: {first != second}")
    print("That is the recovery, and it is only possible because the error was")
    print("returned to the model rather than raised past it.")
else:
    print("Only one call: the model did not retry, so this run shows no recovery.")

# %% [markdown]
# ## §9.6 The seven-call trace, re-run
#
# The chapter publishes a seven-call trace whose four failures it attributes to
# its own tool design. Two of those failures no longer reproduce: `evaluate()`
# now puts `rows` and the builtins in globals, so a name inside a `lambda` and a
# nested comprehension both resolve. The trace was captured before that fix.
#
# This cell runs the same question against the shipped tool and prints whatever
# it produces, so the passage has an artefact that matches the code as shipped.
#
# The chapter's conclusion is unaffected and arguably strengthened: most of the
# cost of a slow agent is tool ergonomics rather than model capability, and two
# of the four failures here were fixed by changing four characters in the tool.

# %%
from peb import run_tools
from peb.checks import evaluate
from peb.depot_log import DEPOT_LOG

QUESTION_HARD = ("Using the depot log, which depot has the highest average "
                 "pallets per delivery, and what is that average to one decimal "
                 "place? Then say how many depots there are in total.")

TOOL_SPEC = {
    "name": "run_python",
    "description": ("Evaluate a single Python expression over the depot log and "
                    "return its value. The variable `rows` is a list of dicts, "
                    "each with keys: depot (str), pallets (int), product (str). "
                    "Only an expression, not statements."),
    "input_schema": {
        "type": "object",
        "properties": {"code": {"type": "string"}},
        "required": ["code"],
        "additionalProperties": False,
    },
}

calls = []


def traced(name, args):
    code = args.get("code", "")
    out = evaluate(code, DEPOT_LOG)
    calls.append((code, out))
    return out


answer, turns, usage = run_tools(QUESTION_HARD, [TOOL_SPEC], traced,
                                 max_tokens=3000, max_turns=10)

for i, (code, out) in enumerate(calls, 1):
    print(f"call {i}:  {code[:96]}")
    print(f"   ->    {out[:96]}")

print(f"\nfinal:  {answer.strip()[:200]}")
print(f"\n{len(calls)} tool call(s) over {turns} turn(s); "
      f"{usage.input_tokens} input tokens")

# %%
refusals = [c for c, o in calls if o.startswith("refused")]
errors = [c for c, o in calls if o.startswith("error")]
print(f"refused as statements : {len(refusals)}")
print(f"raised an error       : {len(errors)}")
print("\nPublished in §9.6: seven calls, four failures -- three statements")
print("rejected by the expression-only rule, one NameError on `sum` inside a")
print("lambda. The NameError cannot occur against the shipped tool: `sum` is in")
print("SAFE_BUILTINS, which is installed as __builtins__ inside globals, so it")
print("resolves inside a lambda. That failure belongs to an earlier version.")

if len(refusals) > 0:
    print("\nThe expression-only failures DO still reproduce, and they are the")
    print("chapter's real point: that constraint exists because the tool uses")
    print("eval, which is an implementation detail leaking into the interface.")
