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
# # Chapter 16 — Building an End-to-End System
#
# The whole book in one pipeline. Nothing new is introduced here; every
# technique has appeared earlier.
#
# | stage | from |
# |---|---|
# | triage | §8.2 schema-constrained extraction |
# | reply | §6.4 grounded, with an escape hatch |
# | validate | §13.4 code, because code can express these rules |
# | retry | §12.3 bounded, because an unbounded retry is an outage |

# %%
import json
import re

from peb import ask
from peb.checks import validate
from peb.fixtures import ORDER, POLICY

MAX_ATTEMPTS = 3

CUSTOMER = ("My Nordic 400 arrived 5 days late on order KL-449021, and the drip "
            "tray has already warped. What are you going to do about it?")

# %% [markdown]
# ## Triage
#
# `needs_human` is a deliberately narrow rule. A vague escalation condition
# escalates everything, and a pipeline that escalates everything is a queue.

# %%
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


def triage(message):
    prompt = (f"Triage this customer message.\n"
              f"Reply with one JSON object matching this schema and nothing else.\n\n"
              f"{json.dumps(TRIAGE_SCHEMA, indent=2)}\n\n{TRIAGE_RULE}\n\n"
              f"Message: ```{message}```")
    text, _ = ask(prompt, max_tokens=4000)
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"no JSON in triage reply: {text[:80]!r}")
    obj = json.loads(m.group(0))
    missing = set(TRIAGE_SCHEMA["required"]) - set(obj)
    if missing:
        raise ValueError(f"triage missing keys: {sorted(missing)}")
    return obj


# %% [markdown]
# ## Draft
#
# The feedback line matters. On a retry the model is told *what failed*, not
# "try again" — §12.3.

# %%
REPLY_RULES = (
    "Use ONLY the policy and order record above for any factual claim.\n"
    "If the answer is not in them, say you will check and come back.\n"
    "Length: 50 to 70 words.\n"
    "Do not offer a refund. Do not invent dates or amounts.\n"
    "Sign as 'Kestrel Support'.")


def draft(message, order, feedback=None):
    prompt = (f"Policy:\n{POLICY}\n\nOrder record:\n{json.dumps(order, indent=2)}\n\n"
              f"{REPLY_RULES}\n\nCustomer: ```{message}```")
    if feedback:
        prompt += f"\n\nYour previous draft failed these checks: {'; '.join(feedback)}"
    text, _ = ask(prompt, max_tokens=4000)
    return text.strip()


# %% [markdown]
# ## Run it
#
# `validate()` lives in `peb/checks.py` and is covered by `test_offline.py`,
# which runs without a key. The checker is the part most worth testing.

# %%
print("CUSTOMER  " + CUSTOMER + "\n")

t = triage(CUSTOMER)
print("triage    " + json.dumps(t))

if t["needs_human"]:
    print("\n-> escalated. The pipeline stops here, by design.")
else:
    feedback = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        reply = draft(CUSTOMER, ORDER, feedback)
        problems = validate(reply, ORDER)
        print(f"\nattempt {attempt}  ({len(reply.split())} words)")
        print(reply)
        if not problems:
            print("\n-> passed every check. Sent.")
            break
        print(f"failed: {problems}")
        feedback = problems
    else:
        # Bounded. The failure is visible, not silent.
        print(f"\n-> {MAX_ATTEMPTS} attempts, still failing {feedback}. Handed to a human.")
