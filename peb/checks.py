"""The checkers, separated from the experiments that use them.

Two reasons this is its own module rather than living in the chapter files.

Notebooks run top to bottom, so anything defined in a chapter file would be
re-executed -- and anything that imports a chapter file to reuse a function
would fire that chapter's API calls as a side effect. Tests cannot import from
a notebook cell.

And these are the parts worth testing. Chapter 13's argument is that the
checker is the thing most likely to be silently broken, so the checkers live
somewhere `test_offline.py` can reach them without a key.
"""
import math
import re

# --- Chapter 9: restriction is not isolation --------------------------------

# An allowlist, not an empty namespace. Blanking __builtins__ entirely also
# removes len, sum and round, which leaves the tool unable to answer any of the
# questions it exists for -- a restriction so tight the feature stops working
# is a bug, not security.
SAFE_BUILTINS = {
    "len": len, "sum": sum, "min": min, "max": max, "round": round,
    "sorted": sorted, "set": set, "list": list, "dict": dict, "tuple": tuple,
    "abs": abs, "any": any, "all": all, "enumerate": enumerate, "zip": zip,
    "str": str, "int": int, "float": float, "bool": bool,
}


def evaluate(code, rows):
    """Evaluate one expression over `rows`.

    Restriction, not isolation -- see §15.4. A denylist of substrings is a
    speed bump. Anything that matters runs in a real sandbox.
    """
    if any(tok in code for tok in ("import", "__", "open(", "exec", "eval")):
        return "refused: expression only"
    try:
        # `rows` and the builtins both go in GLOBALS, not locals, and that is
        # the whole fix. eval() gives comprehension and lambda bodies their own
        # scope which can see globals but NOT the locals mapping -- so with
        # `rows` in locals, a plain `sum(r["pallets"] for r in rows)` worked
        # while a nested comprehension raised "name 'rows' is not defined", and
        # a name used inside a lambda was invisible. Both now work.
        #
        # §9.7's trace was captured before this fix and reports both failures.
        # If you are reading that trace against this code, it will not reproduce
        # -- which is the point the chapter makes about tool ergonomics, arriving
        # one layer down.
        env = {"__builtins__": SAFE_BUILTINS, "rows": rows}
        return repr(eval(code, env, {}))
    except Exception as e:
        return f"error: {e}"


# --- Chapter 13: the three lines of code ------------------------------------

def violations(reply, lo=55, hi=60, signature="Kestrel Support"):
    """The baseline every other checker has to beat."""
    problems = []
    n = len(reply.split())
    if not lo <= n <= hi:        problems.append(f"length={n}")
    if signature not in reply:   problems.append("unsigned")
    return problems


# --- Chapter 14: scoring, and the interval ----------------------------------

def norm_dashes(text):
    """Models write 2026\u201101\u201114 with a non-breaking hyphen.

    A substring check for "2026-01-14" then fails on output that is visibly
    correct. This cost one false negative in §6.5 before it was spotted.
    """
    for dash in "\u2010\u2011\u2012\u2013\u2014\u2212":
        text = text.replace(dash, "-")
    return text


def exact(got, want):
    return got.strip().upper() == want


def fuzzy(got, want):
    """Ignores case and dashes -- catches near-misses exact scoring hides."""
    norm = lambda s: re.sub(r"[^A-Z0-9]", "", s.upper())
    return norm(got) == norm(want)


def wilson(k, n, z=1.96):
    """Wilson score interval.

    8/10 is not 80%; it is 80% give or take 24 points. Reporting the point
    estimate alone is how a 14-run experiment gets read as a fact.
    """
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


# --- Chapter 16: the validator that can send a reply back -------------------

def validate(reply, order, lo=50, hi=70):
    problems = []
    n = len(reply.split())
    if not lo <= n <= hi:              problems.append(f"length {n} outside {lo}-{hi}")
    if "refund" in reply.lower():      problems.append("mentions refund")
    if "Kestrel Support" not in reply: problems.append("missing signature")
    # Grounding: any date in the reply must appear in the record supplied.
    known = {order["ordered"], order["delivered"]}
    for d in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", reply):
        if d not in known:
            problems.append(f"invented date {d}")
    return problems
