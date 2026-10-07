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


results = {}
for label, prompt in CONDITIONS.items():
    ok = blocked = 0
    for _ in range(RUNS):
        try:
            ok += within_limit(ask(prompt, max_tokens=4000)[0])
        except Blocked:
            blocked += 1
    answered = RUNS - blocked
    results[label] = {"ok": ok, "answered": answered, "blocked": blocked}
    note = f"   ({blocked}/{RUNS} blocked upstream)" if blocked else ""
    print(f"{label:<10} {ok}/{answered or '-'} inside the limit{note}")

# %% [markdown]
# ### The conclusion, computed rather than asserted
#
# The sentence this experiment exists to support is "emphasis is not an
# instruction". Printing it regardless of what came back would make it an
# assertion dressed as a result — and on at least one run `shouting` beat
# `plain` 9 to 4, which that sentence does not survive.
#
# So compute it. With n=10 per condition the intervals are wide enough that
# most differences are not separable, and saying so is the finding.

# %%
from peb.checks import wilson

plain = results["plain"]
if plain["answered"]:
    p_lo, p_hi = wilson(plain["ok"], plain["answered"])
    print(f"\nplain      {plain['ok']}/{plain['answered']}  95% CI [{p_lo:.0%}, {p_hi:.0%}]")
    separable = []
    for label, v in results.items():
        if label == "plain" or not v["answered"]:
            continue
        lo, hi = wilson(v["ok"], v["answered"])
        apart = lo > p_hi or hi < p_lo
        separable.append((label, apart))
        print(f"{label:<10} {v['ok']}/{v['answered']}  95% CI [{lo:.0%}, {hi:.0%}]"
              f"   separable from plain: {apart}")

    if not any(apart for _, apart in separable):
        print("\nNo condition separates from plain at n=10. Emphasis is not an")
        print("instruction; structure is — and this run cannot tell the emphasis")
        print("conditions apart from each other either.")
    else:
        moved = [l for l, apart in separable if apart]
        print(f"\nThese separate from plain at n=10: {', '.join(moved)}.")
        print("That is more than emphasis alone should buy. Before concluding")
        print("anything, check what else changed in those conditions — and raise n:")
        print("§14.2 is the chapter on how little ten runs settle.")

for label, v in results.items():
    if v["blocked"]:
        print(f"\n{label}: {v['blocked']}/{RUNS} refused by a platform filter before")
        print("the model ran. That is not evidence about the model either way.")
