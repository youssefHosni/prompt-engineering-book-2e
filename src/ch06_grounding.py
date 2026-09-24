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
# # Chapter 6 — Grounding, Hallucination, and Retrieval
#
# | § | what it shows |
# |---|---|
# | 6.4 | giving the model a way to say "not in the document" |
# | 6.5 | two passages that disagree, and a rule for which wins |

# %%
from peb import ask
from peb.checks import norm_dashes

DOC = """Kestrel Logistics Service Terms, revision 2026-01-14.

Standard delivery is 3 working days from dispatch. Palletised freight over
500 kg is 5 working days. A fuel surcharge of 4.5% applies to all shipments
booked after 2026-02-01.
"""

OLD = """Kestrel Logistics Service Terms, revision 2025-06-02.
The fuel surcharge is 2.0% and applies to palletised freight only.
"""

ANSWERABLE = "What is the fuel surcharge?"
UNANSWERABLE = "What is the penalty for a missed collection?"

# %% [markdown]
# ## §6.4 An escape hatch the model can actually take
#
# Without a named way to decline, a question the document does not answer still
# gets an answer. The exact sentinel matters: `NOT IN DOCUMENT` is detectable
# in code, "I'm not sure" is not.

# %%
grounded = """Answer using ONLY the document. Quote the exact sentence you used,
then give the answer. If no sentence in the document answers the question,
reply with exactly: NOT IN DOCUMENT

Question: {q}"""

for q in (ANSWERABLE, UNANSWERABLE):
    text, _ = ask(f"{DOC}\n\n" + grounded.format(q=q), max_tokens=4000)
    first = text.strip().splitlines()[0] if text.strip() else ""
    print(f"{q}\n  -> {first[:90]!r}\n")

# %% [markdown]
# ## §6.5 Two revisions that disagree
#
# Retrieval returns both. Which one wins has to be stated, or the model picks.

# %%
CONFLICT_RULE = (
    "If two passages conflict, prefer the one with the later revision date and say "
    "which you used. If they have no dates, reply exactly: CONFLICT.")

text, _ = ask(f"{OLD}\n---\n{DOC}\n\n{CONFLICT_RULE}\n\nQuestion: {ANSWERABLE}",
              max_tokens=4000)
print(text.strip()[:400])
print(f"\ncited the later revision: {'2026-01-14' in norm_dashes(text)}")
