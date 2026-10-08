#!/usr/bin/env python3
"""Generate the .ipynb notebooks from the chapter scripts.

The scripts are the source of truth. Notebooks are derived, never hand-edited,
so the two cannot drift -- which is the failure this repository already has one
validator guarding against on the book side.

    python build_notebooks.py            # regenerate all
    python build_notebooks.py --execute  # and run them, embedding real output

Executing costs API calls. Without --execute the notebooks ship with cells
ready to run and no stored output.
"""
import argparse
import pathlib
import sys

import jupytext
import nbformat

REPO = "youssefHosni/prompt-engineering-book-2e"
HERE = pathlib.Path(__file__).parent
SRC = HERE / "src"          # the .py sources
OUT = HERE / "notebooks"   # the generated .ipynb


def badge(name):
    url = f"https://colab.research.google.com/github/{REPO}/blob/main/notebooks/{name}"
    return (f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]"
            f"({url})")


SETUP_CELL = """# Colab only: fetch the shared helpers and install the SDKs.
# Running locally? Skip this cell -- you already have them.
import os, sys
if "google.colab" in sys.modules:
    !pip -q install anthropic openai python-dotenv
    !git clone -q https://github.com/{repo} /content/peb-book
    sys.path.insert(0, "/content/peb-book")
    from getpass import getpass
    os.environ["ANTHROPIC_API_KEY"] = getpass("ANTHROPIC_API_KEY: ")
"""


def has_output(path):
    """Does an existing notebook carry executed output worth protecting?"""
    if not path.exists():
        return False
    try:
        nb = nbformat.read(path, as_version=4)
    except Exception:
        return False
    return any(c.cell_type == "code" and c.get("outputs") for c in nb.cells)


def error_count(path):
    """How many cells in an existing notebook ended in an exception."""
    if not path.exists():
        return 0
    try:
        nb = nbformat.read(path, as_version=4)
    except Exception:
        return 0
    return sum(1 for c in nb.cells for o in c.get("outputs", [])
               if o.get("output_type") == "error")


def build(script, execute=False):
    nb = jupytext.read(script)
    name = script.stem + ".ipynb"

    # Regenerating without --execute produces a notebook with no output. If one
    # with output already exists, that would silently destroy it -- which is
    # exactly what happened once, to all fourteen at the same time. Refuse.
    target = OUT / name
    if not execute and has_output(target):
        raise SystemExit(
            f"{name} already has executed output.\n"
            f"Regenerating without --execute would discard it.\n"
            f"Use --execute to re-run, or delete {target} first if you really "
            f"want an empty one.")

    # Badge goes above the title, then the Colab setup cell.
    nb.cells.insert(0, nbformat.v4.new_markdown_cell(badge(name)))
    nb.cells.insert(2, nbformat.v4.new_code_cell(SETUP_CELL.format(repo=REPO)))

    nb.metadata.setdefault("kernelspec", {
        "display_name": "Python 3", "language": "python", "name": "python3"})

    if execute:
        from nbclient import NotebookClient
        client = NotebookClient(nb, timeout=900, kernel_name="python3",
                               resources={"metadata": {"path": str(HERE)}},
                               allow_errors=True)
        client.execute()

    # Executing without a key makes every API cell raise, and writing that over
    # a clean notebook destroys the output silently -- which is how this went
    # wrong once. Refuse to replace a notebook with a more broken one.
    if execute:
        new_errors = sum(1 for c in nb.cells for o in c.get("outputs", [])
                         if o.get("output_type") == "error")
        was = error_count(target)
        if new_errors > was:
            raise SystemExit(
                f"{name}: this run errored in {new_errors} cell(s), the existing "
                f"notebook in {was}. Refusing to overwrite a cleaner notebook.\n"
                f"Usually this means no key reached the kernel: run it through "
                f"./capture.sh --notebooks, which exports PEB_ENV_FILE.")

    OUT.mkdir(exist_ok=True)
    nbformat.write(nb, OUT / name)
    cells = len(nb.cells)
    return name, cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true",
                    help="run each notebook and embed its output (costs API calls)")
    ap.add_argument("only", nargs="*", help="name prefixes, e.g. ch03 ch14")
    args = ap.parse_args()

    scripts = sorted(SRC.glob("ch*.py")) + [SRC / "appendix_b_finetuning.py"]
    if args.only:
        scripts = [s for s in scripts if any(s.name.startswith(p) for p in args.only)]

    for s in scripts:
        if not s.exists():
            continue
        try:
            name, cells = build(s, args.execute)
            print(f"  {name:<40} {cells} cells")
        except Exception as e:
            print(f"  {s.name:<40} FAILED: {type(e).__name__}: {e}", file=sys.stderr)
            return 1
    print(f"\nnotebooks in {OUT.relative_to(HERE)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
