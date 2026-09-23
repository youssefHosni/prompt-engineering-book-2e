"""Tests that need no API key.

Everything here checks the *checkers* -- the validators and scorers in
`peb/checks.py`. That is deliberate. Chapter 13 opens with a verification step
that returned an empty string on every call while the scoring code read it as a
pass, so the instrument is the thing most worth testing.

The checkers live in `peb/checks.py` rather than in the chapter files precisely
so this file can import them without firing a single API call.

    python test_offline.py
"""
import sys

from peb.checks import evaluate, exact, fuzzy, validate, violations, wilson
from peb.fixtures import ORDER

failures = []


def check(name, got, want):
    if got != want:
        failures.append(f"{name}: got {got!r}, want {want!r}")


# --- Chapter 14: scoring and the interval -----------------------------------

check("exact matches", exact("KL-449021", "KL-449021"), True)
check("exact is case-insensitive after strip", exact(" kl-449021 ", "KL-449021"), True)
check("exact rejects a missing dash", exact("KL449021", "KL-449021"), False)
check("fuzzy accepts a missing dash", fuzzy("KL449021", "KL-449021"), True)
check("fuzzy still rejects the wrong number", fuzzy("KL-449022", "KL-449021"), False)

lo, hi = wilson(8, 10)
check("wilson(8,10) lower", round(lo, 2), 0.49)
check("wilson(8,10) upper", round(hi, 2), 0.94)
check("wilson(0,0) is not a crash", wilson(0, 0), (0.0, 0.0))

# The claim §14.2 makes, and the one that applies to this book's own §13.1
# numbers: at n=14, 9/14 and 5/14 are not distinguishable.
lo9, hi9 = wilson(9, 14)
lo5, hi5 = wilson(5, 14)
check("9/14 and 5/14 overlap at n=14", lo9 < hi5, True)


# --- Chapter 13: the three lines of code ------------------------------------

good13 = " ".join(["word"] * 57) + " Kestrel Support"
check("a compliant reply has no problems", violations(good13), [])
check("an undershoot is caught",
      any("length" in p for p in violations(" ".join(["word"] * 51) + " Kestrel Support")),
      True)
check("an overshoot is caught",
      any("length" in p for p in violations(" ".join(["word"] * 65) + " Kestrel Support")),
      True)
check("missing signature is caught", "unsigned" in violations(" ".join(["word"] * 57)), True)


# --- Chapter 16: the validator that can send a reply back -------------------

good = " ".join(["word"] * 57) + " Kestrel Support"
check("a compliant reply has no problems", validate(good, ORDER), [])
check("short reply is caught",
      any("length" in p for p in validate("Too short. Kestrel Support", ORDER)), True)
check("refund is caught",
      "mentions refund" in validate(" ".join(["word"] * 55) + " refund Kestrel Support", ORDER),
      True)
check("missing signature is caught",
      "missing signature" in validate(" ".join(["word"] * 57), ORDER), True)
check("an invented date is caught",
      any("invented date" in p for p in
          validate(" ".join(["word"] * 55) + " on 2026-04-01 Kestrel Support", ORDER)),
      True)
check("a date from the record is allowed",
      validate(" ".join(["word"] * 55) + f" on {ORDER['delivered']} Kestrel Support", ORDER),
      [])


# --- Chapter 9: restriction is not a sandbox, but it should still hold ------

ROWS = [{"depot": "Leeds", "pallets": 120, "product": "cement"},
        {"depot": "Hull", "pallets": 140, "product": "cement"}]

check("a plain expression evaluates", evaluate("len(rows)", ROWS), "2")
check("builtins the tool needs are present",
      evaluate("sum(r['pallets'] for r in rows)", ROWS), "260")
check("import is refused", evaluate("__import__('os')", ROWS), "refused: expression only")
check("dunder is refused", evaluate("().__class__", ROWS), "refused: expression only")
check("open is refused", evaluate("open('/etc/passwd')", ROWS), "refused: expression only")
check("a bad expression returns an error, not a crash",
      evaluate("rows[99]", ROWS).startswith("error:"), True)


if failures:
    print(f"{len(failures)} failure(s):\n")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
print(f"all offline checks passed ({len(failures)} failures)")
