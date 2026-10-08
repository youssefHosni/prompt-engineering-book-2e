"""The inputs the book reuses across chapters.

Keeping them here is the same argument Appendix A makes about setup: one copy,
one place to change it, no chance of two chapters disagreeing about what the
customer actually wrote.
"""

# The running example. Chapters 7, 8, 15 and 16 all work on this one review.
REVIEW = """Ordered the Nordic 400 on the 3rd, arrived on the 11th which is longer than the
3 days advertised. Machine itself is excellent - the burr grinder is much quieter
than my old one and the espresso is genuinely good. Two problems though. The drip
tray warped after about a week, it's very thin plastic. And the manual is clearly
a bad translation, there's a step about "descaling the vapour wand" that makes no
sense. Support answered in about 4 hours which was better than I expected. Would
still recommend it but be prepared to buy a replacement tray. Order ref KL-449021."""

# The product facts behind Chapter 3's two product-description prompts. The
# prompts differ in what they ask for; the facts they draw on are identical.
FACTS = """Product: Nordic 400 espresso machine
Burr grinder: conical steel, 40 settings, 58 dB at the bean hopper
Boiler: 1.2 L stainless, 9-bar pump
Warranty: 2 years parts and labour, extendable to 4
Dimensions: 32 x 28 x 40 cm
Weight: 9.4 kg
Included: portafilter, twin basket, tamper, descaling sachet"""

# Chapter 16's order record, for the grounded reply.
ORDER = {
    "ref": "KL-449021",
    "product": "Nordic 400",
    "ordered": "2026-03-03",
    "delivered": "2026-03-11",
    "promised_days": 3,
    "status": "delivered",
    "replacement_eligible": True,
}

# Chapter 16's policy excerpt. The reply must cite only this.
POLICY = """Delivery: orders are promised within 3 working days. A delivery that
exceeds the promise by more than 2 working days entitles the customer to a
refund of the delivery fee, applied automatically within 5 working days.

Parts: components that fail within 90 days of delivery are replaced free of
charge, shipped within 2 working days. Drip trays are a covered component.

Escalation: refunds of the full purchase price require a supervisor and are not
offered by support agents."""


# --- Chapter 4 and 5: the twelve arithmetic word problems -------------------
#
# §4.1 describes "twelve multi-step word problems -- buy n items at p each, pay
# with a note, spend a fraction of the change". The original twelve were not
# committed, and the scripts ran ONE problem twelve times, which is a different
# measurement: twelve runs measure sampling variance, twelve problems measure
# the instruction. Both chapters print `n/12`.
#
# This is a reconstruction of that shape, not the original set. It is generated
# from a fixed seed so the problems are stable, and every answer is COMPUTED
# here rather than written down -- a word problem with a hand-typed answer is a
# test of the author's arithmetic, which is the thing being measured.

def arithmetic_12(seed=20260814):
    """Twelve multi-step money problems with computed answers.

    Returns a list of (question, answer) with the answer in whole pence, so
    scoring is `==` rather than a float comparison. Every problem divides
    exactly, every answer is distinct, and the four fractions are all used --
    the first version of this filtered candidates by divisibility, which
    silently made eleven of the twelve "one half".
    """
    import random
    rng = random.Random(seed)
    items = ["notebooks", "pens", "folders", "mugs", "batteries", "cables",
             "sticky-note pads", "staplers", "envelopes", "markers",
             "USB sticks", "clipboards"]
    fracs = [2, 3, 4, 5] * 3                      # each used three times
    out, seen = [], set()
    for name, frac in zip(items, fracs):
        for _ in range(4000):                     # search, do not discard
            n = rng.randint(3, 9)
            pence = rng.randrange(45, 500, 5)
            note = rng.choice([1000, 2000, 5000])
            change = note - n * pence
            if change <= 0 or change % frac:
                continue
            answer = change - change // frac
            if answer in seen:
                continue
            seen.add(answer)
            out.append((
                f"You buy {n} {name} at £{pence / 100:.2f} each and pay with a "
                f"£{note // 100} note. You then spend one {_ordinal(frac)} of "
                f"the change on a coffee. How much money do you have left? "
                f"Answer in pounds and pence.",
                answer))
            break
        else:
            raise RuntimeError(f"no exact problem found for {name}/{frac}")
    return out


def _ordinal(frac):
    return {2: "half", 3: "third", 4: "quarter", 5: "fifth"}[frac]


ARITHMETIC_12 = arithmetic_12()
assert len(ARITHMETIC_12) == 12, len(ARITHMETIC_12)
assert len({a for _, a in ARITHMETIC_12}) == 12          # all answers distinct
assert all(isinstance(a, int) and a > 0 for _, a in ARITHMETIC_12)
