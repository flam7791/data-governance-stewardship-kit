"""Command line: python -m dgkit {generate,score,check-config} ..."""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .data import generate
from .report import write
from .rules import TYPES
from .scorecard import run


def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def check_config(register: dict, rules: dict, stewardship: dict) -> list[str]:
    """Structural checks on the governance configuration itself (the register must be complete before scoring)."""
    problems = []
    rids = {r["id"] for r in rules["rules"]}
    for c in register["cdes"]:
        if c["domain"] not in stewardship["domains"]:
            problems.append(f"{c['id']}: domain {c['domain']!r} has no owner in stewardship.json")
        if not c.get("definition", "").strip():
            problems.append(f"{c['id']}: no business definition")
        if not c.get("rules"):
            problems.append(f"{c['id']}: no quality rule")
        for r in c.get("rules", []):
            if r not in rids:
                problems.append(f"{c['id']}: rule {r} not defined")
        if c.get("criticality") not in stewardship["targets_by_criticality"]:
            problems.append(f"{c['id']}: unknown criticality {c.get('criticality')!r}")
    for r in rules["rules"]:
        if r["type"] not in TYPES:
            problems.append(f"{r['id']}: unknown rule type {r['type']!r}")
    for d, info in stewardship["domains"].items():
        for k in ("data_owner", "data_steward"):
            if not info.get(k):
                problems.append(f"domain {d}: {k} not named")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="dgkit")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate", help="write six weekly synthetic snapshots for Northwind Stays")
    g.add_argument("--out", default="data")
    g.add_argument("--seed", type=int, default=42)
    for name in ("score", "check-config"):
        s = sub.add_parser(name)
        s.add_argument("--register", default="config/cde_register.json")
        s.add_argument("--rules", default="config/dq_rules.json")
        s.add_argument("--stewardship", default="config/stewardship.json")
        if name == "score":
            s.add_argument("--data", default="data")
            s.add_argument("--out", default="reports/latest")
            s.add_argument("--organisation", default="Northwind Stays (fictional)")
    a = ap.parse_args(argv)
    if a.cmd == "generate":
        generate(a.out, a.seed)
        print(f"wrote six weekly snapshots to {a.out}/")
        return 0
    reg, rules, stew = _load(a.register), _load(a.rules), _load(a.stewardship)
    problems = check_config(reg, rules, stew)
    if a.cmd == "check-config" or problems:
        for p in problems:
            print("CONFIG:", p)
        print("config OK" if not problems else f"{len(problems)} config problem(s)")
        return 0 if not problems else 1
    try:
        facts = run(a.data, reg, rules, stew)
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    fj, md = write(facts, {"tool": "dgkit", "version": __version__, "organisation": a.organisation}, a.out)
    print(f"wrote {fj} and {md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
