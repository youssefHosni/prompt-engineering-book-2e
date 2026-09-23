"""Chapter 4 — Give the Model Room to Think.

The headline finding here was, in the first draft, an artifact of the author's
own prompt: "Reply with only the number" suppressed the working and produced a
2/12 baseline that had nothing to do with reasoning. Both conditions are run
here so you can see the difference the instruction makes.
"""
from peb import ask

RUNS = 12

EMAIL = """Hi - the Nordic 400 I ordered last month has started making a loud
grinding noise whenever I pull a shot, and the crema has gone. It was fine for
three weeks. Is this something I can fix or do I need to send it back?"""

steps = """For the customer email below, do the following in order:

1. Identify the product the customer is writing about.
2. Decide whether the message is a complaint, a question, or praise.
3. If it is a complaint, name the specific fault.
4. Draft a two-sentence reply.

Return each step on its own line, labelled.

Email: ```{email}```"""

WORD_PROBLEM = ("A cafe buys 3 boxes of 12 cups and 2 boxes of 18 cups. "
                "It breaks 7 cups. How many cups does it have?")


def structured_steps():
    print("§4.2  four numbered steps, one pass\n")
    text, _ = ask(steps.format(email=EMAIL), max_tokens=700)
    print("  " + text.strip().replace("\n", "\n  ")[:700])
    labelled = sum(text.count(f"{i}.") > 0 for i in range(1, 5))
    print(f"\n  steps present: {labelled}/4\n")


def room_to_think_vs_not():
    print("§4.4  the instruction that suppresses the working\n")
    for label, suffix in (
            ("room to think", " Show your working, then give the answer."),
            ("answer only",   " Reply with only the number.")):
        right = 0
        for _ in range(RUNS):
            text, _ = ask(WORD_PROBLEM + suffix, max_tokens=600)
            digits = [int(s) for s in __import__("re").findall(r"\b\d+\b", text)]
            right += (digits and digits[-1] == 65)   # 36 + 36 - 7
        print(f"  {label:<15} {right}/{RUNS} correct")
    print("\n  Measure the prompt you wrote, not the one you meant to write.\n")


if __name__ == "__main__":
    structured_steps()
    room_to_think_vs_not()
