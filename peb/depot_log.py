"""The 520-row depot log behind Chapters 2 and 9.

The original generated file was not kept. This rebuilds it deterministically to
the ground truth both chapters publish, which the book states was known exactly
*because* the document was generated (§2.8). The invariants are asserted at
import, so a log that does not match the published figures cannot be used by
accident.

Published ground truth:

    520 rows
     56 cement entries
  2,812 cement pallets
  2,891 pallets at Aberdeen, all products   (§9.3)

A note on provenance, since this book is about exactly that: this is a
reconstruction, not the original artefact. It reproduces every published
aggregate, but a model's answer on it will not be token-identical to a run
against the file used in 2026. Where a chapter reports a model's *wrong* answer
-- 55 and 2,782, say -- that figure belongs to the original run and is not
expected to reproduce here.
"""
import random

ROWS = 520
CEMENT_ENTRIES = 56
CEMENT_PALLETS = 2812
ABERDEEN_PALLETS = 2891

DEPOTS = ["Aberdeen", "Leeds", "Hull", "Oldham", "Bristol",
          "Cardiff", "Norwich", "Dundee"]
PRODUCTS = ["cement", "timber", "sand", "aggregate", "insulation", "plasterboard"]


def _build(seed=20260823):
    rng = random.Random(seed)

    # 56 cement rows whose pallets sum to exactly CEMENT_PALLETS.
    cement = [rng.randint(18, 82) for _ in range(CEMENT_ENTRIES)]
    while sum(cement) != CEMENT_PALLETS:
        i = rng.randrange(CEMENT_ENTRIES)
        step = 1 if sum(cement) < CEMENT_PALLETS else -1
        if 18 <= cement[i] + step <= 82:
            cement[i] += step

    rows = [{"depot": None, "pallets": p, "product": "cement"} for p in cement]
    rows += [{"depot": None, "pallets": rng.randint(12, 95),
              "product": rng.choice(PRODUCTS[1:])}
             for _ in range(ROWS - CEMENT_ENTRIES)]
    rng.shuffle(rows)
    for r in rows:
        r["depot"] = rng.choice(DEPOTS)

    # Force Aberdeen's all-product total, adjusting only NON-cement Aberdeen rows
    # so the cement invariants above are left alone.
    def aberdeen():
        return sum(r["pallets"] for r in rows if r["depot"] == "Aberdeen")

    spare = [r for r in rows if r["depot"] == "Aberdeen" and r["product"] != "cement"]
    while aberdeen() != ABERDEEN_PALLETS:
        delta = ABERDEEN_PALLETS - aberdeen()
        if delta > 0:
            # Move a non-cement row into Aberdeen, or raise one already there.
            cand = next((r for r in rows if r["depot"] != "Aberdeen"
                         and r["product"] != "cement" and r["pallets"] <= delta), None)
            if cand is None:
                r = spare[0]; r["pallets"] += delta
            else:
                cand["depot"] = "Aberdeen"; spare.append(cand)
        else:
            cand = next((r for r in spare if r["pallets"] <= -delta and len(spare) > 1), None)
            if cand is None:
                r = max(spare, key=lambda r: r["pallets"]); r["pallets"] += delta
            else:
                cand["depot"] = "Leeds"; spare.remove(cand)
    return rows


DEPOT_LOG = _build()

# The log is useless if it does not match what the chapters publish.
_cement = [r for r in DEPOT_LOG if r["product"] == "cement"]
assert len(DEPOT_LOG) == ROWS, len(DEPOT_LOG)
assert len(_cement) == CEMENT_ENTRIES, len(_cement)
assert sum(r["pallets"] for r in _cement) == CEMENT_PALLETS
assert sum(r["pallets"] for r in DEPOT_LOG if r["depot"] == "Aberdeen") == ABERDEEN_PALLETS


# §2.6 describes "a 520-line depot log, about 21,000 tokens" -- roughly 40 tokens
# a line, so each line is a full log entry rather than a triple. The extra fields
# carry no signal; they are there because the experiment is about length.
_DRIVERS = ["R. Okafor", "M. Pilcher", "S. Nawaz", "J. Attwood", "L. Brennan",
            "K. Osei", "T. Marchetti", "A. Dunlop", "P. Varga", "N. Achterberg"]
_STATUS = ["complete", "complete", "complete", "part-load", "held at gate"]
_BAYS = ["bay 1", "bay 2", "bay 3", "bay 4", "north dock", "south dock"]

# The needle for the lost-in-the-middle test at §2.6.
NEEDLE = "Entry X. The internal reference code for the Kirkwall depot is QX-7741."


def _line(i, r, rng):
    # Trimmed to land on the ~21,000 tokens §2.6 reports. Driver and bay were
    # dropped: they carried no signal and pushed the log 35% over the published
    # figure, which would have made §9.3's 21,226 unreproducible.
    return (f"Entry {i}. 2026-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}, "
            f"{r['depot']} depot, order KL-{rng.randint(100000, 999999)}, "
            f"{r['pallets']} pallets of {r['product']}, "
            f"unloaded {rng.randint(5,19):02d}:{rng.randint(0,59):02d}, "
            f"status {rng.choice(_STATUS)}.")


def as_text(rows=None, needle_at=None, seed=20260823):
    """The log as the model sees it: one full entry per line.

    `needle_at` is "start", "middle" or "end" for §2.6's position test. Omit it
    and no needle is inserted.
    """
    rows = DEPOT_LOG if rows is None else rows
    rng = random.Random(seed)
    lines = [_line(i + 1, r, rng) for i, r in enumerate(rows)]
    if needle_at:
        pos = {"start": 2, "middle": len(lines) // 2, "end": len(lines) - 2}[needle_at]
        lines.insert(pos, NEEDLE)
    return "\n".join(lines)


if __name__ == "__main__":
    print(f"rows            {len(DEPOT_LOG)}")
    print(f"cement entries  {len(_cement)}")
    print(f"cement pallets  {sum(r['pallets'] for r in _cement)}")
    print(f"Aberdeen total  {sum(r['pallets'] for r in DEPOT_LOG if r['depot'] == 'Aberdeen')}")
    print(f"all pallets     {sum(r['pallets'] for r in DEPOT_LOG)}")
    txt = as_text()
    print(f"chars as text   {len(txt)}")
    print(f"~tokens (chars/4) {len(txt) // 4}")
    print()
    print(as_text(DEPOT_LOG[:2]))
