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

: "${PEB_ENV_FILE:=../../../Prompt-Engineering-for-Instruction-Tuned-LLM-main/.env}"
export PEB_ENV_FILE

if [ ! -f "$PEB_ENV_FILE" ]; then
  echo "no key file at $PEB_ENV_FILE — set PEB_ENV_FILE to point at one" >&2
  exit 1
fi

mkdir -p outputs/live
scripts=()
if [ $# -gt 0 ]; then
  for a in "$@"; do scripts+=("$(ls "${a}"*.py 2>/dev/null | head -1)"); done
else
  scripts=(ch*.py)
fi

fail=0
for s in "${scripts[@]}"; do
  [ -f "$s" ] || { echo "skip: no script for that name" >&2; continue; }
  out="outputs/live/${s%.py}.txt"
  printf '%-34s ' "$s"
  if python3 "$s" > "$out" 2>&1; then
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
