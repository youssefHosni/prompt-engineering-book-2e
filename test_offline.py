"""Tests that need no API key.

Everything here checks the *checkers* -- the validators and scorers the book
leans on. That is deliberate. Chapter 13 opens with a verification step that
returned an empty string on every call while the scoring code read it as a
pass, so the instrument is the thing most worth testing.

    python test_offline.py
"""
import sys

import ch09_agents as ch09
import ch14_evaluation as ch14
import ch16_end_to_end as ch16
from peb.fixtures import ORDER

failures = []


def check(name, got, want):
    if got != want:
        failures.append(f"{name}: got {got!r}, want {want!r}")


# --- Chapter 14: scoring and the interval -----------------------------------

check("exact matches", ch14.exact("KL-449021", "KL-449021"), True)
check("exact is case-insensitive after strip",
      ch14.exact(" kl-449021 ", "KL-449021"), True)
check("exact rejects a missing dash", ch14.exact("KL449021", "KL-449021"), False)
check("fuzzy accepts a missing dash", ch14.fuzzy("KL449021", "KL-449021"), True)
check("fuzzy still rejects the wrong number",
      ch14.fuzzy("KL-449022", "KL-449021"), False)

lo, hi = ch14.wilson(8, 10)
check("wilson(8,10) lower", round(lo, 2), 0.49)
check("wilson(8,10) upper", round(hi, 2), 0.94)
check("wilson(0,0) is not a crash", ch14.wilson(0, 0), (0.0, 0.0))
# The claim the chapter makes: with ten examples, 7/10 and 9/10 overlap.
lo7, hi7 = ch14.wilson(7, 10)
lo9, hi9 = ch14.wilson(9, 10)
check("7/10 and 9/10 overlap at n=10", lo9 < hi7, True)


# --- Chapter 16: the validator that can send a reply back -------------------

good = (" ".join(["word"] * 57) + " Kestrel Support")
check("a compliant reply has no problems", ch16.validate(good, ORDER), [])

short = "Too short. Kestrel Support"
check("short reply is caught", any("length" in p for p in ch16.validate(short, ORDER)), True)

refund = " ".join(["word"] * 55) + " refund Kestrel Support"
check("refund is caught", "mentions refund" in ch16.validate(refund, ORDER), True)

unsigned = " ".join(["word"] * 57)
check("missing signature is caught",
      "missing signature" in ch16.validate(unsigned, ORDER), True)

invented = (" ".join(["word"] * 55) + " on 2026-04-01 Kestrel Support")
check("an invented date is caught",
      any("invented date" in p for p in ch16.validate(invented, ORDER)), True)

real_date = (" ".join(["word"] * 55) + f" on {ORDER['delivered']} Kestrel Support")
check("a date from the record is allowed", ch16.validate(real_date, ORDER), [])


# --- Chapter 9: restriction is not a sandbox, but it should still hold ------

check("a plain expression evaluates", ch09.evaluate("len(rows)"), "5")
check("import is refused", ch09.evaluate("__import__('os')"), "refused: expression only")
check("dunder is refused", ch09.evaluate("().__class__"), "refused: expression only")
check("open is refused", ch09.evaluate("open('/etc/passwd')"), "refused: expression only")
check("a bad expression returns an error, not a crash",
      ch09.evaluate("rows[99]").startswith("error:"), True)


if failures:
    print(f"{len(failures)} failure(s):\n")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
print("all offline checks passed")
