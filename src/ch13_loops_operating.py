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
# # Chapter 13 — Operating a Loop
#
# This chapter opens with the author's own verification step failing, and the
# scoring code reading the failure as a pass. Both versions are here.
#
# | § | what it shows |
# |---|---|
# | 13.2 | the free-text checker that returns nothing |
# | 13.3 | the same checker with a schema and a real budget |
# | 13.4 | who catches violations: the model, a checklist, or three lines of code |
#
# **Pinned to Sonnet.** The chapter's numbers were measured on it. Running this
# on a different model and reporting a different number would be a finding about
# the model, printed as a finding about the chapter.

# %%
import json
import os
import re

from peb import ask
from peb.checks import violations

RUNS = 14
MODEL = os.getenv("PEB_MODEL", "claude-sonnet-5")

# %% [markdown]
# Twenty distinct messages rather than one prompt repeated. Those measure
# different things: one prompt run fourteen times measures sampling variance,
# fourteen different messages measure the instruction — which is what the
# chapter claims to be about.
#
# The band is 55 to 60. Ask for 50 with a loose check and every reply passes,
# the §13.4 comparison becomes 0/0, and nothing is measured. That mistake was in
# this file until a live run exposed it.

# %%
MESSAGES = [f"Order KL-{100000 + i * 13} arrived damaged. What should I do?"
            for i in range(RUNS)]

RULES = "between 55 and 60 words, signed as 'Kestrel Support'"

DRAFT = ("Write a reply to the customer about a damaged delivery.\n"
         "Length: exactly between 55 and 60 words.\n"
         "Sign as 'Kestrel Support'.\n\nMessage: ```{m}```")

replies = [ask(DRAFT.format(m=m), model=MODEL, max_tokens=4000)[0] for m in MESSAGES]
truth = [violations(r) for r in replies]
bad = sum(bool(v) for v in truth)

print(f"{RUNS} replies; {bad} violate at least one rule (verified in code)")
print(f"word counts: {[len(r.split()) for r in replies]}")

# %% [markdown]
# ## §13.2 The free-text checker
#
# A 16-token budget, which is what caused the original failure. The guard clause
# in `ask()` raises; **without it each of these is an empty string**, and
# `if not problems` reads an empty string as a pass.
#
# That is the bug this chapter exists for, and it was reintroduced into this
# repository once, hours after this script was written.

# %%
starved = 0
for r in replies[:3]:
    try:
        text, _ = ask(f"Check this reply against the rules.\n\nRules: {RULES}\n\n"
                      f"Reply:\n{r}", model=MODEL, max_tokens=16)
        print(f"returned {text.strip()[:60]!r}")
    except RuntimeError as e:
        starved += 1
        print(f"RuntimeError: {e}")

print(f"\n{starved}/3 raised instead of returning quietly.")

# %% [markdown]
# ## §13.3 The same checker, with a schema and a real budget

# %%
CHECK = {"type": "object",
         "properties": {"word_count": {"type": "integer"},
                        "signed":     {"type": "boolean"}},
         "required": ["word_count", "signed"],
         "additionalProperties": False}

parsed = caught = 0
for r in replies:
    text, _ = ask(f"Return JSON matching this schema for the reply below.\n"
                  f"{json.dumps(CHECK)}\n\nReply:\n{r}", model=MODEL, max_tokens=4000)
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        continue
    try:
        obj = json.loads(m.group(0))
    except Exception:
        continue
    parsed += 1
    if abs(obj.get("word_count", -1) - len(r.split())) <= 1:
        caught += 1

print(f"parsed {parsed}/{RUNS}   word count within 1: {caught}/{max(parsed, 1)}")

# %% [markdown]
# ## §13.4 Who catches the violations?

# %%
same_model = 0
for r, t in zip(replies, truth):
    text, _ = ask(f"Rules: {RULES}\n\nReply:\n{r}\n\n"
                  f"Is it compliant? Answer YES or NO only.",
                  model=MODEL, max_tokens=4000)
    same_model += (text.strip().upper().startswith("NO") == bool(t))

print(f"same model, 'is it compliant?'   agreed with code on {same_model}/{RUNS}")

# The code row is not a competitor. `violations()` DEFINES the truth every other
# checker is scored against, so any "n/n" printed for it is a tautology, not a
# measurement — it cannot lose a comparison it is the answer key for.
#
# What is worth printing is the thing the model checker gets wrong, which is a
# real number and the one the chapter's argument rests on.
disagreed = RUNS - same_model
print(f"three lines of code              the reference; not scored against itself")
print(f"\nthe model checker disagreed with the code on {disagreed}/{RUNS} replies.")
print("Each disagreement is either a miss or a false alarm, and the code is the")
print("answer key only because these rules are expressible in code. §13.5 is")
print("about the ones that are not.")
print("\nUse the model to judge what code cannot express. Use code for")
print("everything it can — which is more than you think.")
