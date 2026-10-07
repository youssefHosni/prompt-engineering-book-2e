#!/usr/bin/env python3
"""Summarise outputs/run-log.jsonl: calls, tokens, and estimated spend.

Prices are USD per million tokens, as published for the models the book uses.
They are estimates for budgeting, not an invoice -- check your own dashboard
before quoting a figure.
"""
import collections, json, pathlib, sys

PRICES = {                      # (input, output) USD per 1M tokens
    "claude-opus-5":    (15.0, 75.0),
    "claude-sonnet-5":  (3.0, 15.0),
    "claude-haiku-4.5": (1.0, 5.0),
    "gpt-5.6-terra":    (1.25, 10.0),
    "gemini-3.7-flash": (0.30, 2.50),
}
DEFAULT = (15.0, 75.0)          # assume the dearest if unknown

log = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/run-log.jsonl")
if not log.exists():
    sys.exit(f"no log at {log}")

rows = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
by = collections.defaultdict(lambda: {"calls": 0, "in": 0, "out": 0})
for r in rows:
    k = (r["script"], r["model"])
    by[k]["calls"] += 1
    by[k]["in"] += r["input_tokens"]
    by[k]["out"] += r["output_tokens"]

total = 0.0
print(f"{'script':<32} {'model':<18} {'calls':>5} {'in':>8} {'out':>8} {'USD':>7}")
for (script, model), v in sorted(by.items()):
    pin, pout = PRICES.get(model, DEFAULT)
    cost = v["in"] / 1e6 * pin + v["out"] / 1e6 * pout
    total += cost
    print(f"{script:<32} {model:<18} {v['calls']:>5} {v['in']:>8} {v['out']:>8} {cost:>7.3f}")

dates = sorted({r["ts"][:10] for r in rows})
print(f"\n{len(rows)} calls on {', '.join(dates)}   estimated USD {total:.2f}")
