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
import re

from peb import ask

RUNS = 12

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

for label, suffix in (
        ("room to think", " Show your working, then give the answer as "
                          "'CARTONS: <n>  LEFTOVER: <n>'."),
        ("answer only",   " Reply with only 'CARTONS: <n>  LEFTOVER: <n>' and "
                          "no working.")):
    right = 0
    for _ in range(RUNS):
        text, _ = ask(WORD_PROBLEM + suffix, max_tokens=4000)
        m = re.search(r"CARTONS:\s*(\d+)\s+LEFTOVER:\s*(\d+)", text.upper())
        right += bool(m) and (int(m.group(1)), int(m.group(2))) == (ANSWER_CARTONS,
                                                                    ANSWER_LEFT)
    print(f"{label:<15} {right}/{RUNS} correct")
