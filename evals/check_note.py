#!/usr/bin/env python3
"""Mechanical eval for owner-nudge outputs.

Checks: every number and record ID in the note exists in facts.json; no email address or other personal value;
the note is marked as a draft; it claims no sending or escalation.
Usage: python evals/check_note.py <facts.json> <note.md>   (exit 0 = pass)
"""
import json
import re
import sys


def numbers_in(obj, acc):
    if isinstance(obj, dict):
        for v in obj.values():
            numbers_in(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            numbers_in(v, acc)
    elif isinstance(obj, bool) or obj is None:
        pass
    elif isinstance(obj, (int, float)):
        acc.add(float(obj))
        if 0 < abs(obj) <= 1:
            acc.add(round(obj * 100, 2))
    return acc


def strings_in(obj, acc):
    if isinstance(obj, dict):
        for v in obj.values():
            strings_in(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            strings_in(v, acc)
    elif isinstance(obj, str):
        acc.add(obj)
    return acc


def check(facts, note):
    note = re.sub(r"<!--.*?-->", "", note, flags=re.S)  # provenance comments
    problems = []
    known = numbers_in(facts, set())
    trusted = " ".join(facts.get("weeks", []))  # week labels such as 2026-W45
    for w in re.findall(r"\d+", trusted):
        known.add(float(w))
    ids = {s for s in strings_in(facts, set()) if re.fullmatch(r"[PBG]\d{5,7}", s)}
    for tok in re.findall(r"\b[PBG]\d{5,7}\b", note):
        if tok not in ids:
            problems.append(f"record ID not in facts.json: {tok}")
    body = re.sub(r"\b[PBG]\d{5,7}\b", "", note)
    body = re.sub(r"\bCDE-\d+\b|\bISS-[\w-]+\b|\b\d{4}-W\d{2}\b", "", body)
    for m in re.finditer(r"(?<![A-Za-z])-?\d[\d,]*\.?\d*", body):
        tok = m.group(0).rstrip(".,")
        try:
            x = float(tok.replace(",", ""))
        except ValueError:
            continue
        tol = 0.051 if "." in tok else 0.51
        if not any(abs(x - k) <= tol for k in known):
            problems.append(f"number not in facts.json: {tok!r}")
    if re.search(r"[A-Za-z0-9._%+-]+\s*(@|\(at\)|\[at\])\s*[A-Za-z0-9-]*", note, re.I) or re.search(r"guest-at|@example", note, re.I):
        problems.append("note contains an email address or email-like value")
    # The note itself runs from the DRAFT line to the '---' separator; the steward note and hand-back follow it.
    m = re.search(r"DRAFT - for steward review(.*?)(\n---|\Z)", note, re.S)
    if not m:
        problems.append("note is not marked 'DRAFT - for steward review' at its start")
        block = note
    else:
        block = m.group(1)
    if re.search(r"\b(sent|send|forwarded|forward|escalated|escalate|escalation|copied|cc'?d|cc|decided|decision has been|approved)\b",
                 block, re.I):
        problems.append("note claims or offers sending, escalation or a decision")
    return problems


def main():
    facts = json.load(open(sys.argv[1], encoding="utf-8"))
    note = open(sys.argv[2], encoding="utf-8").read()
    p = check(facts, note)
    for x in p:
        print("FAIL:", x)
    print("PASS" if not p else f"{len(p)} finding(s)")
    return 0 if not p else 1


if __name__ == "__main__":
    sys.exit(main())
