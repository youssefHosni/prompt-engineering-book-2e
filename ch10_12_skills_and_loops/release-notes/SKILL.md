---
name: release-notes
description: >
  Draft release notes from merged pull requests. Use when asked for release
  notes, a changelog, or a summary of what shipped in a version. Do not use
  for individual commit messages, incident write-ups, or roadmap updates.
---

## Steps

1. Run `scripts/merged_since.py <last-tag>` (requires the `gh` CLI,
   authenticated) to list merged pull requests.
2. Group them into Added, Changed, Fixed. Discard anything labelled
   `internal` or `chore`.
3. Read `references/house-style.md` before writing a word.
4. Draft one line per item, present tense, no marketing adjectives.
5. STOP. Show the draft and ask before writing to a file.
6. On approval, write to `CHANGELOG.md` under a new version heading.

## Rules

- Never invent a change that is not in the PR list. An invented entry is
  indistinguishable from a real one once it is published.
- If a PR title is unclear, list it under `Needs description` rather than
  guessing what it did. A guess that reads well is worse than a gap.
- Never edit an existing version heading. Append only, because a published
  changelog entry is a reference other people have linked to.
- If `merged_since.py` exits with an error rather than a list, stop and report
  the error. Do not continue to step 2: grouping a list you never received is
  how a loop invents a release.
- If there are no merged PRs, say so and stop. An empty section implies a
  release happened.

## Done means

`CHANGELOG.md` has a new version heading, every line under it traces to a PR
number from step 1, no line contains a word banned by
`references/house-style.md`, and no previous heading was touched. Check these,
not your impression of the output.

<!-- last reviewed: 2026-10-09, by the author.
     §11.10: a skill is a document with an owner and a review cadence. This
     line is the cadence. An approved release note belongs in
     references/past-releases.md as a worked example -- a real one beats an
     invented one. -->
