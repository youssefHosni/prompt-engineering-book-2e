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
import os
import re

from peb import ask

RUNS = 14

# The chapter's numbers were measured on Sonnet. Pinned here so this script
# reproduces the chapter; PEB_MODEL still overrides if you want to compare.
MODEL = os.getenv("PEB_MODEL", "claude-sonnet-5")

# The chapter's experiment, reproduced exactly: twenty distinct messages rather
# than one prompt repeated, and the wording the book used. Both matter. A single
# prompt run fourteen times measures sampling variance; fourteen different
# messages measure the instruction, which is what the chapter claims to be
# about. The band is 55 to 60; ask for 50 with a loose check and every reply
# passes, the §13.4 comparison becomes 0/0, and nothing is measured.
MESSAGES = [f"Order KL-{100000 + i * 13} arrived damaged. What should I do?"
            for i in range(RUNS)]

RULES = ("between 55 and 60 words, signed as 'Kestrel Support'")

DRAFT = ("Write a reply to the customer about a damaged delivery.\n"
         "Length: exactly between 55 and 60 words.\n"
         "Sign as 'Kestrel Support'.\n\nMessage: ```{m}```")

CHECK = {"type": "object",
         "properties": {"word_count": {"type": "integer"},
                        "signed":     {"type": "boolean"}},
         "required": ["word_count", "signed"],
         "additionalProperties": False}


def violations(reply):
    """Three lines of code. The baseline everything else has to beat."""
    problems = []
    n = len(reply.split())
    if not 55 <= n <= 60:              problems.append(f"length={n}")
    if "Kestrel Support" not in reply: problems.append("unsigned")
    return problems


def main():
    replies = [ask(DRAFT.format(m=m), model=MODEL, max_tokens=4000)[0]
               for m in MESSAGES]
    truth = [violations(r) for r in replies]
    bad = sum(bool(v) for v in truth)
    print(f"{RUNS} replies; {bad} violate at least one rule (verified in code)")
    print(f"   word counts: {[len(r.split()) for r in replies]}\n")

    print("§13.2  the free-text checker\n")
    starved = 0
    for r in replies[:3]:
        try:
            # 16 tokens: the budget that caused the original failure.
            text, _ = ask(f"Check this reply against the rules.\n\nRules: {RULES}\n\n"
                          f"Reply:\n{r}", model=MODEL, max_tokens=16)
            print(f"  returned {text.strip()[:60]!r}")
        except RuntimeError as e:
            starved += 1
            print(f"  RuntimeError: {e}")
    print(f"\n  {starved}/3 raised instead of returning quietly.\n"
          f"  Without the guard clause every one of those is an empty string, and\n"
          f"  an `if not problems` test reads an empty string as a pass. That is\n"
          f"  the bug this chapter opens with.\n")

    print("§13.3  the same checker, with a schema and a real budget\n")
    parsed = caught = 0
    for r, t in zip(replies, truth):
        text, _ = ask(f"Return JSON matching this schema for the reply below.\n"
                      f"{json.dumps(CHECK)}\n\nReply:\n{r}", model=MODEL, max_tokens=4000)
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
        text, _ = ask(f"Rules: {RULES}\n\nReply:\n{r}\n\n"
                      f"Is it compliant? Answer YES or NO only.", model=MODEL, max_tokens=4000)
        said_no = text.strip().upper().startswith("NO")
        same_model += (said_no == bool(t))
    print(f"  same model, 'is it compliant?'   agreed with code on {same_model}/{RUNS}")
    print(f"  three lines of code              {bad}/{bad} by definition\n")
    print("  Use the model to judge what code cannot express. Use code for\n"
          "  everything it can — which is more than you think.\n")


if __name__ == "__main__":
    main()
