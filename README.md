# Prompt Engineering 2.0: Agents, Skills, and Loops — code

*Engineering Reliable Behaviour from Instruction-Tuned Models*

Runnable notebooks for every chapter.

> Looking for the first edition (2024)? It is archived at
> [Prompt-Engineering-for-Instruction-Tuned-LLM](https://github.com/youssefHosni/Prompt-Engineering-for-Instruction-Tuned-LLM).
> Its examples target `gpt-3.5-turbo` and no longer run.

Every number printed in the book came from a live API call. This repository is
those calls. You can re-run any of them, and `outputs/` holds what the book
recorded so you can see whether your run agrees.

## Setup

```bash
git clone https://github.com/youssefHosni/prompt-engineering-book-2e
cd prompt-engineering-book-2e
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then add your key
```

Then run a chapter:

```bash
python ch03_clear_instructions.py
```

Each script prints the experiment for one chapter, section by section, with the
checks the book applies. They take seconds and a handful of calls.

## Keys

`ANTHROPIC_API_KEY` is what the book's listings assume. If you set
`OPENROUTER_API_KEY` instead, the scripts use that — it is how the book's own
measurements were gathered, and §2.5 is honest about why that is an exploration
tool rather than what you should ship against. Tool use (§8.5, §9.1) is
provider-specific and wants the Anthropic key.

If your key file lives outside this repo, point `PEB_ENV_FILE` at it rather than
copying it in.

## Layout

Each chapter is a notebook. Click a badge to run it in Colab with no setup —
the first cell installs the SDKs and asks for your key. Or clone and open them
locally; they are in `notebooks/`.

| | Chapter | Run it |
|---|---|---|
| **Part I** | **Foundations** | |
| 1 | How Instruction-Tuned Models Work | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/youssefHosni/prompt-engineering-book-2e/blob/main/notebooks/ch01_instruction_following.ipynb) |
| 2 | The Anatomy of a Request | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/youssefHosni/prompt-engineering-book-2e/blob/main/notebooks/ch02_anatomy_of_a_request.ipynb) |
| **Part II** | **Core Technique** | |
| 3 | Writing Clear Instructions | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/youssefHosni/prompt-engineering-book-2e/blob/main/notebooks/ch03_clear_instructions.ipynb) |
| 4 | Giving the Model Room to Think | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/youssefHosni/prompt-engineering-book-2e/blob/main/notebooks/ch04_room_to_think.ipynb) |
| 5 | Patterns and Anti-Patterns | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/youssefHosni/prompt-engineering-book-2e/blob/main/notebooks/ch05_patterns.ipynb) |
| 6 | Grounding, Hallucination, and Retrieval | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/youssefHosni/prompt-engineering-book-2e/blob/main/notebooks/ch06_grounding.ipynb) |
| **Part III** | **Applying It** | |
| 7 | The Task Playbook | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/youssefHosni/prompt-engineering-book-2e/blob/main/notebooks/ch07_task_playbook.ipynb) |
| 8 | Structured Outputs and Tool Use | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/youssefHosni/prompt-engineering-book-2e/blob/main/notebooks/ch08_structured_outputs.ipynb) |
| 9 | From Chains to Agents | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/youssefHosni/prompt-engineering-book-2e/blob/main/notebooks/ch09_agents.ipynb) |
| **Part IV** | **Skills and Loops** | |
| 10-12 | Skills, and Loops That Run Without You | [a directory to copy](ch10_12_skills_and_loops/) |
| 13 | Operating a Loop | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/youssefHosni/prompt-engineering-book-2e/blob/main/notebooks/ch13_loops_operating.ipynb) |
| **Part V** | **Production** | |
| 14 | Evaluating LLM Applications | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/youssefHosni/prompt-engineering-book-2e/blob/main/notebooks/ch14_evaluation.ipynb) |
| 15 | Security, Cost, and Latency | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/youssefHosni/prompt-engineering-book-2e/blob/main/notebooks/ch15_security_cost.ipynb) |
| 16 | Building an End-to-End System | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/youssefHosni/prompt-engineering-book-2e/blob/main/notebooks/ch16_end_to_end.ipynb) |

Chapters 10 to 12 are about files and directories rather than API calls, so they
ship as a tree to copy rather than a notebook. See
[`ch10_12_skills_and_loops/README.md`](ch10_12_skills_and_loops/README.md).

Appendix B (fine-tuning) needs a GPU: `appendix_b_finetuning.ipynb`. Nothing
else in the book depends on it.

### Notebooks are generated, not edited

The `.py` files beside the notebooks are the source of truth; the notebooks are
built from them with jupytext:

```bash
python build_notebooks.py              # regenerate
python build_notebooks.py --execute    # and run them, embedding output
```

Edit the `.py`, never the `.ipynb`. That way the two cannot drift, which is the
same discipline `check-repo.py` enforces between the book and this repository.

## Tests

```bash
python test_offline.py
```

No key needed. It tests the *checkers* — the validators and scorers — rather
than the model, which is the part most worth testing: Chapter 13 opens with a
verification step that returned an empty string on every call while the scoring
code read it as a pass.

## Shared code

- `peb/client.py` — the `ask()` wrapper printed in Appendix A, which fails loudly
  on the two silent failures from §2.3 rather than returning an empty string.
- `peb/fixtures.py` — the Nordic 400 review and the order record. Six chapters
  work on this one input, so it lives in one place.

## What `outputs/` is, and is not

`outputs/ch07.txt` is what the book printed, captured from the run that produced
the numbers in the text. Re-running `ch07_task_playbook.py` will **not**
reproduce it character for character, and it is not supposed to. Chapter 3 §3.1
is built on exactly that variation, and Chapter 14 puts confidence intervals
around it.

What should reproduce is the *finding*: the direction of the effect, the rough
spread, and which checks fail. If yours disagrees about that, something has
changed worth knowing about — model versions move, and §14.6 is about noticing.

## A note on the code you will read

The scripts check their own results in code rather than by asking the model
whether it did well. That is Chapter 13's argument and it applies to the book's
own instrument: four of the experiments here were rewritten after the *measuring
code* turned out to be broken rather than the model. Those corrections are in
the text, and the fixed versions are what you are running.
