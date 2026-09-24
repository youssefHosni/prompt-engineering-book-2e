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
# # Appendix B — Instruction Fine-Tuning a Small Model
#
# The one thing in the book that needs a **GPU**. Nothing else depends on it.
#
# Work through it in order. The dataset stage runs anywhere and is worth doing
# first: most fine-tuning disappointments are dataset problems, and you can see
# them without a GPU.

# %%
BASE = "your-chosen-small-instruct-model"

# Every row agrees on length, register, and what a good summary contains.
# Consistency is the property that matters -- several hundred consistent rows
# beat several thousand inconsistent ones.
ROWS = [
    {"prompt": "Summarise this support ticket in one sentence for a triage queue.\n\n"
               "Ticket: Drip tray on a Nordic 400 warped after a week. Order KL-449021.",
     "completion": "Warped drip tray on a Nordic 400, order KL-449021, replacement requested.",
     "order_ref": "KL-449021"},
    {"prompt": "Summarise this support ticket in one sentence for a triage queue.\n\n"
               "Ticket: Delivery on KL-449022 is six days late and the customer wants an ETA.",
     "completion": "Late delivery on order KL-449022, customer requests an ETA.",
     "order_ref": "KL-449022"},
    {"prompt": "Summarise this support ticket in one sentence for a triage queue.\n\n"
               "Ticket: Manual for KL-449023 has an untranslated descaling step.",
     "completion": "Mistranslated descaling instructions in the manual for order KL-449023.",
     "order_ref": "KL-449023"},
    # ... several hundred more, all agreeing on length and register
]

# %% [markdown]
# ## Stage 1 — the dataset
#
# Look at the spread before you touch a GPU. If completion lengths vary widely,
# the model has nothing consistent to learn and the fine-tune will disappoint
# you expensively.

# %%
from datasets import Dataset

ds = Dataset.from_list(ROWS).train_test_split(test_size=0.1, seed=0)
print(ds)

lengths = [len(r["completion"].split()) for r in ROWS]
print(f"\ncompletion lengths: min={min(lengths)} max={max(lengths)} "
      f"mean={sum(lengths) / len(lengths):.1f}")
print("If that spread is wide, fix the dataset before touching a GPU.")

# %% [markdown]
# ## Stage 2 — LoRA fine-tune (GPU)
#
# `print_trainable_parameters()` should report well under 1% of the total. If it
# does not, `target_modules` is wrong and you are training more than you meant.

# %%
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

tok = AutoTokenizer.from_pretrained(BASE)
model = AutoModelForCausalLM.from_pretrained(BASE, dtype="auto", device_map="auto")

lora = LoraConfig(
    r=16,                    # rank: 8-32 covers most cases
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules="all-linear",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora)
model.print_trainable_parameters()

# %%
from trl import SFTConfig, SFTTrainer

cfg = SFTConfig(
    output_dir="out/ticket-summariser",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,      # higher than full fine-tuning; LoRA likes 1e-4 to 3e-4
    bf16=True,
    logging_steps=10,
    eval_strategy="epoch",
)

trainer = SFTTrainer(model=model, args=cfg,
                     train_dataset=ds["train"], eval_dataset=ds["test"])
trainer.train()
trainer.save_model()         # writes the adapter, not the base model

# %% [markdown]
# ## Stage 3 — was it worth it?
#
# The same three questions Chapter 14 asks of anything:
#
# 1. exact or programmatic checks first
# 2. the base model **with your best prompt** as the baseline
# 3. a holdout you have not tuned against
#
# Point 2 is the one people skip. A baseline of the base model with a lazy
# prompt measures your prompt, not your fine-tune.

# %%
def score(model_fn, examples):
    ok = 0
    for ex in examples:
        out = model_fn(ex["prompt"])
        ok += (len(out.split()) <= 25                 # your length rule
               and ex["order_ref"] in out             # must-survive check, §7.4
               and "\n" not in out.strip())           # single line
    return ok / len(examples)


# %%
from peb import ask

holdout = list(ds["test"])


def base_with_a_good_prompt(prompt):
    text, _ = ask(prompt + "\n\nOne sentence, at most 25 words, one line, "
                           "and keep the order reference exactly as written.",
                  max_tokens=4000)
    return text.strip()


print(f"baseline (prompted base model): {score(base_with_a_good_prompt, holdout):.0%}")
print("tuned: load the adapter and pass its generate() here.")
