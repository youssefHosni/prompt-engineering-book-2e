---
name: release-notes
description: >
  Draft release notes from merged pull requests. Use when asked for release
  notes, a changelog, or a summary of what shipped in a version. Do not use
  for individual commit messages, incident write-ups, or roadmap updates.
---

## Steps

1. Run `scripts/merged_since.py <last-tag>` to list merged pull requests.
2. Group them into Added, Changed, Fixed. Discard anything labelled
   `internal` or `chore`.
3. Read `references/house-style.md` before writing a word.
4. Draft one line per item, present tense, no marketing adjectives.
5. STOP. Show the draft and ask before writing to a file.
6. On approval, write to `CHANGELOG.md` under a new version heading.

## Rules

- Never invent a change that is not in the PR list.
- If a PR title is unclear, list it under `Needs description` rather than
  guessing what it did.
- Never edit an existing version heading. Append only.
- If there are no merged PRs, say so and stop. Do not produce an empty
  section.
