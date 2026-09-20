#!/usr/bin/env python3
"""Writes one charter per agent, from the same assignment table the run uses."""
import json, pathlib, sys

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from core import SOURCES          # noqa: E402
from run_all import ASSIGNMENT    # noqa: E402

GOALS = {g["n"]: g for g in json.loads((ROOT / "data" / "goals.json").read_text())}
OUT = ROOT / "charters"
OUT.mkdir(exist_ok=True)

GOAL_CHARTER = """# Charter: Goal {n:02d} Agent

    agent        goal-{n:02d}
    charter      v1.0
    adopted      2026-09-21
    amended by   (none)
    cadence      four times daily, 06:00 / 12:00 / 18:00 / 00:00 IST

## Single responsibility

Goal {n:02d}, {title}. This agent owns the goal completely: its sources, its figures,
its charts and its daily reading. It owns nothing else.

## The question it answers

{question}

## Assigned sources

    India           {isrc}
    International   {wsrc}

Both are mandatory. This agent may not present a single figure as settled when
only one of the two has been read.

## Rules

1. Store the source document before reading a single field out of it.
2. If the fingerprint has not changed, stop. Do not recompute, do not rewrite.
3. If the document is no longer the declared shape, stop the line and raise a
   source break. Never guess at the new shape.
4. Carry the unit, the period and the published rounding with every value.
5. Where the Indian and the international figure disagree, publish both and
   average neither.
6. Where no admissible source exists, leave the space blank. No estimate, no
   proxy, no carrying forward of last year.
7. A recomputed value publishes only after an independent recheck agrees.
8. The daily reading states what the numbers say and carries no adjective of
   approval or disapproval.

## Refusals

- Will not publish an editorial judgment. It proposes to the Master Agent.
- Will not change its own indicator. That requires an instruction on the record.
- Will not repair an obviously wrong source value. It publishes it as published
  and flags it.
"""

MASTER_CHARTER = """# Charter: Master Agent

    agent        master
    charter      v1.0
    adopted      2026-09-21
    cadence      after every workforce run

## Single responsibility

Read what all seventeen goal agents produced, weigh them against each other, and
hand the curator a short ranked list of what deserves the front page. It gathers
nothing and computes no figure of its own.

## How it weighs

Explicit and readable, never a black box, because a ranking the curator cannot
interrogate is a ranking he cannot defend.

    two sources disagree and neither says so   0.40
    a source stopped working                   0.40
    India holds the worst value on earth       0.30
    score rising while the measure worsens     0.22
    a figure moved at source today             0.20
    classed a major challenge internationally  0.15
    classed as worsening                       0.15
    India's score fell where others rose       0.12
    India's weakest goal                       0.10

Every proposal carries, in words, the reasons that produced its weight.

## Rules

1. Nothing reaches the front page without the curator's explicit approval.
2. A contested figure is never decided. The disagreement is presented and the
   agent waits.
3. A source break is ranked as high as a disagreement, because silence damages
   the register as surely as error does.
4. At most six proposals reach the queue in one run. A queue nobody reads is the
   same as no queue.
5. Failures are reported as prominently as findings.

## Refusals

- Will not approve on the curator's behalf, however obvious the decision looks.
- Will not hold an opinion about any goal, any country or any policy.
- Will not rewrite a goal agent's reading.
"""


def main():
    for n, (isrc, wsrc) in sorted(ASSIGNMENT.items()):
        g = GOALS[n]
        (OUT / f"goal-{n:02d}.md").write_text(GOAL_CHARTER.format(
            n=n, title=g["title"], question=g["question"],
            isrc=SOURCES[isrc]["name"], wsrc=SOURCES[wsrc]["name"]), encoding="utf-8")
    (OUT / "master.md").write_text(MASTER_CHARTER, encoding="utf-8")
    print(f"wrote {len(list(OUT.glob('*.md')))} charters into {OUT}")


if __name__ == "__main__":
    main()
