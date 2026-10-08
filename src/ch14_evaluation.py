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
bounds = {}
for k, lbl in ((9, "book's ch13 run"), (5, "a later re-run")):
    lo, hi = wilson(k, 14)
    bounds[lbl] = (lo, hi)
    print(f"{lbl:<18} {k}/14 = {k / 14:.0%}   95% CI [{lo:.0%}, {hi:.0%}]")

(a_lo, a_hi), (b_lo, b_hi) = bounds["book's ch13 run"], bounds["a later re-run"]
overlap = a_lo <= b_hi and b_lo <= a_hi
if overlap:
    print(f"\nThose two intervals overlap between {max(a_lo, b_lo):.0%} and "
          f"{min(a_hi, b_hi):.0%}. At n=14 the runs are not distinguishable,")
    print("and reporting either as a fact would be overstating what was measured.")
else:
    print("\nThose intervals do NOT overlap, so the two runs differ by more than")
    print("sampling at n=14. Something changed between them — model, prompt or")
    print("scoring — and it needs finding before either number is published.")

# %% [markdown]
# ## The three judge experiments
#
# §14.4 publishes three results about LLM-as-judge and the repository holds none
# of them. All three run here.
#
# Provenance: `claude-opus-5` unless a cell names another model, default
# sampling, run date in `outputs/run-log.jsonl`, scoring in this file.
#
# The design point shared by all three: a judge is only worth having if you have
# scored it, and the way to score it is to give it a question where you already
# know the answer and watch whether the *presentation* moves its verdict.

# %%
import collections

from peb import ask
from peb.checks import wilson

MODEL = "claude-opus-5"

# %% [markdown]
# ### §14.4a Position
#
# Twelve arithmetic questions with one right and one wrong answer, each shown in
# both orders. Arithmetic because the verdict is not a matter of taste: there is
# a correct answer and the judge either tracks it or tracks the position.

# %%
QUESTIONS = [
    ("17 x 23", "391", "397"), ("144 / 12", "12", "14"),
    ("2^10", "1024", "1048"), ("89 + 147", "236", "226"),
    ("1000 - 377", "623", "633"), ("15 x 15", "225", "215"),
    ("7 x 13", "91", "81"), ("256 / 8", "32", "36"),
    ("45 + 68", "113", "123"), ("9 x 17", "153", "143"),
    ("300 / 4", "75", "85"), ("63 + 29", "92", "82"),
]

JUDGE_PAIR = ("Which answer to this question is correct?\n\n"
              "Question: {q}\n\nAnswer A: {a}\nAnswer B: {b}\n\n"
              "Reply with exactly one character: A or B.")


def verdict(text):
    t = text.strip().upper().lstrip("*( ").rstrip("*). ")
    return t[0] if t and t[0] in "AB" else "?"


for label, correct_slot in (("correct answer shown as A", "A"),
                            ("correct answer shown as B", "B")):
    picks = collections.Counter()
    right = 0
    for q, good, bad in QUESTIONS:
        a, b = (good, bad) if correct_slot == "A" else (bad, good)
        v = verdict(ask(JUDGE_PAIR.format(q=q, a=a, b=b),
                        model=MODEL, max_tokens=4000)[0])
        picks[v] += 1
        right += v == correct_slot
    n = len(QUESTIONS)
    lo, hi = wilson(right, n)
    chose = "  ".join(f"{k} {v}" for k, v in sorted(picks.items()))
    print(f"{label:<28} {right}/{n}   chose: {chose}   95% CI [{lo:.0%}, {hi:.0%}]")

print("\nPublished in §14.4: 12/12 and 12/12 — the judge tracked correctness,")
print("not position, on a task with a checkable answer.")

# %% [markdown]
# ### §14.4b Verbosity
#
# Eight pairs: a terse correct answer against an elaborate wrong one. This is the
# test that separates "the judge knows the answer" from "the judge likes effort".

# %%
PAIRS = [
    ("What causes a 429 response?", "Rate limiting.",
     "A 429 indicates the server is overwhelmed and has entered a protective "
     "degraded mode, typically because an upstream dependency has saturated its "
     "connection pool, which cascades into request rejection at the edge."),
    ("What does max_tokens control?", "The output budget.",
     "max_tokens governs the total context window available to the request, "
     "encompassing both the prompt and the completion, and is the principal "
     "lever for controlling the model's memory across a conversation."),
    ("What is a system prompt?", "Instructions outside the user turn.",
     "The system prompt is a cryptographically separated channel that the model "
     "is architecturally incapable of disregarding, which is why it is the "
     "correct place to put security controls."),
    ("What does temperature do?", "Controls sampling randomness.",
     "Temperature adjusts the model's confidence threshold, so that a lower "
     "value causes it to consult a larger portion of its training data before "
     "committing to a token, improving factual accuracy."),
    ("What is a token?", "A chunk of text, often part of a word.",
     "A token is a single word as delimited by whitespace, which is why token "
     "counts and word counts are interchangeable for billing purposes."),
    ("What is an embedding?", "A vector representation of text.",
     "An embedding is a compressed copy of the source document stored in the "
     "model's weights, which can be decompressed on demand to recover the "
     "original text verbatim."),
    ("What is fine-tuning?", "Further training on your own examples.",
     "Fine-tuning appends your examples to the model's prompt at inference time, "
     "which is why it increases per-request cost in proportion to dataset size."),
    ("What is a stop sequence?", "A string that ends generation.",
     "A stop sequence is a safety control that prevents the model from producing "
     "disallowed content, and is enforced by a separate classifier model."),
]

JUDGE_QUALITY = ("Which of these two answers is better?\n\n"
                 "Question: {q}\n\nAnswer A: {a}\n\nAnswer B: {b}\n\n"
                 "Reply with exactly one character: A or B.")

right = 0
picks = collections.Counter()
for i, (q, terse, elaborate) in enumerate(PAIRS):
    # Alternate the slot so position cannot be the explanation.
    a, b = (terse, elaborate) if i % 2 == 0 else (elaborate, terse)
    want = "A" if i % 2 == 0 else "B"
    v = verdict(ask(JUDGE_QUALITY.format(q=q, a=a, b=b), model=MODEL, max_tokens=4000)[0])
    picks[v] += 1
    right += v == want

lo, hi = wilson(right, len(PAIRS))
print(f"terse + right over elaborate + wrong   {right}/{len(PAIRS)}   "
      f"95% CI [{lo:.0%}, {hi:.0%}]")
print(f"slots chosen: {dict(picks)}")
print("\nPublished in §14.4: 16 of 16 (over sixteen pairs; eight run here).")

# %% [markdown]
# ### §14.4c Two judges on a subjective question
#
# The chapter's most valuable result, and the one where positional bias finally
# appears. Two explanations of prompt caching, neither wrong, shown to two
# different judges in both orders.

# %%
EXPL_1 = ("Prompt caching stores the processed form of a stable prefix so that "
          "repeated requests sharing that prefix skip re-processing it. You pay "
          "a write cost once and a much lower read cost thereafter, so it pays "
          "off when the prefix is long, stable, and reused often.")

EXPL_2 = ("Caching works on the front of your prompt. Put the parts that never "
          "change first -- the system prompt, the tool definitions, the skill "
          "descriptions -- and the provider can reuse the work it already did on "
          "them. Change a byte near the top and the cache misses for everything "
          "after it.")

JUDGES = ["claude-opus-5", "claude-sonnet-5"]
SUBJECTIVE = ("Which explanation of prompt caching is better for a working "
              "engineer?\n\nA: {a}\n\nB: {b}\n\nReply with exactly one character: A or B.")

print(f"{'judge':<20} {'1 shown as A':>14} {'1 shown as B':>14}   consistent?")
for judge in JUDGES:
    v1 = verdict(ask(SUBJECTIVE.format(a=EXPL_1, b=EXPL_2), model=judge, max_tokens=4000)[0])
    v2 = verdict(ask(SUBJECTIVE.format(a=EXPL_2, b=EXPL_1), model=judge, max_tokens=4000)[0])
    # Consistent means it picked the same EXPLANATION, not the same letter.
    first_pick = "expl-1" if v1 == "A" else "expl-2"
    second_pick = "expl-2" if v2 == "A" else "expl-1"
    consistent = first_pick == second_pick
    print(f"{judge:<20} {('picked ' + first_pick):>14} {('picked ' + second_pick):>14}"
          f"   {'yes' if consistent else 'NO -- followed position'}")

print("\nOn a question with no checkable answer, a judge that changes its verdict")
print("when the order changes is measuring the slot, not the content. That is why")
print("§14.4 says to score your judge before trusting it -- and why the positional")
print("test above, on arithmetic, cannot detect this failure.")


# %% [markdown]
# ## §14.5 The rubric experiment
#
# The chapter's claim is that a bare 1-to-5 scale carries no information and a
# four-point rubric with named levels does. This is the experiment behind that
# result, and it is the one worth repeating against your own rubric.
#
# Note what the two conditions share: the same explanation, the same judge, the
# same number of runs. The only change is the scale.

# %%
import re as _re

RUBRIC_RUNS = 8

BARE = ("Rate this explanation of prompt caching from 1 to 5.\n\n"
        f"{EXPL_1}\n\nReply with only the number.")

# Four named levels, each in terms of something observable in the text. Level 4
# requires the invalidation rule, which EXPL_1 does not state -- so a working
# rubric should land on 3 and say why.
RUBRIC = ("Score this explanation of prompt caching against the rubric.\n\n"
          "1 -- wrong about what is cached, or describes output caching.\n"
          "2 -- says caching saves money but not what is stored or when it hits.\n"
          "3 -- names the stable prefix and the write/read cost asymmetry.\n"
          "4 -- all of 3, and states what invalidates the cache.\n\n"
          f"{EXPL_1}\n\nReply with only the number.")


def score(reply):
    """First integer in the reply, or None if it answered in prose."""
    m = _re.search(r"\b([1-5])\b", reply or "")
    return int(m.group(1)) if m else None


for label, prompt in (("bare 1-5 scale", BARE), ("4-point rubric", RUBRIC)):
    raw = [ask(prompt, max_tokens=4000)[0] for _ in range(RUBRIC_RUNS)]
    got = [score(r) for r in raw]
    parsed = [g for g in got if g is not None]
    dropped = len(got) - len(parsed)
    print(f"{label:<18} {parsed}   {len(set(parsed))} distinct value"
          f"{'' if len(set(parsed)) == 1 else 's'}"
          f"{f'   ({dropped} of {RUBRIC_RUNS} returned prose, dropped)' if dropped else ''}")

print("\nRead the two rows against each other, not against the book. §14.5 "
      "publishes")
print("eight 5s on the bare scale and five 3s on the rubric with three runs "
      "dropped")
print("as prose. Two runs on 2026-10-08 returned a bare scale moving between 4 "
      "and 5")
print("and eight 3s with nothing dropped: the rubric reproduced exactly, the "
      "ceiling")
print("did not, and the prose failure did not recur. Do not read the exact "
      "sequence")
print("above as the finding -- the finding is that the rubric's number is")
print("attached to a named criterion and the bare scale's is not -- whatever "
      "value it")
print("happens to land on. Dropped runs, when they occur, are §6.4 again: the "
      "fix is")
print("a schema with an integer field, not an instruction to reply with just the "
      "number.")
