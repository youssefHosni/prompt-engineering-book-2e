# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Chapter 10 — what progressive disclosure is worth
#
# §10.3 publishes three token counts and two ratios. The six skills it measured
# were never committed, so this re-measures the same three quantities against six
# skills that *are* in the repository, under `ch10_12_skills_and_loops/`.
#
# These are reconstructions. The procedures are real and each body carries
# forty-odd numbered steps and a rules block, as the chapter describes, but they
# are not the author's originals — so the absolute totals differ. The chapter
# already names the durable part: "The ratio is the durable part, and it comes
# from arithmetic rather than pricing."
#
# Token counts are measured, not estimated: each block is sent to the API and the
# reported `input_tokens` is read back.

# %%
import pathlib
import re

from peb import ask

SKILLS_DIR = pathlib.Path(__file__).parent.parent / "ch10_12_skills_and_loops"
METER = "claude-haiku-4.5"      # cheapest model; the tokeniser is what matters

skills = sorted(p for p in SKILLS_DIR.glob("*/SKILL.md"))
print(f"{len(skills)} skills found\n")


def tokens(text):
    """Real input-token count, read back from the API."""
    _, usage = ask(f"{text}\n\nReply with the single word OK.",
                   model=METER, max_tokens=20)
    return usage.input_tokens


OVERHEAD = tokens("")           # the wrapper itself, subtracted from each figure


def description_of(body):
    """Level 1: the frontmatter block, which is all that is always resident."""
    m = re.search(r"^---\n(.*?)\n---", body, re.S)
    return m.group(1) if m else ""


bodies = {p.parent.name: p.read_text() for p in skills}
descs = {n: description_of(b) for n, b in bodies.items()}

# %%
all_bodies = tokens("\n\n".join(bodies.values())) - OVERHEAD
all_descs = tokens("\n\n".join(descs.values())) - OVERHEAD
# Load a representative skill, not the shortest one. release-notes predates the
# other five and is a third their size; using it would flatter the ratio.
_median = sorted(bodies, key=lambda n: len(bodies[n]))[len(bodies) // 2]
one_body = tokens(bodies[_median]) - OVERHEAD
print(f"(the matched skill is {_median})")

print(f"{'six full skill bodies, always in the prompt':<46} {all_bodies:>7,} tokens")
print(f"{'six descriptions only':<46} {all_descs:>7,} tokens")
print(f"{'one body, loaded because it matched':<46} {one_body:>7,} tokens")

print(f"\npublished in §10.3: 14,068 / 215 / 2,394")

# %%
cheaper = all_bodies / all_descs
fired = all_bodies / (all_descs + one_body)
print(f"\ncarrying descriptions alone is {cheaper:.0f}x cheaper than carrying bodies")
print(f"  (§10.3 publishes 65x)")
print(f"on a request where a skill fires you pay {all_descs:,} + {one_body:,} = "
      f"{all_descs + one_body:,},")
print(f"  still {fired:.1f}x cheaper than always-loaded  (§10.3 publishes 5.4x)")

# %% [markdown]
# ### Why the ratios hold and the absolutes do not
#
# The first ratio is roughly `six bodies / six descriptions`, so it is set by how
# much longer a procedure is than its label — a property of writing skills, not of
# these six. The second is roughly `six bodies / one body`, which tends to six and
# is dragged down only by the descriptions you still carry.
#
# That is why the chapter is right to call the ratio durable. It is also why a
# reconstruction can check the argument without reproducing the author's figures.

# %%
per_body = all_bodies / len(bodies)
per_desc = all_descs / len(descs)
print(f"mean body        {per_body:>7,.0f} tokens   (§10.3 implies ~2,345)")
print(f"mean description {per_desc:>7,.0f} tokens   (§10.3 implies ~36)")
print(f"body : description = {per_body / per_desc:.0f} : 1")

print()
print("The two ratios are NOT equally durable, and the chapter treats them as if")
print("they were.")
print()
print(f"  descriptions-vs-bodies ({cheaper:.0f}x here, 65x published) is just the")
print("  body:description length ratio. That is a property of how long your")
print("  procedures are and how terse your descriptions are -- it is a fact about")
print("  a particular set of skills, not about progressive disclosure.")
print()
print(f"  always-loaded-vs-fired ({fired:.1f}x here, 5.4x published) is bounded by the")
print(f"  NUMBER of skills: it tends to {len(bodies)}x as bodies grow, from either side,")
print("  because you load one body instead of six. That one is structural, and it")
print("  is the ratio worth quoting.")
