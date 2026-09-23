"""Chapter 1 — From Pre-training to Instruction Following.

Three experiments:
  1.3  "exactly three words" — precise, checkable, and not reliably followed
  1.5  a product that does not exist, asked about confidently
  1.6  tokens billed vs. words returned, the cheapest instrument you have
"""
from peb import ask

RUNS = 6

prompt_three_words = (
    "Summarise the following in exactly three words.\n\n"
    "The 2024 revision of the building code raised the minimum insulation "
    "requirement for new residential roofs from R-38 to R-49, "
    "effective January 2025."
)

prompt_nonexistent = "Tell me about the AeroGlide UltraSlim Smart Toothbrush by Boie"

prompt_api = ("How do I use the batch_stream() method on the Anthropic Python client? "
              "Show a short code example.")


def exactly_three_words():
    print("§1.3  'exactly three words'\n")
    hits = 0
    for i in range(1, RUNS + 1):
        text, _ = ask(prompt_three_words, max_tokens=200)
        n = len(text.split())
        hits += (n == 3)
        print(f"  run {i}  words={n:<3} {text.strip()[:50]}")
    # The count is done in code, not by asking the model. Chapter 13 explains why.
    print(f"\n  {hits}/{RUNS} runs hit exactly three words.\n")


def confident_about_nothing():
    print("§1.5  a product that does not exist\n")
    text, _ = ask(prompt_nonexistent, max_tokens=400)
    print("  " + text.strip().replace("\n", "\n  ")[:600])
    hedged = any(w in text.lower() for w in
                 ("don't have", "do not have", "not aware", "no record", "unable to find"))
    print(f"\n  hedged rather than invented: {hedged}\n")


def billed_vs_returned():
    print("§1.6  tokens billed vs. words returned\n")
    for label, p in (("three words", prompt_three_words), ("api question", prompt_api)):
        text, usage = ask(p, max_tokens=800)
        words = len(text.split())
        print(f"  {label:<14} in={usage.input_tokens:<5} out={usage.output_tokens:<5} "
              f"words={words:<5} ratio={usage.output_tokens / max(words, 1):.2f}")
    print("\n  A ratio far above ~1.4 means tokens went somewhere the text did not.\n")


if __name__ == "__main__":
    exactly_three_words()
    confident_about_nothing()
    billed_vs_returned()
