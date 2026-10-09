# Chapters 10–12 — skills and loops

These three chapters are about files and directories, not about API calls, so
this part of the repository is a tree to copy rather than a script to run.

```
ch10_12_skills_and_loops/
├── release-notes/          the complete skill from §11.5
│   ├── SKILL.md            level 1 frontmatter + level 2 body
│   ├── references/         level 3: read only when a step asks for it
│   └── scripts/            level 3: run, never loaded into context
└── loop/                   the minimum viable loop from §12.4
    ├── INSTRUCTIONS.md     you edit this
    ├── PROGRESS.md         the loop edits this
    └── outputs/            one file per run
```

## Trying the skill

Copy `release-notes/` into your skills directory — `.claude/skills/` for a
single project, or `~/.claude/skills/` to have it everywhere. §10.7 covers
which of those you want and why the answer is usually the project.

Then ask for release notes. You are testing one thing first: whether the
description fires on the right requests and stays quiet on the wrong ones.
§11.8 has the three-case test, and it costs less than building a harness.

## Trying the loop

Run it by hand. Six times, watching, before it goes anywhere near a schedule.
`PROGRESS.md` here is a real state file after six hand-runs, including the two
entries under **Do Not Repeat** that exist because those runs went wrong.

The separation matters more than anything else in the directory: instructions
you write, state the loop writes. §12.7 is the argument for keeping them in
different files, and the failure it prevents is a loop editing its own
instructions until they no longer say what you meant.

## A warning that applies to both

A skill you install from elsewhere is a dependency that runs with your
permissions and can read what you can read. Read `SKILL.md` and every script
before installing, exactly as you would read a build plugin. §11.9 is the
longer version.
