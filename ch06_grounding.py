"""Chapter 6 — Grounding, Hallucination, and Retrieval.

  6.4  giving the model a way to say "not in the document"
  6.5  two passages that disagree, and a rule for which wins
"""
from peb import ask

DOC = """Kestrel Logistics Service Terms, revision 2026-01-14.

Standard delivery is 3 working days from dispatch. Palletised freight over
500 kg is 5 working days. A fuel surcharge of 4.5% applies to all shipments
booked after 2026-02-01.
"""

OLD = """Kestrel Logistics Service Terms, revision 2025-06-02.
The fuel surcharge is 2.0% and applies to palletised freight only.
"""

grounded = """Answer using ONLY the document. Quote the exact sentence you used,
then give the answer. If no sentence in the document answers the question,
reply with exactly: NOT IN DOCUMENT

Question: {q}"""

CONFLICT_RULE = (
    "If two passages conflict, prefer the one with the later revision date and say "
    "which you used. If they have no dates, reply exactly: CONFLICT.")

ANSWERABLE = "What is the fuel surcharge?"
UNANSWERABLE = "What is the penalty for a missed collection?"


def escape_hatch():
    print("§6.4  a question the document does not answer\n")
    for q in (ANSWERABLE, UNANSWERABLE):
        text, _ = ask(f"{DOC}\n\n" + grounded.format(q=q), max_tokens=400)
        first = text.strip().splitlines()[0] if text.strip() else ""
        print(f"  {q}\n    -> {first[:80]!r}")
    print("\n  Without the escape hatch the second question gets an answer anyway.\n")


def conflicting_passages():
    print("§6.5  two revisions that disagree\n")
    prompt = (f"{OLD}\n---\n{DOC}\n\n{CONFLICT_RULE}\n\n"
              f"Question: {ANSWERABLE}")
    text, _ = ask(prompt, max_tokens=400)
    print("  " + text.strip().replace("\n", "\n  ")[:400])
    print(f"\n  cited the later revision: {'2026-01-14' in text}\n")


if __name__ == "__main__":
    escape_hatch()
    conflicting_passages()
