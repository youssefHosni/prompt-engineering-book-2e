# Loop Progress

The loop edits this file. You read it.

## Current State
- Status: healthy
- Main objective: a daily PR digest a human can skim in 30 seconds
- Current focus: routine runs; no open migration
- Last updated: 2026-08-24

## Last Run
- Date: 2026-08-24
- Trigger: manual (run 6 of the hand-run period; not yet scheduled)
- Summary: 9 merged PRs, 2 discarded as `chore`, 7 written to the digest
- Output produced: outputs/digest-2026-08-24.md

## Open Items
- PR #4412 has no description. Listed under Needs attention for the third run
  running; the author is on leave until the 1st.

## Blockers
- None.

## Needs Human Review
- The `Needs attention` section has grown for three consecutive runs. If that
  continues, the discard rule at step 4 is probably too narrow.

## Next Run Should
- Use tag `v4.2.0` as the base, not `v4.1.1`.
- Leave PR #4412 where it is. Do not attempt to infer its contents.

## Decisions Made
- 2026-08-19: one file per day rather than one rolling file. A rolling file
  made every run an edit of previous output, and edits are where loops corrupt
  their own history.
- 2026-08-21: `chore` joins `internal` on the discard list.

## Do Not Repeat
- 2026-08-20: rewrote the previous day's digest because the PR list overlapped
  at the tag boundary. The range is exclusive of the base tag. Fixed in
  INSTRUCTIONS step 2, but the instinct to "tidy up" yesterday is the thing to
  resist.
- 2026-08-22: produced an empty digest with three empty headings on a day with
  no merges. Step 3 exists because of this.
