"""Rule engine: data-quality rules as code. Each rule returns pass counts and the IDs (never values) of failing rows."""
from __future__ import annotations

import re
from collections import Counter
from datetime import date

KEYS = {"properties": "property_id", "bookings": "booking_id"}
TYPES = {"not_null", "in_set", "regex", "range", "unique", "foreign_key", "date_order", "freshness"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _date(v):
    try:
        return date.fromisoformat(v)
    except (TypeError, ValueError):
        return None


def evaluate(rule: dict, data: dict[str, list[dict]], snapshot: date) -> dict:
    t = rule["type"]
    if t not in TYPES:
        raise ValueError(f"rule {rule['id']}: unknown type {t!r}")
    rows = data[rule["dataset"]]
    key = KEYS[rule["dataset"]]
    f = rule["field"]
    if t == "unique":
        seen: Counter = Counter()
        ok = []
        for r in rows:
            seen[r[f]] += 1
            ok.append(seen[r[f]] == 1)  # the first occurrence passes; repeats fail
    elif t == "foreign_key":
        ref = {r[rule["ref_field"]] for r in data[rule["ref_dataset"]]}
        ok = [r[f] in ref for r in rows]
    else:
        ok = []
        for r in rows:
            v = (r.get(f) or "").strip()
            if t == "not_null":
                ok.append(v != "")
            elif t == "in_set":
                ok.append(v in rule["values"])
            elif t == "regex":
                ok.append(bool(re.fullmatch(rule["pattern"], v)))
            elif t == "range":
                x = _num(v)
                ok.append(x is not None and rule["min"] <= x <= rule["max"])
            elif t == "date_order":
                a, b = _date(v), _date(r.get(rule["after_field"]))
                ok.append(a is not None and b is not None and b > a)
            elif t == "freshness":
                d = _date(v)
                ok.append(d is not None and (snapshot - d).days <= rule["max_age_days"])
    failed = [r[key] for r, good in zip(rows, ok) if not good]
    total = len(rows)
    return {"rule": rule["id"], "cde": rule["cde"], "dimension": rule["dimension"], "total": total,
            "failed": len(failed), "pass_rate": round((total - len(failed)) / total, 4) if total else None,
            "sample_failed_ids": list(dict.fromkeys(failed))[:5]}
