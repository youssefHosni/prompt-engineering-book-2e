---
name: weekly-report
description: >
  Draft the weekly team report from the issue tracker and the previous
  week's report. Use when asked for the weekly report, a status update or a
  team summary. Do not use for incident write-ups, release notes or a
  one-off project update.
---

Turning a week of tracker activity into a report someone will read.

## Steps

1. Read last week's report in `reports/` and note every item under Carried over.
2. Run `scripts/closed_since.py <last-monday>` for issues closed in the period.
3. Run `scripts/opened_since.py <last-monday>` for issues opened in the period.
4. Discard anything labelled `chore`, `dependencies` or `flaky-test`.
5. Group the remainder into Shipped, In progress, and Blocked.
6. For each Shipped item, find the pull request that closed it.
7. Record the PR number beside the item; a claim with no PR is not Shipped.
8. For each In progress item, check the last comment date.
9. Anything untouched for more than ten days moves to Stalled, not In progress.
10. For each Blocked item, name what it is blocked on and who owns that.
11. A blocker with no owner is the report's most important line. Say so.
12. Compare this week's Shipped count with the previous four weeks.
13. Do not editorialise about the trend. State the five numbers.
14. Read `references/house-style.md` before writing any prose.
15. Draft the Shipped section: one line per item, present tense, no adjectives.
16. Draft the In progress section: one line per item, with the expected close date.
17. Where no close date exists, write `no date` rather than estimating one.
18. Draft the Blocked section: item, blocker, owner, days blocked.
19. Draft the Stalled section only if it is non-empty.
20. Write the summary paragraph last, after the sections exist.
21. The summary is three sentences: what shipped, what is at risk, what is needed.
22. Do not put anything in the summary that is not in a section below it.
23. Check every person named is spelled as they spell it in the tracker.
24. Check every issue number resolves; a wrong number is worse than none.
25. Convert all dates to ISO format.
26. Remove every instance of the banned words in `references/house-style.md`.
27. Count the words. Over 400 means the sections are carrying commentary.
28. Re-read the Blocked section and ask whether a reader could act on each line.
29. If a blocker has been present three weeks running, flag it in the summary.
30. Check the Carried over items from step 1 all appear somewhere.
31. Anything that silently disappeared between reports is a defect; list it.
32. Add the Carried over section for next week.
33. STOP. Show the draft and ask before writing to a file.
34. On approval, write to `reports/<YYYY-MM-DD>.md`.
35. Never overwrite an existing report file.
36. Update `reports/index.md` with the new entry.
37. Post the summary paragraph only, with a link, to the team channel.
38. Record in `PROGRESS.md` which issues were discarded at step 4 and why.
39. If the tracker was unreachable, write nothing and report the failure.
40. Do not produce a report from a partial issue list.

## Rules

- Never invent an issue number, a date or an owner.
- Never report an item as Shipped without a merged pull request.
- Never estimate a close date the tracker does not contain.
- If the tracker query fails, stop. A partial report is worse than none.
- Never edit a previous week's report. Append a correction to this week's.
- If two issues describe the same work, report it once and note the duplicate.
