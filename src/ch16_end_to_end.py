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

# %% [markdown]
# ## §16.7 The evaluation set
#
# Sixteen labelled messages: three for each of the four policy areas, and four
# that must escalate. Each stage scored separately, because a pipeline that is
# only scored end-to-end tells you it is broken without telling you where.
#
# The twelve non-escalating messages are the ones that reach the drafter, which
# is where `11 of 12` gets its denominator.
#
# Provenance: triage on `claude-sonnet-5` and `claude-haiku-4.5`, drafting on
# `claude-sonnet-5`, default sampling, run date in `outputs/run-log.jsonl`.

# %%
import collections
import json
import re

# %% [markdown]
# The pipeline stages again, parameterised by model. §16.7 compares two triage
# models, which the single-model versions above cannot express.

# %%
def triage_with(message, model):
    prompt = (f"Triage this customer message.\n"
              f"Reply with one JSON object matching this schema and nothing else.\n\n"
              f"{json.dumps(TRIAGE_SCHEMA, indent=2)}\n\n{TRIAGE_RULE}\n\n"
              f"Message: ```{message}```")
    text, _ = ask(prompt, model=model, max_tokens=4000)
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"no JSON in triage reply: {text[:60]!r}")
    return json.loads(m.group(0))


def draft_with(message, order, model, feedback=None):
    prompt = (f"Policy:\n{POLICY}\n\nOrder record:\n{json.dumps(order, indent=2)}\n\n"
              f"{REPLY_RULES}\n\nCustomer: ```{message}```")
    if feedback:
        prompt += f"\n\nYour previous draft failed these checks: {'; '.join(feedback)}"
    return ask(prompt, model=model, max_tokens=4000)[0].strip()


from peb import ask
from peb.checks import validate, wilson
from peb.fixtures import ORDER, POLICY

TRIAGE_MODELS = ["claude-sonnet-5", "claude-haiku-4.5"]
DRAFT_MODEL = "claude-sonnet-5"

# (message, intent, needs_human)
MESSAGES = [
    # delivery
    ("My Nordic 400 arrived 5 days late on order KL-449021. What are you doing about it?",
     "delivery", False),
    ("Order KL-318402 was promised Tuesday and still hasn't turned up. Where is it?",
     "delivery", False),
    ("The tracking has said 'out for delivery' for three days now on KL-771203.",
     "delivery", False),
    # claims
    ("The drip tray on my Nordic 400 warped after a week. Order KL-449021.",
     "claims", False),
    ("Half the tiles in KL-662190 arrived cracked. I have photographs.",
     "claims", False),
    ("The machine on KL-884417 stopped working on day nine. I'd like it replaced.",
     "claims", False),
    # packaging
    ("The pallet on KL-220984 was shrink-wrapped to about 2.1m and it toppled.",
     "packaging", False),
    ("Fragile items in KL-553001 came with no void fill at all, just loose in the box.",
     "packaging", False),
    ("Can you confirm what packaging you need for liquids before I book?",
     "packaging", False),
    # surcharge
    ("Why is there a 4.5% line on invoice KL-449021 that wasn't on the quote?",
     "surcharge", False),
    ("I was charged a fuel surcharge on a standard delivery. Is that right?",
     "surcharge", False),
    ("Can you explain how the surcharge on KL-990112 is calculated?",
     "surcharge", False),
    # escalation: legal threat or refund over 500
    ("This is the third failed delivery. I am referring this to my solicitor.",
     "delivery", True),
    ("I want a full refund of 1,850 GBP for order KL-449021, not a replacement.",
     "claims", True),
    ("Unless you refund the 920 GBP today I will be taking legal action.",
     "claims", True),
    ("My lawyer has advised me to request the full 2,400 GBP back on KL-100238.",
     "claims", True),
]

assert len(MESSAGES) == 16
assert sum(1 for _, _, esc in MESSAGES if esc) == 4
print(f"{len(MESSAGES)} messages, {sum(1 for *_, e in MESSAGES if e)} requiring escalation")

# %% [markdown]
# ### Stage 1 — triage, scored per model

# %%
rows = {}
for model in TRIAGE_MODELS:
    intent_ok = caught = missed = false_alarm = 0
    failures = []
    for msg, want_intent, want_esc in MESSAGES:
        try:
            t = triage_with(msg, model)
        except Exception as e:
            failures.append((msg[:40], f"{type(e).__name__}"))
            continue
        if t.get("intent") == want_intent:
            intent_ok += 1
        else:
            failures.append((msg[:40], f"{t.get('intent')} != {want_intent}"))
        got_esc = bool(t.get("needs_human"))
        caught += got_esc and want_esc
        missed += want_esc and not got_esc
        false_alarm += got_esc and not want_esc
    rows[model] = (intent_ok, caught, missed, false_alarm, failures)

print(f"{'triage model':<20}{'intent correct':>16}{'escalation caught':>20}"
      f"{'missed':>9}{'false alarms':>14}")
for model, (ok, caught, missed, fa, _) in rows.items():
    print(f"{model:<20}{f'{ok}/16':>16}{f'{caught} of 4':>20}{missed:>9}{fa:>14}")

print("\nPublished in §16.7: 13/16 and 14/16, 4 of 4 for both, 0 missed, 0 false alarms.")

for model, (_, _, _, _, failures) in rows.items():
    if failures:
        print(f"\n{model} disagreed with the label on:")
        for msg, why in failures:
            print(f"  {msg:<42} {why}")

# %% [markdown]
# ### Stage 2 — drafting and validation
#
# Only the twelve non-escalating messages reach the drafter: an escalated message
# stops at triage by design, which is what makes the denominator 12 rather than 16.

# %%
drafted = [m for m in MESSAGES if not m[2]]
passed = 0
reasons = collections.Counter()

for msg, _, _ in drafted:
    feedback = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        reply = draft_with(msg, ORDER, DRAFT_MODEL, feedback)
        problems = validate(reply, ORDER)
        if not problems:
            passed += 1
            break
        feedback = problems
    else:
        reasons[problems[0].split()[0]] += 1

lo, hi = wilson(passed, len(drafted))
print(f"validator pass rate ({DRAFT_MODEL} drafting)   {passed} of {len(drafted)}"
      f"   95% CI [{lo:.0%}, {hi:.0%}]")
if reasons:
    print(f"failures after {MAX_ATTEMPTS} attempts: {dict(reasons)}")
print("\nPublished in §16.7: 11 of 12, one failure: length.")
