# Daily digest loop

You edit this file. The loop does not.

## Task

Summarise yesterday's merged pull requests into `outputs/digest-<YYYY-MM-DD>.md`,
with sections for Added, Fixed, and Needs attention.

## Every run

1. Read `PROGRESS.md` first. Everything under **Do Not Repeat** is binding.
2. Run `../release-notes/scripts/merged_since.py <last-tag>` for the PR list.
3. If the list is empty, write nothing. Update `PROGRESS.md` to say the run was
   a no-op and stop. An empty digest is worse than no digest.
4. Group items into Added, Fixed, Needs attention. Anything labelled `internal`
   or `chore` is discarded.
5. Write `outputs/digest-<YYYY-MM-DD>.md` with exactly those three headings,
   present tense, one line per item.
6. Update `PROGRESS.md`: Last Run, Open Items, and anything that belongs under
   Needs Human Review.

## Rules

- Never edit a digest from a previous day. Append-only, one file per day.
- Never invent a change that is not in the PR list.
- If a PR title is unclear, put it under Needs attention. Do not guess.
- Stop after 3 failed attempts at any step and record the failure under
  **Blockers**. Do not retry silently — §12.3.
- You may write to `outputs/` and `PROGRESS.md`. Nothing else.

## Done means

`outputs/digest-<today>.md` exists, has all three headings, contains no banned
word from `../release-notes/references/house-style.md`, and every line traces to
a PR number in the list. Check these, not your impression of the output.
