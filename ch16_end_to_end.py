"""Chapter 16 — End to End.

The whole book in one pipeline: triage to a schema, a grounded reply, and a
validator that can send the reply back. Every technique here has appeared
earlier; nothing new is introduced.

  triage   -> §8.2   schema-constrained extraction
  reply    -> §6.4   grounded, with an escape hatch
  validate -> §13.4  code, because code is what can express these rules
  retry    -> §12.3  bounded, because an unbounded retry is an outage
"""
import json
import re

from peb import ask
from peb.fixtures import ORDER, POLICY

MAX_ATTEMPTS = 3

TRIAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "intent":      {"type": "string",
                        "enum": ["delivery", "claims", "packaging",
                                 "surcharge", "other"]},
        "order_ref":   {"type": ["string", "null"]},
        "sentiment":   {"type": "string",
                        "enum": ["positive", "negative", "mixed"]},
        "needs_human": {"type": "boolean"},
    },
    "required": ["intent", "order_ref", "sentiment", "needs_human"],
    "additionalProperties": False,
}

TRIAGE_RULE = ("needs_human is true only if the customer threatens legal action or asks "
               "for a refund over 500 pounds.")

REPLY_RULES = (
    "Use ONLY the policy and order record above for any factual claim.\n"
    "If the answer is not in them, say you will check and come back.\n"
    "Length: 50 to 70 words.\n"
    "Do not offer a refund. Do not invent dates or amounts.\n"
    "Sign as 'Kestrel Support'.")

CUSTOMER = ("My Nordic 400 arrived 5 days late on order KL-449021, and the drip "
            "tray has already warped. What are you going to do about it?")


def triage(message):
    prompt = (f"Triage this customer message.\n"
              f"Reply with one JSON object matching this schema and nothing else.\n\n"
              f"{json.dumps(TRIAGE_SCHEMA, indent=2)}\n\n{TRIAGE_RULE}\n\n"
              f"Message: ```{message}```")
    text, _ = ask(prompt, max_tokens=500)
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"no JSON in triage reply: {text[:80]!r}")
    obj = json.loads(m.group(0))
    missing = set(TRIAGE_SCHEMA["required"]) - set(obj)
    if missing:
        raise ValueError(f"triage missing keys: {sorted(missing)}")
    return obj


def draft(message, order, feedback=None):
    prompt = (f"Policy:\n{POLICY}\n\nOrder record:\n{json.dumps(order, indent=2)}\n\n"
              f"{REPLY_RULES}\n\nCustomer: ```{message}```")
    if feedback:
        # Say what was wrong, not "try again". §12.3.
        prompt += f"\n\nYour previous draft failed these checks: {'; '.join(feedback)}"
    text, _ = ask(prompt, max_tokens=700)
    return text.strip()


def validate(reply, order):
    problems = []
    n = len(reply.split())
    if not 50 <= n <= 70:              problems.append(f"length {n} outside 50-70")
    if "refund" in reply.lower():      problems.append("mentions refund")
    if "Kestrel Support" not in reply: problems.append("missing signature")
    # Grounding: any date in the reply must appear in the record we supplied.
    known = {order["ordered"], order["delivered"]}
    for d in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", reply):
        if d not in known:
            problems.append(f"invented date {d}")
    return problems


def main():
    print("CUSTOMER  " + CUSTOMER + "\n")

    t = triage(CUSTOMER)
    print("triage    " + json.dumps(t))
    if t["needs_human"]:
        print("\n  -> escalated. The pipeline stops here, by design.\n")
        return

    feedback = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        reply = draft(CUSTOMER, ORDER, feedback)
        problems = validate(reply, ORDER)
        print(f"\nattempt {attempt}  ({len(reply.split())} words)")
        print("  " + reply.replace("\n", "\n  "))
        if not problems:
            print("\n  -> passed every check. Sent.\n")
            return
        print(f"  failed: {problems}")
        feedback = problems

    # Bounded. The failure is visible, not silent.
    print(f"\n  -> {MAX_ATTEMPTS} attempts, still failing {feedback}. "
          f"Handed to a human.\n")


if __name__ == "__main__":
    main()
