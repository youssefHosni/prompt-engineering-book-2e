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
# # Chapter 4 — Giving the Model Room to Think
#
# The headline finding in this chapter's first draft was an artifact of the
# author's own prompt. "Reply with only the number" suppressed the working and
# produced a 2/12 baseline that had nothing to do with reasoning.
#
# Both conditions are run here, because the difference between them *is* the
# chapter.

# %%
import os
import re

from peb import ask

RUNS = 12

# The chapter measures TWO models, and the contrast is the whole point:
#
#   claude-haiku-4.5   12/12 normally, 2/12 with "Reply with only the number"
#   claude-sonnet-5    12/12 either way -- its thinking does not live in the text
#
# Running only a reasoning model gives 12/12 in both arms and looks like a null
# result. That is not a refutation of the chapter, it is the chapter's second
# row. Both are run here.
MODELS = os.getenv("PEB_MODEL", "claude-haiku-4.5,claude-sonnet-5").split(",")

# %% [markdown]
# ## §4.2 Four numbered steps in one pass

# %%
EMAIL = """Hi - the Nordic 400 I ordered last month has started making a loud
grinding noise whenever I pull a shot, and the crema has gone. It was fine for
three weeks. Is this something I can fix or do I need to send it back?"""

steps = """For the customer email below, do the following in order:

1. Identify the product the customer is writing about.
2. Decide whether the message is a complaint, a question, or praise.
3. If it is a complaint, name the specific fault.
4. Draft a two-sentence reply.

Return each step on its own line, labelled.

Email: ```{email}```"""

text, _ = ask(steps.format(email=EMAIL), max_tokens=4000)
print(text.strip()[:700])
print(f"\nsteps present: {sum(text.count(f'{i}.') > 0 for i in range(1, 5))}/4")

# %% [markdown]
# ## §4.4 The instruction that suppresses the working
#
# One variable changes between these two conditions: whether the model is
# allowed to show its steps. Measure the prompt you wrote, not the one you
# meant to write.

# %%
# The original problem here was 3x12 + 2x18 - 7. Both conditions scored 12/12
# on it: a current model does that arithmetic without needing to write anything
# down, so the prompt difference had nothing to bite on. An experiment where
# both arms score full marks measures nothing -- §14.1, again.
#
# This one has multiple dependent steps and a unit change, which is where
# suppressing the working actually costs something.
WORD_PROBLEM = (
    "A depot receives 7 pallets. Each pallet holds 24 cases; each case holds 18 "
    "tins. During unloading 3 cases are crushed, and a further 2 pallets are "
    "found to be half-empty (12 cases each instead of 24). Tins are then packed "
    "into cartons of 45 for dispatch. How many full cartons can be dispatched, "
    "and how many tins are left over?")
# 5 full pallets x 24 = 120 cases, plus 2 x 12 = 24 cases -> 144, minus 3 = 141
# 141 x 18 = 2538 tins -> 2538 / 45 = 56 cartons remainder 18
ANSWER_CARTONS, ANSWER_LEFT = 56, 18

for model in MODELS:
    print(f"\n{model}")
    for label, suffix in (
            ("room to think", " Show your working, then give the answer as "
                              "'CARTONS: <n>  LEFTOVER: <n>'."),
            ("answer only",   " Reply with only 'CARTONS: <n>  LEFTOVER: <n>' and "
                              "no working.")):
        right = tokens = 0
        for _ in range(RUNS):
            text, usage = ask(WORD_PROBLEM + suffix, model=model, max_tokens=4000)
            tokens += usage.output_tokens
            m = re.search(r"CARTONS:\s*(\d+)\s+LEFTOVER:\s*(\d+)", text.upper())
            right += bool(m) and (int(m.group(1)), int(m.group(2))) == (ANSWER_CARTONS,
                                                                        ANSWER_LEFT)
        print(f"  {label:<15} {right}/{RUNS} correct   "
              f"{tokens / RUNS:.0f} output tokens/problem")


# %% [markdown]
# ## The twelve problems, as a dataset
#
# §4.1 says "twelve multi-step word problems". The cells above run ONE problem
# twelve times, which measures sampling variance rather than the instruction --
# a different experiment with the same denominator. `peb.fixtures.ARITHMETIC_12`
# is the twelve-problem version, generated from a fixed seed with every answer
# computed and re-derived in `test_offline.py`.
#
# It is a RECONSTRUCTION of the shape §4.1 describes, not the original set,
# which was not committed. So run it to reproduce the *method*; do not read a
# disagreement with the published 12/12-and-2/12 as a correction to the book,
# because a different problem set is a different measurement.

# %%
from peb.fixtures import ARITHMETIC_12

ARMS = {
    "bare question": "",
    '+ "Reply with only the number."': " Reply with only the number.",
}


def pence(reply):
    """Last money-looking figure in the reply, in whole pence."""
    m = re.findall(r"£\s*(\d+(?:\.\d{1,2})?)", reply or "")
    if m:
        return round(float(m[-1]) * 100)
    m = re.findall(r"(\d+(?:\.\d{1,2})?)", (reply or "").replace(",", ""))
    return round(float(m[-1]) * 100) if m else None


for model in MODELS:
    print(f"\n{model}  (twelve problems, one run each)")
    for label, suffix in ARMS.items():
        hits = 0
        for q, answer in ARITHMETIC_12:
            text, _ = ask(q + suffix, model=model, max_tokens=4000)
            hits += pence(text) == answer
        print(f"  {label:<34}{hits:>3}/12")

print("\nTwelve problems, not twelve runs of one. Both are legitimate and they")
print("measure different things, which is why §4.1 now says which it means.")
