#!/usr/bin/env python3
"""List merged pull requests since a tag.

Level 3: the skill body names this script, but its contents are never loaded
into the context. The model runs it and reads the output.

Deterministic work belongs in code. Chapter 10 §10.2 is the argument; this is
the argument as a file.
"""
import json
import subprocess
import sys


def merged_since(tag):
    """Merged PRs since `tag`, newest first, via the gh CLI."""
    rng = subprocess.run(
        ["git", "log", f"{tag}..HEAD", "--merges", "--pretty=%H"],
        capture_output=True, text=True, check=True).stdout.split()
    if not rng:
        return []

    out = subprocess.run(
        ["gh", "pr", "list", "--state", "merged", "--limit", "200",
         "--json", "number,title,labels,mergeCommit"],
        capture_output=True, text=True, check=True).stdout
    shas = set(rng)
    prs = []
    for pr in json.loads(out):
        commit = (pr.get("mergeCommit") or {}).get("oid")
        if commit in shas:
            prs.append({
                "number": pr["number"],
                "title": pr["title"],
                "labels": [l["name"] for l in pr["labels"]],
            })
    return prs


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: merged_since.py <last-tag>")
    for pr in merged_since(sys.argv[1]):
        labels = ",".join(pr["labels"]) or "-"
        print(f"#{pr['number']}\t{labels}\t{pr['title']}")
