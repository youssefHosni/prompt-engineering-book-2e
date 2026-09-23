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
# # Chapter 5 — Patterns and Anti-Patterns
#
# The anti-pattern measured here is the one everyone has tried: making the
# instruction louder.
#
# Note that each condition changes exactly **one** thing. An earlier draft
# changed two — capitals *and* an added "important" — which measures nothing,
# and is the same confound §14.6 warns about.

# %%
from peb import ask
from peb.client import Blocked

RUNS = 10

BASE = ("Summarise the paragraph below in one sentence of at most 15 words.\n\n"
        "The depot moved 412 pallets in March, up from 388 in February, "
        "though two of the four loading bays were closed for resurfacing.")

CONDITIONS = {
    "plain":    BASE,
    "shouting": BASE.replace("at most 15 words", "AT MOST 15 WORDS"),
    "urgent":   BASE.replace("Summarise", "IMPORTANT! Summarise"),
    # This condition is currently refused by a platform filter citing "reverse
    # engineering or duplicating model outputs" -- the WORKING:/ANSWER: framing
    # reads as an attempt to extract raw reasoning. It is kept, and the block is
    # reported as its own outcome, because a reader who writes this prompt will
    # hit the same wall. Note that §4.4's "Show your working, then give the
    # answer" is NOT affected; it runs normally.
    "format":   BASE + "\n\nBegin your reply with the line 'WORKING:' and show "
                       "your steps, then a line 'ANSWER:' with just the number.",
}

# %%
def within_limit(text):
    body = text.split("ANSWER:")[-1] if "ANSWER:" in text else text
    return len(body.split()) <= 15


for label, prompt in CONDITIONS.items():
    ok = blocked = 0
    for _ in range(RUNS):
        try:
            ok += within_limit(ask(prompt, max_tokens=4000)[0])
        except Blocked:
            blocked += 1
    answered = RUNS - blocked
    note = f"   ({blocked}/{RUNS} blocked upstream)" if blocked else ""
    print(f"{label:<10} {ok}/{answered or '-'} inside the limit{note}")

print("\nEmphasis is not an instruction. Structure is.")
