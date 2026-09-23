"""Chapter 13 — Operating a Loop.

This chapter opens with a failure of the author's own instrument: a verification
step that returned an empty string on every call, and scoring code that read the
empty string as a pass. Both versions are here.

  13.2  the free-text checker that returns nothing
  13.3  the same checker with a schema
  13.4  who actually catches violations: the model, a checklist, or three lines
        of code
"""
import json
import re

from peb import ask

RUNS = 12

TASK = ("Write a 50-word note to a customer whose delivery was late. "
        "Do not offer a refund. Sign as 'Kestrel Support'.")

CHECK = {"type": "object",
         "properties": {"word_count": {"type": "integer"},
                        "signed":     {"type": "boolean"}},
         "required": ["word_count", "signed"],
         "additionalProperties": False}


def violations(reply):
    """Three lines of code. The baseline everything else has to beat."""
    problems = []
    if not 45 <= len(reply.split()) <= 55:  problems.append("length")
    if "refund" in reply.lower():           problems.append("refund")
    if "Kestrel Support" not in reply:      problems.append("unsigned")
    return problems


def main():
    replies = [ask(TASK, max_tokens=500)[0] for _ in range(RUNS)]
    truth = [violations(r) for r in replies]
    bad = sum(bool(v) for v in truth)
    print(f"{RUNS} replies; {bad} violate at least one rule (verified in code)")
    print(f"   word counts: {[len(r.split()) for r in replies]}\n")

    print("§13.2  the free-text checker\n")
    empty = 0
    for r in replies[:3]:
        text, _ = ask(f"Check this reply against the rules.\n\nRules: {TASK}\n\n"
                      f"Reply:\n{r}", max_tokens=16)   # the budget that caused it
        empty += not text.strip()
        print(f"  {text.strip()[:60]!r}")
    print(f"\n  {empty}/3 returned nothing at all — and an `if not problems` test\n"
          f"  reads every one of those as a pass.\n")

    print("§13.3  the same checker, with a schema and a real budget\n")
    parsed = caught = 0
    for r, t in zip(replies, truth):
        text, _ = ask(f"Return JSON matching this schema for the reply below.\n"
                      f"{json.dumps(CHECK)}\n\nReply:\n{r}", max_tokens=300)
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            continue
        try:
            obj = json.loads(m.group(0))
        except Exception:
            continue
        parsed += 1
        # The model's own word count, against the real one.
        if abs(obj.get("word_count", -1) - len(r.split())) <= 1:
            caught += 1
    print(f"  parsed {parsed}/{RUNS}   word count within 1: {caught}/{max(parsed,1)}\n")

    print("§13.4  who catches the violations?\n")
    same_model = 0
    for r, t in zip(replies, truth):
        text, _ = ask(f"Rules: {TASK}\n\nReply:\n{r}\n\n"
                      f"Is it compliant? Answer YES or NO only.", max_tokens=100)
        said_no = text.strip().upper().startswith("NO")
        same_model += (said_no == bool(t))
    print(f"  same model, 'is it compliant?'   agreed with code on {same_model}/{RUNS}")
    print(f"  three lines of code              {bad}/{bad} by definition\n")
    print("  Use the model to judge what code cannot express. Use code for\n"
          "  everything it can — which is more than you think.\n")


if __name__ == "__main__":
    main()
