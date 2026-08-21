# Why this skill exists

Source: Kushal Chakrabarti, *Why Does CLAUDE.md Keep Growing? Catastrophic
Remembering in Agentic Coding*, [arXiv:2608.11095](https://arxiv.org/abs/2608.11095).

Read this only if you need the evidence. The protocol is in `SKILL.md`.

## What holds up

Across 1,867 public repos and 247,694 instruction lifetimes:

- Median instruction file ends at 39 instructions
- Mean count more than triples over the file's life (+226%)
- Net +4.9 instructions per commit
- Deletion hazard *falls* with age (log-hazard -0.032/commit)
- More authors make deletion even less likely
- ~77% of instruction deaths are wholesale rewrites; growth then resumes
  faster (4.1% → 4.9% per commit)

That slope is not staleness (stale rules should die more as they age) and
not only fragile content dying young. The instruction stays; the rationale
decays. The paper calls this **catastrophic remembering**.

Without the original why, a safe audit of which subset of instructions is
excess is exponential in prompt size. Recording the why at write time is
O(1).

## What the comments actually need

In the paper's inverted-IFEval worlds, comments that encode the failure, a
hypothesis, and the **outcome** halt growth. Comment-shaped noise does
nothing. A narrative with no outcomes is worse than no comment. Dropping
the recurrence count costs a large share of the pruning effect.

## What not to take from the paper

- The 99.3% excess-size cut is a lab number on 2–3 instruction covers. Real
  median files are ~39 instructions.
- The "up to 23.1%" instruction-following lift is seeded noise plus an
  LLM judge. Direction is plausible; the percentage is not a target.
- Do not auto-delete from recovered rationale. Their protocol emptied about
  1 prompt in 8, and the uncommented arm scored higher on those worlds.
  The author: keep a human in the deletion path; hold safety-relevant
  rules out of scope.
- Age is not "this rule is still true" and not "this rule is dead." The
  comment (or a test) tells which.
