"""Appendix B — Instruction fine-tuning a small model with LoRA.

This is the one thing in the book that needs a GPU. Nothing else depends on it.

Run the stages in order:

    python appendix_b_finetuning.py data      # build and inspect the dataset
    python appendix_b_finetuning.py train     # LoRA fine-tune (GPU)
    python appendix_b_finetuning.py score     # base vs. tuned, on a holdout

The `data` stage runs anywhere and is worth doing first: most fine-tuning
disappointments are dataset problems, and you can see them without a GPU.
"""
import sys

BASE = "your-chosen-small-instruct-model"

# Every row agrees on length, register, and what a good summary contains.
# Consistency is the property that matters; several hundred consistent rows
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


def build_dataset():
    from datasets import Dataset
    ds = Dataset.from_list(ROWS).train_test_split(test_size=0.1, seed=0)
    print(ds)
    lengths = [len(r["completion"].split()) for r in ROWS]
    print(f"\ncompletion lengths: min={min(lengths)} max={max(lengths)} "
          f"mean={sum(lengths) / len(lengths):.1f}")
    print("If that spread is wide, fix the dataset before touching a GPU.")
    return ds


def train(ds):
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import SFTConfig, SFTTrainer

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
    model.print_trainable_parameters()   # expect well under 1% of the total

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
    return tok, model


# the same three questions Chapter 14 asks of anything
#   1. exact or programmatic checks first
#   2. the base model with your best prompt as the baseline
#   3. a holdout you have not tuned against

def score(model_fn, examples):
    ok = 0
    for ex in examples:
        out = model_fn(ex["prompt"])
        ok += (len(out.split()) <= 25                 # your length rule
               and ex["order_ref"] in out             # must-survive check, §7.4
               and "\n" not in out.strip())           # single line
    return ok / len(examples)


def score_stage(ds):
    """The comparison that decides whether the fine-tune was worth it."""
    from peb import ask

    holdout = list(ds["test"])

    def base_with_a_good_prompt(prompt):
        # The baseline is not the base model with a lazy prompt. It is the base
        # model with the best prompt you can write -- otherwise you are
        # measuring your own prompt, not the fine-tune.
        text, _ = ask(prompt + "\n\nOne sentence, at most 25 words, one line, "
                               "and keep the order reference exactly as written.",
                      max_tokens=200)
        return text.strip()

    print(f"baseline (prompted base model): {score(base_with_a_good_prompt, holdout):.0%}")
    print("tuned: load the adapter and pass its generate() here.")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "data"
    ds = build_dataset()
    if stage == "train":
        train(ds)
    elif stage == "score":
        score_stage(ds)
