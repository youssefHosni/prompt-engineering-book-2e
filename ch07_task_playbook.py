"""Chapter 7 — Task Playbooks.

One input, six tasks. The chapter's argument is that these are not six
techniques; they are one technique with the risk moved around.
"""
from peb import ask
from peb.fixtures import REVIEW

pm = """Summarise this review in 2 sentences for a product manager deciding
what to fix next. Report only faults and their severity. Ignore praise and
logistics.

Review: ```{review}```"""

ops = """Summarise this review in 2 sentences for a logistics lead.
Report only delivery and support performance. Ignore the product itself.

Review: ```{review}```"""

extract = """Extract from the review. Use exactly these keys, one per line,
in this order. Use the literal string NONE if a value is absent.

order_ref | ordered_date | arrived_date | support_hours

Review: ```{review}```"""

classify = """Classify this review. Reply with exactly these three lines
and nothing else:

sentiment: positive | negative | mixed
recommends: yes | no
faults: a comma-separated list, or NONE

Review: ```{review}```"""

transform = """Rewrite the review as an internal support ticket. Neutral register,
no first person, keep every order reference and part name exactly as written.

Review: ```{review}```"""

translate = """Translate the review into Modern Standard Arabic. Keep product
names, order references and part numbers in Latin script, unchanged.

Review: ```{review}```"""

expand = """Write a reply to this customer.
Length: 60 to 80 words.
Acknowledge the late delivery and the drip tray.
Offer a replacement tray. Do not offer a refund.
Do not promise a delivery date.
Sign as 'Kestrel Support'.

Review: ```{review}```"""

must_keep = ["KL-449021", "drip tray", "manual", "support"]


def run(label, template, **checks):
    text, _ = ask(template.format(review=REVIEW), max_tokens=900)
    print(f"--- {label}")
    print("  " + text.strip().replace("\n", "\n  ")[:520])
    for name, fn in checks.items():
        print(f"  [check] {name}: {fn(text)}")
    print()


def main():
    print("§7.1  two summaries of one review, for two readers\n")
    run("summarise (product manager)", pm)
    run("summarise (logistics lead)", ops)

    print("§7.2  extraction — the keys are fixed, so the check is trivial\n")
    run("extract", extract,
        all_keys=lambda t: all(k in t for k in
                               ("order_ref", "ordered_date", "arrived_date", "support_hours")))

    print("§7.3  classification\n")
    run("classify", classify,
        three_lines=lambda t: len([l for l in t.strip().splitlines() if l.strip()]) == 3)

    print("§7.4  transformation — the risk is silent loss\n")
    run("transform", transform,
        kept=lambda t: [k for k in must_keep if k.lower() not in t.lower()] or "all kept")

    print("§7.5  translation — the same check, across a script boundary\n")
    run("translate", translate,
        latin_kept=lambda t: "KL-449021" in t and "Nordic 400" in t)

    print("§7.6  expansion — the highest-risk task, so the most constraints\n")
    run("expand", expand,
        length=lambda t: len(t.split()),
        no_refund=lambda t: "refund" not in t.lower(),
        signed=lambda t: "Kestrel Support" in t)


if __name__ == "__main__":
    main()
