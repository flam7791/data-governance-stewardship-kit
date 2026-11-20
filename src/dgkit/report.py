"""Write facts.json (input for the owner-nudge agent) and scorecard.md (for people)."""
from __future__ import annotations

import json
import os

DOT = {"green": "green", "amber": "AMBER", "red": "**RED**"}


def pct(x) -> str:
    return "n/a" if x is None else f"{x * 100:.1f}%"


def to_markdown(facts: dict, meta: dict) -> str:
    s, wk = facts["summary"], facts["latest_week"]
    out = [f"# Data quality and stewardship scorecard: {meta['organisation']}", "",
           f"Week {wk} (compared with {facts['previous_week']}) · {s['cdes']} critical data elements · "
           f"{s['green']} green, {s['amber']} amber, {s['red']} red · {s['open_issues_latest_week']} issues raised this week", "",
           "> Every figure is measured from the weekly snapshots by the rules in `config/dq_rules.json`. "
           "Reports show record IDs, never values: restricted personal fields stay in the source systems.", "",
           "## 1. Data owners", "",
           "| Domain | Data owner | Score | Change (pts) | Green / amber / red | Adoption stage | Issues acknowledged in SLA (4 wks) |",
           "|---|---|---|---|---|---|---|"]
    for o in facts["owners"]:
        ch = "n/a" if o["change_pp"] is None else f"{o['change_pp']:+.2f}"
        out.append(f"| {o['domain']} | {o['data_owner']} | {pct(o['score'])} | {ch} | {o['green']} / {o['amber']} / {o['red']} | "
                   f"{o['adoption']['stage']} | {pct(o['adoption']['sla_ack_rate'])} |")
    out += ["", "### Trend (average pass rate per week)", "", "| Domain | " + " | ".join(facts["weeks"]) + " |",
            "|---|" + "---|" * len(facts["weeks"])]
    for o in facts["owners"]:
        out.append(f"| {o['domain']} | " + " | ".join(pct(x) for x in o["trend"]) + " |")
    out += ["", f"## 2. Critical data elements, week {wk}", "",
            "| CDE | Name | Domain | Dimension | Pass rate | Target | Status | Failed records | Sample record IDs |",
            "|---|---|---|---|---|---|---|---|---|"]
    for c in facts["latest_cdes"]:
        out.append(f"| {c['cde']} | {c['name']} | {c['domain']} | {c['dimension']} | {pct(c['pass_rate'])} | {pct(c['target'])} | "
                   f"{DOT[c['status']]} | {c['failed_records']} of {c['records']} | {', '.join(c['sample_failed_ids']) or '-'} |")
    out += ["", "## 3. Issue log (red elements)", "", "| Issue | Domain | Failed records | Acknowledged after (days) | Within SLA |",
            "|---|---|---|---|---|"]
    for i in facts["issues"][-12:]:
        out.append(f"| {i['issue']} | {i['domain']} | {i['failed_records']} | {i['ack_days'] if i['ack_days'] is not None else 'open'} | "
                   f"{'yes' if i['within_sla'] else 'no'} |")
    out += ["", "## 4. Follow-up for the data stewards", ""]
    nudges = [o for o in facts["owners"] if o["nudge"]]
    if not nudges:
        out.append("No owner needs a follow-up this week.")
    for o in nudges:
        out.append(f"- **{o['domain']}** ({o['data_owner']}): " + "; ".join(o["nudge_reasons"]) + ".")
    out += ["", f"Status: **{facts['approval']['status']}**. {facts['approval']['rule']}", "",
            "Adoption stages: " + facts["policy"]["stages"] + "."]
    return "\n".join(out) + "\n"


def write(facts: dict, meta: dict, outdir: str):
    os.makedirs(outdir, exist_ok=True)
    fj, md = os.path.join(outdir, "facts.json"), os.path.join(outdir, "scorecard.md")
    with open(fj, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, **facts}, f, indent=1, ensure_ascii=False)
    with open(md, "w", encoding="utf-8") as f:
        f.write(to_markdown(facts, meta))
    return fj, md
