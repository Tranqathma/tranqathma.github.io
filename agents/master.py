#!/usr/bin/env python3
"""
The Master Agent.

It gathers nothing. It reads what all seventeen goal agents produced, weighs
them against each other, and hands the curator a short ranked list of what
deserves the front page. It never publishes, and it never decides a contested
figure. It presents the disagreement and waits.

The weighing is deliberately explicit and readable rather than a black box,
because a ranking the curator cannot interrogate is a ranking he cannot defend.
"""
from core import log, NOW

# What raises a goal's claim on the front page, and by how much.
WEIGHTS = {
    "source_disagreement": 0.40,   # two competent bodies differ and neither says so
    "worst_in_world":      0.30,   # India holds the worst recorded value anywhere
    "direction_reversed":  0.22,   # score rising while the underlying figure worsens
    "value_moved":         0.20,   # a number actually changed at source today
    "major_challenge":     0.15,   # classed a major challenge internationally
    "declining":           0.15,   # classed as worsening
    "only_goal_falling":   0.12,   # India's score fell where others rose
    "lowest_score":        0.10,   # India's weakest goal
    "source_break":        0.40,   # a source stopped working, needs a decision
}


class MasterAgent:
    name = "Master Agent"

    def weigh(self, reports, goals, site):
        by_n = {g["n"]: g for g in goals}
        scored = []

        for r in reports:
            g = by_n[r["goal"]]
            reasons, weight = [], 0.0

            def add(key, text):
                nonlocal weight
                weight += WEIGHTS[key]
                reasons.append(text)

            if r["break"]:
                add("source_break", f"source break, {r['break']}")

            ind = g.get("india_ind") or {}
            if ind.get("dispute"):
                add("source_disagreement",
                    f"two admissible sources differ by {ind['dispute']['gap']} "
                    f"and neither discloses the other")
            if ind.get("note") and "highest" in str(ind.get("note")).lower():
                add("worst_in_world", "India holds the worst value recorded anywhere")
            if g["status"] == "major challenge":
                add("major_challenge", "classed a major challenge internationally")
            if g["status"] == "declining":
                add("declining", "classed as worsening")
            if r["changed"]:
                add("value_moved", "a figure moved at source in this run")

            ia = g["india"]
            if ia.get("prev") and ia.get("score") and ia["score"] < ia["prev"]:
                add("only_goal_falling", "India's own score fell on this goal")
            if ia.get("score") and ia["score"] < 50:
                add("lowest_score", f"India's weakest goal at {ia['score']} out of 100")
            if (ia.get("prev") and ia.get("score") and ia["score"] > ia["prev"]
                    and g["status"] == "declining"):
                add("direction_reversed",
                    "India's score rose on this goal while the underlying measure worsened")

            if reasons:
                scored.append({
                    "goal": g["n"], "title": g["title"],
                    "kind": "break" if r["break"] else "editorial",
                    "weight": round(min(weight, 0.99), 2),
                    "reasons": reasons,
                    "proposal": self._headline(g, r),
                    "why": "; ".join(reasons).capitalize() + ".",
                    "raised_by": r["agent"], "state": "awaiting",
                })

        scored.sort(key=lambda x: -x["weight"])
        queue = []
        for i, s in enumerate(scored[:6], 1):
            s["id"] = f"P-{i:04d}"
            queue.append(s)

        log(self.name, f"weighed 17 agents, {len(queue)} proposals raised")
        for q in queue:
            log(self.name, f"  {q['id']} goal {q['goal']:02d} weight {q['weight']:.2f}  {q['proposal'][:58]}")
        log(self.name, "handing the queue to the curator. Publishing nothing.")
        return {"at": NOW, "queue": queue}

    @staticmethod
    def _headline(g, r):
        if r["break"]:
            return f"Source break on goal {g['n']:02d}. A decision is needed on manual entry."
        ind = g.get("india_ind") or {}
        if ind.get("dispute"):
            return f"Lead with the {g['title'].lower()} source disagreement."
        if r["changed"]:
            return f"A figure moved on goal {g['n']:02d}. Consider the front page."
        return f"Raise {g['title'].lower()} to the front page."
