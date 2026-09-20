#!/usr/bin/env python3
"""
One run of the whole workforce. This is what GitHub fires four times a day.

    python3 agents/run_all.py            normal run
    python3 agents/run_all.py --build    also rebuild the site

Seventeen goal agents report. The Master Agent weighs them. Mechanical changes
publish themselves. Judgment waits in the War Room for a named human.
"""
import argparse, json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from core import GoalAgent, SOURCES, TODAY, NOW, log   # noqa: E402
from master import MasterAgent                          # noqa: E402

# Which source pair each goal agent owns. One Indian, one international.
ASSIGNMENT = {
    1:  ("mospi_nif", "un_sdg"),      2:  ("niti_sdg",  "un_sdg"),
    3:  ("mospi_nif", "who_unicef"),  4:  ("niti_sdg",  "un_sdg"),
    5:  ("mospi_nif", "un_sdg"),      6:  ("niti_sdg",  "un_sdg"),
    7:  ("mospi_nif", "un_sdg"),      8:  ("mospi_nif", "un_sdg"),
    9:  ("mospi_nif", "un_sdg"),      10: ("niti_sdg",  "un_sdg"),
    11: ("niti_sdg",  "un_sdg"),      12: ("niti_sdg",  "sdr"),
    13: ("niti_sdg",  "un_sdg"),      14: ("niti_sdg",  "un_sdg"),
    15: ("niti_sdg",  "un_sdg"),      16: ("niti_sdg",  "un_sdg"),
    17: ("niti_sdg",  "un_sdg"),
}


def load():
    goals = json.loads((ROOT / "data" / "goals.json").read_text(encoding="utf-8"))
    site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    return goals, site


def save(goals, site):
    (ROOT / "data" / "goals.json").write_text(json.dumps(goals, indent=1), encoding="utf-8")
    (ROOT / "data" / "site.json").write_text(json.dumps(site, indent=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true", help="rebuild the site after the run")
    args = ap.parse_args()

    goals, site = load()
    by_n = {g["n"]: g for g in goals}

    print(f"\n{'='*66}\nTRANQATHMA workforce, run of {TODAY}\n{'='*66}\n")

    reports = []
    for n in range(1, 18):
        ind_src, world_src = ASSIGNMENT[n]
        agent = GoalAgent(n, by_n[n]["title"], ind_src, world_src)
        reports.append(agent.run(by_n[n]))

    print()
    master = MasterAgent()
    verdict = master.weigh(reports, goals, site)

    # Class A has already been written into the goal records by the agents.
    # Class B goes to the queue and waits.
    site["warroom"] = verdict["queue"]
    site["compiled"] = TODAY
    site["last_run"] = NOW
    save(goals, site)

    changed = [r for r in reports if r["changed"]]
    blocked = [r for r in reports if r["verified"] is False]
    breaks = [r for r in reports if r["break"]]

    print(f"\n{'-'*66}")
    log("room", f"{len(reports)} agents reported")
    log("room", f"{len(changed)} sources moved, {len(blocked)} blocked by the checker")
    log("room", f"{len(breaks)} source breaks")
    log("room", f"{len(verdict['queue'])} proposals awaiting approval in the War Room")
    log("room", "nothing editorial has been published. Approval is required.")

    if args.build:
        print()
        subprocess.run([sys.executable, str(ROOT / "build" / "generate.py")], check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
