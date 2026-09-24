#!/usr/bin/env python3
"""Fail if any notebook has drifted from the source it was generated from.

`src/*.py` is the source of truth; `notebooks/*.ipynb` is generated from it by
build_notebooks.py. Nothing enforced that, and within hours of setting it up
ch04's script was fixed and its notebook was not -- so the published notebook
showed a null result where the chapter has its clearest finding.

This is the check that would have caught it. Run:

    python check_notebooks.py
"""
import pathlib
import sys

import jupytext

HERE = pathlib.Path(__file__).parent
SRC, OUT = HERE / "src", HERE / "notebooks"

# build_notebooks.py injects these two; they are not in the source by design.
INJECTED = ("colab-badge", "google.colab")


def normalise(text):
    """Compare content, ignoring the YAML header and blank-line churn."""
    if text.lstrip().startswith("# ---"):
        text = text.split("# ---", 2)[-1]
    return "\n".join(l.rstrip() for l in text.strip().split("\n") if l.strip())


def main():
    problems = []
    checked = 0

    for src in sorted(SRC.glob("*.py")):
        nbp = OUT / f"{src.stem}.ipynb"
        if not nbp.exists():
            problems.append(f"{src.name}: no notebook at {nbp.relative_to(HERE)}")
            continue

        nb = jupytext.read(nbp)
        nb.cells = [c for c in nb.cells
                    if not any(m in "".join(c.source) for m in INJECTED)]
        if normalise(jupytext.writes(nb, fmt="py:percent")) != normalise(src.read_text()):
            problems.append(f"{src.name}: notebook is out of date -- "
                            f"regenerate with `python build_notebooks.py --execute "
                            f"{src.stem.split('_')[0]}`")
        checked += 1

    # A notebook with no source is just as wrong: it cannot be regenerated.
    for nbp in sorted(OUT.glob("*.ipynb")):
        if not (SRC / f"{nbp.stem}.py").exists():
            problems.append(f"{nbp.name}: no source in src/")

    if problems:
        print(f"check-notebooks: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"check-notebooks: {checked} notebooks match their sources")
    return 0


if __name__ == "__main__":
    sys.exit(main())
