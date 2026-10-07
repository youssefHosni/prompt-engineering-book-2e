#!/usr/bin/env bash
# Re-run the chapter scripts and record their output.
#
# The key is read by python-dotenv from the file PEB_ENV_FILE points at. It is
# never printed, never copied into this repo, and never passed on a command line.
#
#   ./capture.sh              every chapter
#   ./capture.sh ch13 ch14    only these
#
set -uo pipefail
cd "$(dirname "$0")"

# Make the repo root importable even without `pip install -e .`, so the
# scripts in src/ can find the peb package beside them. V-1.
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

: "${PEB_ENV_FILE:=../../../Prompt-Engineering-for-Instruction-Tuned-LLM-main/.env}"
export PEB_ENV_FILE

if [ ! -f "$PEB_ENV_FILE" ]; then
  echo "no key file at $PEB_ENV_FILE — set PEB_ENV_FILE to point at one" >&2
  exit 1
fi

# Notebook mode: regenerate the .ipynb files and execute them, embedding real
# output. Runs through this script so it inherits PEB_ENV_FILE like everything
# else -- one entry point, one place the key path is configured.
if [ "${1:-}" = "--notebooks" ]; then
  shift
  echo "building notebooks (executing; this costs API calls)"
  python3 -u build_notebooks.py --execute "$@" || exit $?
  exec python3 check_notebooks.py
fi

mkdir -p outputs/live outputs/live/_prev

# Every call is logged: script, model, date, tokens. The book asks each result to
# state its model and sample size; this is where that comes from.
: "${PEB_RUN_LOG:=outputs/run-log.jsonl}"
export PEB_RUN_LOG

scripts=()
if [ $# -gt 0 ]; then
  for a in "$@"; do scripts+=("$(ls src/"${a}"*.py 2>/dev/null | head -1)"); done
else
  scripts=(src/ch*.py)
fi

fail=0
for s in "${scripts[@]}"; do
  [ -f "$s" ] || { echo "skip: no script for that name" >&2; continue; }
  out="outputs/live/$(basename "${s%.py}").txt"
  # Keep the previous capture. A failed run writes a stack trace over the file,
  # and these are the only record of what the last run produced.
  [ -f "$out" ] && cp "$out" "outputs/live/_prev/$(basename "$out")"
  printf '%-34s ' "$s"
  if python3 -u "$s" > "$out" 2>&1; then
    echo "ok   -> $out"
  else
    echo "FAIL -> $out"
    tail -3 "$out" | sed 's/^/     /'
    fail=$((fail + 1))
  fi
done

echo
echo "$fail script(s) failed. Live output in outputs/live/ — the book's own"
echo "recorded runs stay untouched in outputs/, so you can compare."
exit $fail
