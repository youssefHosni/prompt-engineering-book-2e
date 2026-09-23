# House style for release notes

Level 3 material: only read at step 3, and never paid for before that.

## Tense and person

Present tense, describing what the software now does. Not what the team did.

- Yes: "Exports include the order reference."
- No:  "We added the order reference to exports."

## Length

One line per item. If an item needs two lines, it is two items.

## Banned words

`seamless`, `robust`, `powerful`, `simply`, `just`, `blazing`, `revolutionary`,
`delighted to announce`. If a line needs one of these to sound like it matters,
the line does not describe a change that matters.

## Grouping

Three groups only: Added, Changed, Fixed. Anything that fits none of them is
almost always `internal` and should have been discarded at step 2.

## Breaking changes

A breaking change goes first, under its own `### Breaking` heading, with the
migration in the same line. Never bury one in Changed.
