"""The §3.1 word counts, as published.

These five-run batches are the chapter's opening evidence and they were living
in exactly one machine-readable place in the project: the \\foreach loops of
figures/src/fig-03-1.tex. A dataset whose only home is a drawing drifts
silently from the prose the moment either is edited, which is the most likely
origin of the 263-296 / 228-280 discrepancy the review found between §3.1 and
§3.7's Pass 1.

They are recorded here so the figure is no longer the source of truth, and
build/check-repo.py now asserts that the figure agrees with this file.

Measured August 2026. The original per-run replies were not kept, so these are
the counts, not the texts.
"""

VAGUE_WORD_COUNTS = [267, 278, 263, 266, 296]
SPECIFIC_WORD_COUNTS = [43, 53, 47, 52, 48]

assert len(VAGUE_WORD_COUNTS) == len(SPECIFIC_WORD_COUNTS) == 5
assert (min(VAGUE_WORD_COUNTS), max(VAGUE_WORD_COUNTS)) == (263, 296)
assert (min(SPECIFIC_WORD_COUNTS), max(SPECIFIC_WORD_COUNTS)) == (43, 53)
