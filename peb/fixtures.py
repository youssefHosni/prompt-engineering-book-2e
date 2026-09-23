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
