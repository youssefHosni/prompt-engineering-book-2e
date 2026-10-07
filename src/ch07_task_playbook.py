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

# %% [markdown]
# ## §7.2 The three-attempt extraction story
#
# The section the chapter calls "the honest case for Chapter 8". Three prompts,
# six runs each, scored by a criterion stated in code rather than in prose.
#
# **What `machine-usable` means**, which the chapter asserts and never defines:
# all five keys present, and the three numeric fields parseable with `int()`
# without cleaning. That is the whole criterion — `ordered_date: 3` passes,
# `ordered_date: 3rd` does not, and that single difference is what the three
# attempts are about.
#
# All three prompts are printed in full here. The chapter shows one and
# paraphrases two, which leaves its conclusion resting on a prompt the reader
# cannot see.

# %%
import re

from peb import ask
from peb.fixtures import REVIEW

RUNS = 6
KEYS = ["order_ref", "ordered_date", "arrived_date", "support_hours", "faults"]
NUMERIC = ["ordered_date", "arrived_date", "support_hours"]

ATTEMPT_1 = """Extract from the review. Use exactly these keys, one per line,
in this order. Use the literal string NONE if a value is absent.

order_ref | ordered_date | arrived_date | support_hours | faults

Review: ```{review}```"""

ATTEMPT_2 = ATTEMPT_1.replace(
    "Review: ```{review}```",
    # Verbatim from §7.2. An earlier version of this file added ", no ordinals",
    # which is the one hint that fixes `3rd` -- and it took attempt two from 0/6
    # to 6/6, i.e. it silently turned the chapter's three-step story into a
    # two-step one. The prompt under test has to be the prompt the chapter shows.
    "Emit bare values only — no units, no words.\n\n"
    "Review: ```{review}```")

ATTEMPT_3 = """Extract from the review. Emit exactly these five keys, one per
line, in this order, each as `key: value`. Every key must appear even if its
value is NONE.

order_ref       a string, or NONE
ordered_date    an integer day of the month, digits only
arrived_date    an integer day of the month, digits only
support_hours   an integer number of hours, digits only
faults          a comma-separated list, or NONE

Emit bare values only — no units, no words, no ordinals. A value like `3rd` or
`4 hours` is wrong; `3` and `4` are right.

Review: ```{review}```"""


def parse(text):
    """Pull `key: value` pairs out of the reply."""
    out = {}
    for line in text.strip().splitlines():
        m = re.match(r"\s*([a-z_]+)\s*[:|]\s*(.+?)\s*$", line)
        if m and m.group(1) in KEYS:
            out[m.group(1)] = m.group(2).strip()
    return out


def machine_usable(text):
    """All five keys present, and the three numeric fields int()-parseable.

    No cleaning, no regex rescue, no stripping of units. If it needs a repair
    step it is not machine-usable -- that is the point the section is making.
    """
    got = parse(text)
    if set(KEYS) - set(got):
        return False
    for k in NUMERIC:
        try:
            int(got[k])
        except (ValueError, TypeError):
            return False
    return True


# %%
print(f"{'attempt':<12} {'machine-usable':>15}   first reply's numeric fields")
for label, prompt in (("one", ATTEMPT_1), ("two", ATTEMPT_2), ("three", ATTEMPT_3)):
    usable = 0
    sample = ""
    for i in range(RUNS):
        text, _ = ask(prompt.format(review=REVIEW), max_tokens=4000)
        usable += machine_usable(text)
        if i == 0:
            got = parse(text)
            sample = "  ".join(f"{k}={got.get(k, '(missing)')!r}" for k in NUMERIC)
    print(f"{label:<12} {usable:>7}/{RUNS:<7}   {sample[:74]}")

print("\nPublished in §7.2: 0 of 6, 0 of 6, 6 of 6.")

# %% [markdown]
# ### A note on the field set
#
# The chapter's prompt at §7.2 specifies five keys including `faults`, and its
# first result block shows four — `faults` disappears without comment. All three
# attempts here keep the five-key set, because dropping the one free-text field
# is most of what makes the later attempts tractable, and silently removing it
# would be the kind of unstated change the chapter warns about elsewhere.
