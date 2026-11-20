"""Weekly scorecards per critical data element and per data owner, the issue log, and stewardship adoption.

Measured: pass rates, statuses, failing counts, record IDs, acknowledgement times from the issue log.
Nothing here decides or sends anything; nudge candidates are listed for a data steward to act on.
"""
from __future__ import annotations

import os
from statistics import mean

from .data import WEEKS, load_acks, load_snapshot, snapshot_date
from .rules import evaluate

STAGES = ["Aware", "Defined", "Measured", "Managed"]


def status(rate: float, target: float, margin: float) -> str:
    if rate >= target:
        return "green"
    return "amber" if rate >= target - margin else "red"


def run(data_dir: str, register: dict, rules_cfg: dict, stewardship: dict, weeks: list[str] | None = None) -> dict:
    weeks = weeks or [w for w in WEEKS if os.path.isdir(os.path.join(data_dir, w))]
    if not weeks:
        raise ValueError(f"no weekly snapshots found in {data_dir}")
    cdes = {c["id"]: c for c in register["cdes"]}
    rules = {r["id"]: r for r in rules_cfg["rules"]}
    domains = stewardship["domains"]
    targets = stewardship["targets_by_criticality"]
    margin = stewardship["amber_margin"]
    acks = load_acks(os.path.join(data_dir, "issue_acknowledgements.csv"))

    by_week = {}
    issues = []
    for wk in weeks:
        data = load_snapshot(os.path.join(data_dir, wk))
        snap = snapshot_date(wk)
        cde_rows = []
        for cid, c in cdes.items():
            res = [evaluate(rules[r], data, snap) for r in c["rules"]]
            rate = min(x["pass_rate"] for x in res)  # a CDE is as good as its weakest rule
            target = targets[c["criticality"]]
            st = status(rate, target, margin)
            failed = sum(x["failed"] for x in res)
            ids = list(dict.fromkeys(i for x in res for i in x["sample_failed_ids"]))[:5]
            cde_rows.append({"cde": cid, "name": c["name"], "domain": c["domain"], "criticality": c["criticality"],
                             "definition": c["definition"],
                             "classification": c["classification"], "rules": c["rules"],
                             "dimension": res[0]["dimension"], "pass_rate": rate, "target": target, "status": st,
                             "failed_records": failed, "records": res[0]["total"], "sample_failed_ids": ids})
            if st == "red":
                ack = acks.get((wk, c["domain"]))
                sla = domains[c["domain"]]["issue_sla_days"]
                issues.append({"issue": f"ISS-{wk}-{cid}", "week": wk, "cde": cid, "domain": c["domain"],
                               "failed_records": failed, "ack_days": ack,
                               "within_sla": (ack is not None and ack <= sla)})
        dom_scores = {}
        for d in domains:
            rows = [r for r in cde_rows if r["domain"] == d]
            dom_scores[d] = {"score": round(mean(r["pass_rate"] for r in rows), 4),
                             "green": sum(r["status"] == "green" for r in rows),
                             "amber": sum(r["status"] == "amber" for r in rows),
                             "red": sum(r["status"] == "red" for r in rows)}
        by_week[wk] = {"cdes": cde_rows, "domains": dom_scores}

    latest, prev = weeks[-1], (weeks[-2] if len(weeks) > 1 else None)
    owners = []
    for d, info in domains.items():
        cur = by_week[latest]["domains"][d]
        before = by_week[prev]["domains"][d]["score"] if prev else None
        change_pp = round((cur["score"] - before) * 100, 2) if before is not None else None
        dcdes = [c for c in cdes.values() if c["domain"] == d]
        defined = bool(info.get("data_owner")) and bool(info.get("data_steward")) and all(c["definition"].strip() for c in dcdes)
        coverage = sum(1 for c in dcdes if c["rules"]) / len(dcdes)
        recent = [i for i in issues if i["domain"] == d and i["week"] in weeks[-4:]]
        sla_rate = round(sum(i["within_sla"] for i in recent) / len(recent), 2) if recent else None
        stage = "Aware"
        if defined:
            stage = "Defined"
            if coverage == 1:
                stage = "Measured"
                if sla_rate is None or sla_rate >= 0.8:
                    stage = "Managed"
        reasons = []
        if change_pp is not None and change_pp <= -0.5:
            reasons.append(f"score fell {abs(change_pp)} points since {prev}")
        if cur["red"]:
            reasons.append(f"{cur['red']} critical data element(s) red in {latest}")
        if sla_rate is not None and sla_rate < 0.8:
            reasons.append(f"{int(round(sla_rate * 100))}% of issues in the last 4 weeks acknowledged within the {info['issue_sla_days']}-day SLA")
        owners.append({"domain": d, "data_owner": info["data_owner"], "data_steward": info["data_steward"],
                       "score": cur["score"], "previous_score": before, "change_pp": change_pp,
                       "green": cur["green"], "amber": cur["amber"], "red": cur["red"],
                       "trend": [by_week[w]["domains"][d]["score"] for w in weeks],
                       "adoption": {"stage": stage, "register_complete": defined, "rule_coverage": coverage,
                                    "issues_last_4_weeks": len(recent), "sla_ack_rate": sla_rate,
                                    "issue_sla_days": info["issue_sla_days"]},
                       "red_cdes": [c for c in by_week[latest]["cdes"] if c["domain"] == d and c["status"] == "red"],
                       "nudge": bool(reasons), "nudge_reasons": reasons})

    return {
        "weeks": weeks, "latest_week": latest, "previous_week": prev,
        "summary": {"cdes": len(cdes), "green": sum(o["green"] for o in owners), "amber": sum(o["amber"] for o in owners),
                    "red": sum(o["red"] for o in owners), "open_issues_latest_week": sum(1 for i in issues if i["week"] == latest)},
        "owners": owners, "latest_cdes": by_week[latest]["cdes"], "issues": issues,
        "history": {w: by_week[w]["domains"] for w in weeks},
        "policy": {"targets_by_criticality": targets, "amber_margin": margin,
                   "cde_status_rule": "a CDE takes the pass rate of its weakest rule",
                   "stages": "Aware -> Defined (owner, steward, definitions) -> Measured (every CDE has a rule) -> Managed (>= 80% of issues acknowledged within SLA)"},
        "approval": {"status": "draft notes need data-steward approval before they are sent",
                     "rule": "dgkit and the owner-nudge agent never contact anyone; a steward reviews and sends."},
    }
