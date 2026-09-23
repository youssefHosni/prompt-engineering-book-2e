"""Chapter 14 — Evaluation.

Ten examples, three scorers, and a Wilson interval so that 8/10 is reported as
what it actually is rather than as "80%".

  14.1  start with ten examples
  14.3  exact, fuzzy, and judged
  14.4  LLM-as-judge, tested against labels rather than trusted
  14.6  a regression suite, and not fooling yourself
"""
import math
import re

from peb import ask

# §14.1 — ten examples, written before the prompt was tuned. Each is an input
# and the answer a competent human gives.
#
# The first ten are the ordinary set, and a current model scores 10/10 on them.
# That is a warning about the set, not a result about the model: an eval where
# everything passes cannot tell you where the prompt is broken, which is the
# only thing §14.1 claims ten examples are good for. The six after them are the
# awkward cases -- the ones a careful human still answers confidently but where
# the rule genuinely bites.
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

JUDGE = ("Is the extracted reference correct for this message?\n"
         "Message: ```{msg}```\nExtracted: {got}\nExpected: {want}\n"
         "Answer YES or NO only.")


def wilson(k, n, z=1.96):
    """Wilson score interval. 8/10 is not 80%; it is 80% give or take 24 points."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def exact(got, want):
    return got.strip().upper() == want


def fuzzy(got, want):
    """Ignores case and dashes — catches the near-misses exact scoring hides."""
    norm = lambda s: re.sub(r"[^A-Z0-9]", "", s.upper())
    return norm(got) == norm(want)


def main():
    print(f"§14.1  {len(CASES)} examples, scored three ways\n")
    results = []
    for msg, want in CASES:
        got, _ = ask(PROMPT.format(msg=msg), max_tokens=4000)
        got = got.strip().splitlines()[0] if got.strip() else ""
        results.append((msg, want, got))
        mark = "ok " if exact(got, want) else "MISS"
        print(f"  [{mark}] want={want:<10} got={got[:16]:<16} {msg[:34]!r}")

    n = len(results)
    for label, fn in (("exact", exact), ("fuzzy", fuzzy)):
        k = sum(fn(g, w) for _, w, g in results)
        lo, hi = wilson(k, n)
        print(f"\n  {label:<6} {k}/{n} = {k / n:.0%}   95% CI [{lo:.0%}, {hi:.0%}]")

    print("\n§14.4  the judge, scored against the labels\n")
    agree = 0
    for msg, want, got in results:
        v, _ = ask(JUDGE.format(msg=msg, got=got or "(empty)", want=want), max_tokens=4000)
        said_yes = v.strip().upper().startswith("YES")
        agree += (said_yes == exact(got, want))
    lo, hi = wilson(agree, n)
    print(f"  judge agreed with the label on {agree}/{n}   95% CI [{lo:.0%}, {hi:.0%}]")
    print("\n  A judge you have not scored is an opinion. Ten labels are enough\n"
          "  to find out whether it is a useful one — §14.4.\n")

    print("  And note the interval. With ten examples, 9/10 and 7/10 overlap.\n"
          "  Ten examples tell you where the prompt is broken, not how good it is.\n")


if __name__ == "__main__":
    main()
