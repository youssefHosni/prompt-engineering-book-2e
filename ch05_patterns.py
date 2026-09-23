"""Chapter 5 — Prompt Patterns and Anti-Patterns.

The anti-pattern measured here is the one everybody has tried: making the
instruction louder. Note that the shouting condition changes only one thing.
An earlier draft changed two (capitals *and* added "important"), which measures
nothing.
"""
import re
from peb import ask

RUNS = 10

BASE = ("Summarise the paragraph below in one sentence of at most 15 words.\n\n"
        "The depot moved 412 pallets in March, up from 388 in February, "
        "though two of the four loading bays were closed for resurfacing.")

CONDITIONS = {
    "plain":    BASE,
    "shouting": BASE.replace("at most 15 words", "AT MOST 15 WORDS"),
    "urgent":   BASE.replace("Summarise", "IMPORTANT! Summarise"),
    "format":   BASE + "\n\nBegin your reply with the line 'WORKING:' and show "
                       "your steps, then a line 'ANSWER:' with just the number.",
}


def within_limit(text):
    body = text.split("ANSWER:")[-1] if "ANSWER:" in text else text
    return len(body.split()) <= 15


def main():
    print("§5.3  does louder help?  (one variable changed per condition)\n")
    for label, prompt in CONDITIONS.items():
        ok = sum(within_limit(ask(prompt, max_tokens=500)[0]) for _ in range(RUNS))
        print(f"  {label:<10} {ok}/{RUNS} inside the limit")
    print("\n  Emphasis is not an instruction. Structure is.\n")


if __name__ == "__main__":
    main()
