---
name: incident-writeup
description: >
  Draft a blameless incident write-up from the incident channel and the
  monitoring timeline. Use when asked for a post-mortem, an incident report
  or an RCA. Do not use for release notes, a weekly report, or a
  customer-facing status page update.
---

The write-up is for the next person, not for the record.

## Steps

1. Collect the incident channel transcript in full.
2. Collect the alert that opened the incident and its timestamp.
3. Collect the deploy log for the six hours before the alert.
4. Collect the monitoring graphs for the affected service.
5. Establish detection time: when the alert fired, not when someone looked.
6. Establish start time: when the behaviour began, from the graphs.
7. The gap between start and detection is the most useful number here.
8. Establish mitigation time: when customer impact stopped.
9. Establish resolution time: when the underlying cause was removed.
10. Mitigation and resolution are different. Record both.
11. Build the timeline from timestamps, not from recollection.
12. Every timeline entry cites a message, an alert or a graph.
13. Mark any entry you could not source as `unsourced` and keep it.
14. Quantify customer impact: requests failed, customers affected, duration.
15. If impact cannot be quantified, say so rather than estimating.
16. Identify the trigger: the change or event that started it.
17. Identify the cause: the condition that made the trigger harmful.
18. A trigger is not a cause. A deploy that exposes a latent bug is a trigger.
19. Ask what made this hard to detect.
20. Ask what made this hard to diagnose.
21. Ask what made this hard to fix.
22. Those three questions produce better actions than asking what went wrong.
23. Name no individual anywhere in the document.
24. Replace every name with a role: the on-call engineer, the deployer.
25. Remove every instance of 'should have', 'failed to' and 'neglected'.
26. Describe what happened and what was known at the time.
27. List what went well. An incident with nothing good in it is badly written.
28. Draft actions: each with an owner, a due date and a tracker issue.
29. An action without an owner is a wish. Do not include it.
30. Separate actions that prevent recurrence from actions that reduce impact.
31. Mark each action as detection, mitigation or prevention.
32. If every action is prevention, the write-up has not thought about detection.
33. Check the timeline against the transcript one final time.
34. Read `references/writeup-template.md` and match its section order.
35. STOP. Circulate the draft to the responders before publishing.
36. Incorporate corrections to the timeline without argument.
37. On approval, publish to the incident register.
38. Link the write-up from every action's tracker issue.
39. Schedule the action review for thirty days out.
40. Never close an incident with open actions unowned.

## Rules

- Never name an individual. Roles only.
- Never use 'should have', 'failed to', or 'human error'.
- Never publish before the responders have seen the timeline.
- Never list an action without an owner and a due date.
- A trigger is not a cause; keep them in separate fields.
- If the timeline cannot be sourced, mark it unsourced rather than dropping it.
