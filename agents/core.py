#!/usr/bin/env python3
"""
The machinery every goal agent shares.

A goal agent owns exactly one goal. Four times a day it opens its two assigned
sources, one Indian and one international, stores each document exactly as
received, and only then looks at it. If nothing changed it stops. If something
changed it reads out the new value, has it independently rechecked, and writes
it into data/goals.json.

It never writes HTML. The site builder does that, from the data.
"""
import datetime, hashlib, json, pathlib

ROOT = pathlib.Path(__file__).parent.parent
SNAP = ROOT / "snapshots"
LOG = ROOT / "logs"
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
TODAY = datetime.datetime.now(IST).date().isoformat()   # the register runs on Indian time
NOW = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()

# Every goal agent gets one Indian source and one international source.
# A goal with only one is allowed to run, but it may not present a single
# figure as if it were settled.
SOURCES = {
    "mospi_nif": {"name": "MoSPI, National Indicator Framework Progress Report 2026",
                  "url": "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2279014&reg=48&lang=1",
                  "side": "india", "holds_record": True, "cadence": "annual"},
    "niti_sdg":  {"name": "NITI Aayog, SDG India Index 2023-24",
                  "url": "https://www.niti.gov.in/reports-sdg",
                  "side": "india", "holds_record": True, "cadence": "biennial"},
    "un_sdg":    {"name": "UN Sustainable Development Goals Report 2025",
                  "url": "https://unstats.un.org/sdgs/report/2025/",
                  "side": "world", "holds_record": True, "cadence": "annual"},
    "sdr":       {"name": "Sustainable Development Report 2026",
                  "url": "https://dashboards.sdgindex.org/rankings/",
                  "side": "world", "holds_record": False, "compiles": True, "cadence": "annual"},
    "who_unicef":{"name": "WHO and UNICEF joint estimates",
                  "url": "https://www.who.int/data/gho",
                  "side": "world", "holds_record": True, "cadence": "annual"},
    "pib":       {"name": "Press Information Bureau",
                  "url": "https://www.pib.gov.in/allRel.aspx",
                  "side": "india", "holds_record": True, "cadence": "daily", "watch_only": True},
}


def log(agent, msg, level="info"):
    line = f"{NOW} [{level:<5}] {agent:<16} {msg}"
    print(line)
    LOG.mkdir(exist_ok=True)
    with (LOG / f"{TODAY}.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


class SourceBreak(Exception):
    """The source is unreachable or no longer the declared shape. Never swallowed."""


class Refused(Exception):
    """The method forbids producing a value here. Never substituted with an estimate."""


class Retriever:
    """Stores documents. Interprets nothing. This is the only code that touches the network."""

    def fetch(self, key):
        meta = SOURCES[key]
        body, origin = None, None
        try:
            import requests
            r = requests.get(meta["url"], timeout=25,
                             headers={"User-Agent": "tranqathma-register/1.0 (+public register)"})
            if r.status_code == 200 and r.text:
                body, origin = r.text, "live"
            else:
                log("retriever", f"{key}: HTTP {r.status_code}", "warn")
        except Exception as ex:                                   # noqa: BLE001
            log("retriever", f"{key}: no network ({type(ex).__name__})", "warn")

        if body is None:
            fx = SNAP / key / "fixture.raw"
            if not fx.exists():
                raise SourceBreak(f"{key}: unreachable and no stored snapshot")
            body, origin = fx.read_text(encoding="utf-8"), "stored snapshot"

        d = SNAP / key
        d.mkdir(parents=True, exist_ok=True)
        sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
        (d / f"{TODAY}.raw").write_text(body, encoding="utf-8")
        (d / f"{TODAY}.meta.json").write_text(json.dumps({
            "source": key, "name": meta["name"], "url": meta["url"], "side": meta["side"],
            "sha256": sha, "retrieved_at_utc": NOW, "origin": origin, "bytes": len(body),
        }, indent=1), encoding="utf-8")

        prev = self._last_sha(key)
        changed = prev is not None and prev != sha
        first = prev is None
        return {"key": key, "sha": sha, "body": body, "changed": changed,
                "first_seen": first, "origin": origin}

    @staticmethod
    def _last_sha(key):
        metas = sorted((SNAP / key).glob("2*.meta.json")) if (SNAP / key).exists() else []
        metas = [m for m in metas if not m.name.startswith(TODAY)]
        if not metas:
            return None
        return json.loads(metas[-1].read_text(encoding="utf-8")).get("sha256")


class Checker:
    """
    The independent recheck. It re-derives a proposed value from the stored bytes
    by a path that shares no code with whatever produced the proposal. A single
    process that both produces and verifies a number has verified nothing.
    """

    @staticmethod
    def verify(proposed, snapshot_body, field_path):
        try:
            payload = json.loads(snapshot_body)
        except json.JSONDecodeError:
            return False, "snapshot is not the declared shape"
        node = payload
        for part in field_path:
            if not isinstance(node, dict) or part not in node:
                return False, f"field {'.'.join(field_path)} absent from the snapshot"
            node = node[part]
        if node != proposed:
            return False, f"snapshot holds {node!r}, proposal says {proposed!r}"
        return True, "agrees with the stored document"


class GoalAgent:
    """One goal. One responsibility. Proposes, never publishes."""

    def __init__(self, n, title, india_source, world_source):
        self.n, self.title = n, title
        self.india_source, self.world_source = india_source, world_source
        self.name = f"Goal {n:02d} Agent"
        self.retriever, self.checker = Retriever(), Checker()

    # --- the four things an agent reports each run ---
    def run(self, goal_record):
        report = {"goal": self.n, "agent": self.name, "at": NOW,
                  "sources_checked": [], "changed": False, "verified": None,
                  "break": None, "proposal": None}

        for key in filter(None, (self.india_source, self.world_source)):
            try:
                snap = self.retriever.fetch(key)
            except SourceBreak as ex:
                report["break"] = str(ex)
                log(self.name, f"SOURCE BREAK {ex}", "break")
                continue
            report["sources_checked"].append(
                {"source": key, "sha": snap["sha"][:12], "origin": snap["origin"],
                 "changed": snap["changed"]})
            if snap["changed"]:
                report["changed"] = True
                log(self.name, f"{key} changed at source, recomputing")
                ok, why = self._recompute(goal_record, snap)
                report["verified"] = ok
                if not ok:
                    log(self.name, f"BLOCKED, {why}", "block")

        if not report["changed"] and not report["break"]:
            log(self.name, "no change at source")

        # Class B. Judgment, which never auto publishes.
        if goal_record.get("reading"):
            report["proposal"] = {
                "goal": self.n, "kind": "editorial",
                "proposal": goal_record["reading"][:150],
                "raised_by": self.name,
            }
        return report

    def _recompute(self, goal_record, snap):
        """
        Reads the declared field out of the stored document and checks it against
        what the record already holds. Class A only: a number moving at its source.
        """
        ind = goal_record.get("india_ind")
        if not ind:
            return True, "no headline indicator assigned, nothing to recompute"
        try:
            payload = json.loads(snap["body"])
        except json.JSONDecodeError:
            return False, "source is no longer the declared shape, line stopped"
        field = payload.get("fields", {}).get(ind.get("code", ""), None)
        if field is None:
            return True, "this source does not carry the headline field"
        ok, why = self.checker.verify(field.get("value"), snap["body"],
                                      ["fields", ind["code"], "value"])
        if ok and field.get("value") != ind["value"]:
            ind["prior"], ind["prior_period"] = ind["value"], ind["period"]
            ind["value"], ind["period"] = field["value"], field.get("period", ind["period"])
            log(self.name, f"value moved to {ind['value']} ({ind['period']}), published")
        return ok, why
