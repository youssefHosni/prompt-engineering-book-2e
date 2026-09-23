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
# # Chapter 1 — How Instruction-Tuned Models Work
#
# | § | what it shows |
# |---|---|
# | 1.3 | "exactly three words" — precise, checkable, and not reliably followed |
# | 1.5 | a product that does not exist, asked about confidently |
# | 1.6 | tokens billed vs. words returned: the cheapest instrument you have |

# %%
from peb import ask

RUNS = 6

# %% [markdown]
# ## §1.3 An instruction that is precise and still not followed
#
# Nothing here is ambiguous. The model simply does not count.

# %%
prompt_three_words = (
    "Summarise the following in exactly three words.\n\n"
    "The 2024 revision of the building code raised the minimum insulation "
    "requirement for new residential roofs from R-38 to R-49, "
    "effective January 2025."
)

hits = 0
for i in range(1, RUNS + 1):
    text, _ = ask(prompt_three_words, max_tokens=4000)
    n = len(text.split())
    hits += (n == 3)
    print(f"run {i}  words={n:<3} {text.strip()[:50]}")

# The count is done in code, never by asking the model. §13.4 is why.
print(f"\n{hits}/{RUNS} runs hit exactly three words.")

# %% [markdown]
# ## §1.5 A product that does not exist
#
# The first edition's headline example. Worth re-running: this is one of the
# 2023-era failure modes that largely does **not** reproduce on current frontier
# models, and the chapter says so rather than pretending otherwise.

# %%
text, _ = ask("Tell me about the AeroGlide UltraSlim Smart Toothbrush by Boie",
              max_tokens=4000)
print(text.strip()[:600])

hedged = any(w in text.lower() for w in
             ("don't have", "do not have", "not aware", "no record", "unable to find"))
print(f"\nhedged rather than invented: {hedged}")

# %% [markdown]
# ## §1.6 Tokens billed vs. words returned
#
# The gap between what you pay for and what you get back is the cheapest
# diagnostic available, and you will only look at it if it is already in your
# hand — which is why `ask()` returns usage alongside the text.

# %%
prompt_api = ("How do I use the batch_stream() method on the Anthropic Python "
              "client? Show a short code example.")

for label, p in (("three words", prompt_three_words), ("api question", prompt_api)):
    text, usage = ask(p, max_tokens=4000)
    words = len(text.split())
    print(f"{label:<14} in={usage.input_tokens:<5} out={usage.output_tokens:<5} "
          f"words={words:<5} ratio={usage.output_tokens / max(words, 1):.2f}")

print("\nA ratio far above ~1.4 means tokens went somewhere the text did not.")
