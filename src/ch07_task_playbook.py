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
# # Chapter 7 — The Task Playbook
#
# One input, six tasks. The chapter's argument is that these are not six
# techniques; they are one technique with the risk moved around.
#
# On the left of that axis the failure is **omission** — something is dropped
# silently and the output still looks complete. On the right it is
# **invention**. The middle two should preserve meaning exactly, which makes
# them easiest to check and easiest to get quietly wrong.

# %%
from peb import ask
from peb.fixtures import REVIEW

print(REVIEW)


# %%
def run(label, template, **checks):
    text, _ = ask(template.format(review=REVIEW), max_tokens=4000)
    print(f"--- {label}")
    print(text.strip()[:520])
    for name, fn in checks.items():
        print(f"  [check] {name}: {fn(text)}")
    print()


# %% [markdown]
# ## §7.1 Summarising: the purpose is the prompt
#
# There is no such thing as *the* summary of a text — only the summary for
# somebody, for something. Two readers, same review.

# %%
pm = """Summarise this review in 2 sentences for a product manager deciding
what to fix next. Report only faults and their severity. Ignore praise and
logistics.

Review: ```{review}```"""

ops = """Summarise this review in 2 sentences for a logistics lead.
Report only delivery and support performance. Ignore the product itself.

Review: ```{review}```"""

run("summarise (product manager)", pm)
run("summarise (logistics lead)", ops)

# %% [markdown]
# Those two summaries share no content. Neither is wrong; they answer different
# questions, and two clauses made the difference.
#
# ## §7.2 Extraction — the keys are fixed, so the check is trivial

# %%
extract = """Extract from the review. Use exactly these keys, one per line,
in this order. Use the literal string NONE if a value is absent.

order_ref | ordered_date | arrived_date | support_hours

Review: ```{review}```"""

run("extract", extract,
    all_keys=lambda t: all(k in t for k in
                           ("order_ref", "ordered_date", "arrived_date", "support_hours")))

# %% [markdown]
# ## §7.3 Classification

# %%
classify = """Classify this review. Reply with exactly these three lines
and nothing else:

sentiment: positive | negative | mixed
recommends: yes | no
faults: a comma-separated list, or NONE

Review: ```{review}```"""

run("classify", classify,
    three_lines=lambda t: len([l for l in t.strip().splitlines() if l.strip()]) == 3)

# %% [markdown]
# ## §7.4 Transformation — the risk is silent loss
#
# `must_keep` is the whole technique. Decide what must survive, then check it in
# code rather than reading the output and feeling reassured.

# %%
must_keep = ["KL-449021", "drip tray", "manual", "support"]

transform = """Rewrite the review as an internal support ticket. Neutral register,
no first person, keep every order reference and part name exactly as written.

Review: ```{review}```"""

run("transform", transform,
    kept=lambda t: [k for k in must_keep if k.lower() not in t.lower()] or "all kept")

# %% [markdown]
# ## §7.5 Translation — the same check, across a script boundary

# %%
translate = """Translate the review into Modern Standard Arabic. Keep product
names, order references and part numbers in Latin script, unchanged.

Review: ```{review}```"""

run("translate", translate,
    latin_kept=lambda t: "KL-449021" in t and "Nordic 400" in t)

# %% [markdown]
# ## §7.6 Expansion — the highest-risk task, so the most constraints
#
# This is the far right of the axis. Every constraint here exists because its
# absence produced something wrong once.

# %%
expand = """Write a reply to this customer.
Length: 60 to 80 words.
Acknowledge the late delivery and the drip tray.
Offer a replacement tray. Do not offer a refund.
Do not promise a delivery date.
Sign as 'Kestrel Support'.

Review: ```{review}```"""

run("expand", expand,
    length=lambda t: len(t.split()),
    no_refund=lambda t: "refund" not in t.lower(),
    signed=lambda t: "Kestrel Support" in t)
