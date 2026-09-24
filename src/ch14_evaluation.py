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
# # Chapter 14 — Evaluating LLM Applications
#
# Sixteen examples, three scorers, and a Wilson interval so that 15/16 is
# reported as what it actually is rather than as "94%".
#
# The first ten are the ordinary set, and a current model scores 10/10 on them.
# **That is a fact about the set, not a result about the model** — an eval where
# everything passes cannot show you where the prompt is broken, which is the
# only thing §14.1 claims ten examples are good for. The six after them are the
# awkward cases.

# %%
from peb import ask
from peb.checks import exact, fuzzy, wilson

CASES = [
    ("Ordered on the 3rd, arrived the 11th. Ref KL-449021.",            "KL-449021"),
    ("order ref kl-449022, still waiting",                              "KL-449022"),
    ("Ref: KL-449023 (second attempt)",                                 "KL-449023"),
    ("My order KL-449024 arrived damaged",                              "KL-449024"),
    ("Reference KL449025 — no dash, sorry",                             "KL-449025"),
    ("KL-449026 and KL-449027 both late",                               "KL-449026"),
    ("I don't have the reference to hand",                              "NONE"),
    ("Invoice INV-99812, not an order ref",                             "NONE"),
    ("kl-449028\nsent from my phone",                                   "KL-449028"),
    ("Order number 449029",                                             "NONE"),

    # The awkward six. Each targets one clause of the rule.
    ("Ref KL-44902 (five digits, typo on my part)",                     "NONE"),
    ("contact me at kl-449030@example.com about the delay",             "NONE"),
    ("> You wrote: your order KL-449031 has shipped\nThat is not mine.", "KL-449031"),
    ("Order KL-449032 for my colleague, mine is KL-449033",             "KL-449032"),
    ("the ref is K L - 4 4 9 0 3 4, spaced out on the label",           "KL-449034"),
    ("no ref, but the invoice says KL-449035-R2 for the replacement",   "KL-449035"),
]

PROMPT = ("Extract the order reference from the message. The format is KL- "
          "followed by six digits. Normalise to upper case with the dash. "
          "If there is no order reference, reply exactly NONE.\n"
          "Reply with the reference or NONE, nothing else.\n\n"
          "Message: ```{msg}```")

# %% [markdown]
# ## §14.1 Ten examples, scored three ways

# %%
results = []
for msg, want in CASES:
    got, _ = ask(PROMPT.format(msg=msg), max_tokens=4000)
    got = got.strip().splitlines()[0] if got.strip() else ""
    results.append((msg, want, got))
    mark = "ok  " if exact(got, want) else "MISS"
    print(f"[{mark}] want={want:<10} got={got[:16]:<16} {msg[:34]!r}")

n = len(results)
for label, fn in (("exact", exact), ("fuzzy", fuzzy)):
    k = sum(fn(g, w) for _, w, g in results)
    lo, hi = wilson(k, n)
    print(f"\n{label:<6} {k}/{n} = {k / n:.0%}   95% CI [{lo:.0%}, {hi:.0%}]")

# %% [markdown]
# ## §14.4 The judge, scored against the labels
#
# A judge you have not scored is an opinion. Sixteen labels are enough to find
# out whether it is a useful one.

# %%
JUDGE = ("Is the extracted reference correct for this message?\n"
         "Message: ```{msg}```\nExtracted: {got}\nExpected: {want}\n"
         "Answer YES or NO only.")

agree = 0
for msg, want, got in results:
    v, _ = ask(JUDGE.format(msg=msg, got=got or "(empty)", want=want), max_tokens=4000)
    agree += (v.strip().upper().startswith("YES") == exact(got, want))

lo, hi = wilson(agree, n)
print(f"judge agreed with the label on {agree}/{n}   95% CI [{lo:.0%}, {hi:.0%}]")

# %% [markdown]
# ## §14.2 What the interval is for
#
# With sixteen examples the interval is still wide. Two results that look
# different are often not distinguishable — which is exactly the situation this
# book's own §13.1 numbers are in.

# %%
for k, lbl in ((9, "book's ch13 run"), (5, "a later re-run")):
    lo, hi = wilson(k, 14)
    print(f"{lbl:<18} {k}/14 = {k / 14:.0%}   95% CI [{lo:.0%}, {hi:.0%}]")

print("\nThose two intervals overlap. At n=14 the runs are not distinguishable,")
print("and reporting either as a fact would be overstating what was measured.")
