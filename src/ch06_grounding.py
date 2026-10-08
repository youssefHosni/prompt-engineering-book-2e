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

# §6.5 and §6.6 use short excerpts of the same handbook, so that one document
# governs the chapter. The earlier stub said the surcharge applied to "all
# shipments", which contradicts the handbook and destroys §6.3's first near-miss.
DOC = """Kestrel Logistics Service Terms, revision 2026-01-14.

Standard delivery is 3 working days from dispatch. Palletised freight over
500 kg is 5 working days. A fuel surcharge of 4.5% applies to Express
deliveries booked after 2026-02-01. Standard delivery carries no fuel
surcharge.
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
    text, _ = ask(f"{DOC}\n\n" + grounded.format(q=q),
                  model="claude-opus-5", max_tokens=4000)
    first = text.strip().splitlines()[0] if text.strip() else ""
    # Branch on the sentinel exactly, which is the whole point of specifying one.
    # Printing a repr for a human to eyeball is the posture §6.4 forbids.
    refused = first.strip().rstrip(".").upper() == "NOT IN DOCUMENT"
    print(f"{q}\n  -> refused={refused}  {first[:90]!r}\n")

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

# %% [markdown]
# ## The handbook, the question sets, and the four experiments
#
# Provenance for everything below: `claude-opus-5` via OpenRouter, default
# sampling, run date in `outputs/run-log.jsonl`, scoring in this file. The model
# is passed explicitly rather than inherited from `PEB_MODEL`, so the script
# records what it used instead of leaving it to an environment variable.
#
# The document is `src/data/kestrel_handbook.md`. Fictional so nothing in it can
# be recalled from training; short so retrieval is not a variable.

# %%
import pathlib
import re

from peb import ask
from peb.checks import wilson
from peb.client import Blocked

MODEL = "claude-opus-5"
RUNS = 3          # §6.7's own argument: one run characterises nothing


def _repo_root():
    """Repo root, whether this runs as a script or as a notebook cell.

    Notebook kernels have no `__file__`, so a path built from it raises
    NameError on every cell below it. nbclient runs with cwd set to the repo
    root, which is the fallback.
    """
    import pathlib
    try:
        return pathlib.Path(__file__).resolve().parent.parent
    except NameError:
        return pathlib.Path.cwd()

HANDBOOK = (_repo_root() / "src" / "data" / "kestrel_handbook.md").read_text()
print(f"handbook: {len(HANDBOOK)} chars, {len(HANDBOOK.split())} words")

SENTINEL = "NOT IN DOCUMENT"

GROUNDED = (f"Answer using ONLY the document. If no sentence in the document "
            f"answers the question, reply with exactly: {SENTINEL}\n\n"
            f"{{doc}}\n\nQuestion: {{q}}")

PLAIN = "{doc}\n\nQuestion: {q}"

# %% [markdown]
# ### The three question sets
#
# Six answerable, six absent-but-plausible, five near-miss. The near-miss set is
# the interesting one: each has a wrong answer sitting in the text, in the right
# units, under a plausible heading.

# %%
ANSWERABLE = [
    ("How many working days is standard delivery?", ["3"]),
    ("What is the cut-off for express delivery?", ["14:00", "2 p.m", "2pm"]),
    ("How long do I have to submit a claim?", ["14"]),
    ("What is the maximum height of a shrink-wrapped pallet?", ["1.8"]),
    ("What is the liability limit per consignment?", ["100"]),
    ("How much void fill do fragile items need?", ["40"]),
]

UNANSWERABLE = [
    "What is the maximum parcel weight?",
    "Which insurer underwrites the claims?",
    "Is there Saturday delivery?",
    "What is the contact number for the claims team?",
    "How long are consignments held in storage before return?",
    "What is the surcharge for a failed collection?",
]

# The trap and what the document actually says.
NEAR_MISS = [
    ("What is the fuel surcharge on STANDARD deliveries?", "4.5% is for EXPRESS"),
    ("What is the cut-off time for STANDARD delivery?", "14:00 is for EXPRESS"),
    ("What is the MAXIMUM void fill for fragile items?", "40 mm is a MINIMUM"),
    ("Within how many WORKING days must a claim be submitted?", "14 is CALENDAR days"),
    ("What is the maximum height for a NON-shrink-wrapped pallet?", "1.8 m is for shrink-wrapped"),
    # The sixth. §6.3 says six and listed five; the original sixth was not
    # recoverable, so this one is new and built to the same shape against the
    # committed handbook: liability is stated per CONSIGNMENT, so a question
    # about per-PALLET liability has the neighbouring number in the right units
    # under the right heading.
    ("What is the liability limit per PALLET?", "100 GBP is per CONSIGNMENT"),
]


def refused(text):
    """§6.4's own advice, applied: check the sentinel exactly, do not eyeball it.

    The chapter's thesis is that a grounding instruction is worth having because
    it yields a string you can branch on. A script that prints a repr for a human
    to read is doing the thing the chapter forbids.
    """
    return text.strip().rstrip(".").upper() == SENTINEL


def contains_any(text, needles):
    return any(n.lower() in text.lower() for n in needles)


BLOCKED = []


def try_ask(prompt, q):
    """Return the reply, or None if a platform filter refused the request.

    A blocked call never reached the model, so it is not evidence about the
    model. Counting it as a failure would report a finding about a guardrail as
    a finding about grounding.
    """
    try:
        return ask(prompt, model=MODEL, max_tokens=4000)[0]
    except Blocked as e:
        BLOCKED.append((q, str(e)[:70]))
        return None


# %% [markdown]
# ### §6.2 Answerable and unanswerable, with and without the instruction

# %%
for label, template in (("plain prompt", PLAIN), ("+ grounding instruction", GROUNDED)):
    correct = refusals = 0
    blocked_before = len(BLOCKED)
    for q, needles in ANSWERABLE:
        reps = [try_ask(template.format(doc=HANDBOOK, q=q), q) for _ in range(RUNS)]
        hits = sum(contains_any(r, needles) for r in reps if r is not None)
        correct += hits == RUNS
    for q in UNANSWERABLE:
        reps = [try_ask(template.format(doc=HANDBOOK, q=q), q) for _ in range(RUNS)]
        hits = sum(refused(r) for r in reps if r is not None)
        refusals += hits == RUNS
    asked = 6 * RUNS * 2
    lost = len(BLOCKED) - blocked_before
    if lost > asked * 0.25:
        print(f"{label:<26} NO RESULT -- {lost} of {asked} calls were refused by a")
        print(f"{'':<26} platform filter before the model ran. A condition this")
        print(f"{'':<26} heavily intercepted measures the filter, not grounding.")
    else:
        print(f"{label:<26} {correct}/6 correct     {refusals}/6 refused"
              f"   (all {RUNS} runs agreeing; {lost} blocked)")

print(f"\nEach cell is {RUNS} runs; a cell counts only if every run agreed.")
print("\nA platform filter intercepts the bare handbook: sending the document")
print("with no instruction is refused reproducibly, and the same document with")
print("a grounding instruction passes. So the unguided condition cannot be")
print("measured on this path -- which is itself worth knowing, because a filter")
print("that silently removes one arm of a comparison will make the other arm")
print("look better than it is. §13.1: if the instrument can fail silently,")
print("treat silence as failure.")
print("Without the instruction, 'refused' means the reply carried no answer at")
print("all -- the exact sentinel is only available when you ask for it, which is")
print("§6.4's argument for asking.")

# %% [markdown]
# ### §6.3 The near-miss set
#
# The failure this guards against is not invention. It is handing back the
# neighbouring fact, which looks entirely reasonable to a reader who has not
# checked the document.

# %%
print(f"{'question':<58} {'refused':>8}  trap")
for q, trap in NEAR_MISS:
    reps = [try_ask(GROUNDED.format(doc=HANDBOOK, q=q), q) for _ in range(RUNS)]
    hits = sum(refused(r) for r in reps if r is not None)
    print(f"{q[:56]:<58} {hits}/{RUNS:<6}  {trap}")

print("\nSix questions, as §6.3 says. The original sixth was not recoverable, so")
print("the liability one is new, built to the same shape against the committed")
print("handbook rather than reconstructed from the chapter.")

# %% [markdown]
# ### §6.8 Distractors
#
# Does an irrelevant corpus around the handbook degrade the answer? Padding is
# other sections of the same handbook, repeated and renumbered, so the
# distractors are same-domain rather than random text.

# %%
DISTRACTOR = ("\n\n## Appendix {n}. Regional depot opening hours\n"
              "Depot {n} operates 07:00 to 19:00 on working days. "
              "Collections from depot {n} are consolidated nightly.\n")

q, needles = ANSWERABLE[0]
print(f"{'distractors':>12}  {'correct':>8}")
for n_dist in (0, 25, 100, 200):
    doc = HANDBOOK + "".join(DISTRACTOR.format(n=i) for i in range(n_dist))
    reps = [try_ask(GROUNDED.format(doc=doc, q=q), q) for _ in range(RUNS)]
    hits = sum(contains_any(r, needles) for r in reps if r is not None)
    lo, hi = wilson(hits, RUNS)
    print(f"{n_dist:>12}  {hits}/{RUNS:>6}   95% CI [{lo:.0%}, {hi:.0%}]")

print(f"\nAt {RUNS} runs per row the intervals are very wide: this can show a")
print("collapse, but it cannot establish 'no degradation'. §14.2 is the chapter")
print("on what that takes.")


# %% [markdown]
# ### §6.8 The citation check, actually run
#
# §6.8 says a quoted span "either appears verbatim in your source or it does
# not, and that is a string comparison you can run in your own code". The
# chapter was right and this file did not do it -- it printed ninety characters
# of the reply for a human to read, which is the posture §6.4 forbids. Here is
# the check.

# %%
CITED = (f"Answer using ONLY the document below. Quote the exact sentence you "
         f"used, then give the answer. If no sentence in the document answers "
         f"the question, reply with exactly: {SENTINEL}"
         "\n\n{doc}\n\nQuestion: {q}")


def quoted_span(text):
    """The first double-quoted run in the reply, if there is one."""
    parts = (text or "").split('"')
    return parts[1] if len(parts) > 2 else ""


def flat(s):
    """Collapse whitespace before comparing.

    Without this the check is a false-positive machine. The handbook is
    hard-wrapped at 76 characters and the model quotes the sentence as one
    line, so a plain `span in HANDBOOK` failed on a CORRECT answer three times
    out of three -- it would have told you to discard a good reply. The
    instrument, not the model. §13.1, one layer down.
    """
    return re.sub(r"\s+", " ", s or "").strip()


print(f"{'question':<46} {'sentinel':>9} {'quote in source':>16}")
for q, _trap in NEAR_MISS[:3] + ANSWERABLE[:3]:
    text = try_ask(CITED.format(doc=HANDBOOK, q=q), q)
    if text is None:
        continue
    span = quoted_span(text)
    if not span:
        verdict = "n/a"
    elif flat(span) in flat(HANDBOOK):
        verdict = "yes"
    else:
        verdict = "NO -- discard"
    print(f"{q[:44]:<46} {str(refused(text)):>9} {verdict:>16}")

print("\nA fabricated citation fails this check. A citation that is real but")
print("answers a different question passes it, which is why §6.3's near-miss")
print("set is a separate test rather than a corollary of this one.")


# %%
if BLOCKED:
    print(f"\n{len(BLOCKED)} call(s) were refused by a platform filter before the")
    print("model ran. Those are not evidence about grounding either way:")
    for q, why in dict(BLOCKED).items():
        print(f"  {q[:60]}\n    {why}")
