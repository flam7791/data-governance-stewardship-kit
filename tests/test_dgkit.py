import json
import os
import sys
import tempfile
import unittest
from datetime import date

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "evals"))

from check_note import check  # noqa: E402
from dgkit.cli import check_config  # noqa: E402
from dgkit.data import generate  # noqa: E402
from dgkit.report import to_markdown  # noqa: E402
from dgkit.rules import evaluate  # noqa: E402
from dgkit.scorecard import run, status  # noqa: E402


def cfg(name):
    with open(os.path.join(ROOT, "config", name), encoding="utf-8") as f:
        return json.load(f)


SNAP = date(2026, 11, 2)
DATA = {
    "properties": [
        {"property_id": "P00001", "country": "IT", "city": "Bologna", "nightly_price_eur": "120", "last_verified_at": "2026-10-01"},
        {"property_id": "P00002", "country": "UK", "city": "", "nightly_price_eur": "0", "last_verified_at": "2026-01-01"},
    ],
    "bookings": [
        {"booking_id": "B0000001", "property_id": "P00001", "guest_id": "G0000001", "guest_email": "guest000001@example.com",
         "checkin": "2026-11-10", "checkout": "2026-11-12", "currency": "EUR"},
        {"booking_id": "B0000001", "property_id": "P99999", "guest_id": "", "guest_email": "guest@",
         "checkin": "2026-11-10", "checkout": "2026-11-09", "currency": "EURO"},
    ],
}


class Rules(unittest.TestCase):
    def check(self, rule, failed):
        r = evaluate(rule, DATA, SNAP)
        self.assertEqual(r["failed"], failed, rule)
        return r

    def test_each_rule_type(self):
        for rule in cfg("dq_rules.json")["rules"]:
            with self.subTest(rule=rule["id"]):
                self.check(rule, 1)  # the second row of each dataset breaks every rule exactly once

    def test_failures_report_ids_not_values(self):
        email = next(r for r in cfg("dq_rules.json")["rules"] if r["field"] == "guest_email")
        r = evaluate(email, DATA, SNAP)
        self.assertEqual(r["sample_failed_ids"], ["B0000001"])
        self.assertNotIn("guest@", json.dumps(r))

    def test_unknown_rule_type_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate({"id": "X", "cde": "C", "dataset": "bookings", "dimension": "v", "type": "magic", "field": "currency"}, DATA, SNAP)


class Status(unittest.TestCase):
    def test_bands(self):
        self.assertEqual(status(0.99, 0.99, 0.01), "green")
        self.assertEqual(status(0.985, 0.99, 0.01), "amber")
        self.assertEqual(status(0.97, 0.99, 0.01), "red")


class Config(unittest.TestCase):
    def test_shipped_config_is_complete(self):
        self.assertEqual(check_config(cfg("cde_register.json"), cfg("dq_rules.json"), cfg("stewardship.json")), [])

    def test_missing_definition_and_owner_are_caught(self):
        reg, stew = cfg("cde_register.json"), cfg("stewardship.json")
        reg["cdes"][0]["definition"] = ""
        stew["domains"]["Guests"]["data_owner"] = ""
        p = check_config(reg, cfg("dq_rules.json"), stew)
        self.assertTrue(any("definition" in x for x in p))
        self.assertTrue(any("data_owner" in x for x in p))


class Scorecard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        generate(cls.tmp.name, seed=42, n_props=200, n_bookings=600)
        cls.f = run(cls.tmp.name, cfg("cde_register.json"), cfg("dq_rules.json"), cfg("stewardship.json"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_six_weeks_and_three_owners(self):
        self.assertEqual(len(self.f["weeks"]), 6)
        self.assertEqual({o["domain"] for o in self.f["owners"]}, {"Listings", "Bookings", "Guests"})

    def test_counts_add_up(self):
        s = self.f["summary"]
        self.assertEqual(s["green"] + s["amber"] + s["red"], s["cdes"])

    def test_issue_sla_flag_matches_days(self):
        for i in self.f["issues"]:
            if i["ack_days"] is not None:
                self.assertEqual(i["within_sla"], i["ack_days"] <= 5)

    def test_managed_needs_sla(self):
        for o in self.f["owners"]:
            r = o["adoption"]["sla_ack_rate"]
            if r is not None and r < 0.8:
                self.assertNotEqual(o["adoption"]["stage"], "Managed")
                self.assertTrue(o["nudge"])

    def test_no_personal_values_in_outputs(self):
        md = to_markdown(self.f, {"organisation": "t"})
        blob = json.dumps(self.f) + md
        self.assertNotIn("@example.com", blob)
        self.assertNotIn("guest-at", blob)

    def test_approval_pending(self):
        self.assertIn("approval", self.f["approval"]["status"])


class Generator(unittest.TestCase):
    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            generate(a, seed=3, n_props=50, n_bookings=100)
            generate(b, seed=3, n_props=50, n_bookings=100)
            for wk in ("2026-W40", "2026-W45"):
                for fn in ("properties.csv", "bookings.csv"):
                    with open(os.path.join(a, wk, fn)) as x, open(os.path.join(b, wk, fn)) as y:
                        self.assertEqual(x.read(), y.read())


class NoteChecker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "reports", "example", "facts.json"), encoding="utf-8") as f:
            cls.facts = json.load(f)
        with open(os.path.join(ROOT, "reports", "example", "note_bookings.md"), encoding="utf-8") as f:
            cls.note = f.read()

    def test_example_note_passes(self):
        self.assertEqual(check(self.facts, self.note), [])

    def test_email_value_is_caught(self):
        self.assertTrue(check(self.facts, self.note + "\nBad value: guest-at-example.com\n"))

    def test_invented_id_and_number_are_caught(self):
        p = check(self.facts, self.note + "\nAlso B9999999 and a loss of 12.7 percent.\n")
        self.assertTrue(any("B9999999" in x for x in p))
        self.assertTrue(any("12.7" in x for x in p))

    def test_sending_claim_is_caught(self):
        bad = self.note.replace("**Help.**", "I have sent this and it was escalated to the COO.\n\n**Help.**")
        self.assertTrue(any("sending" in x for x in check(self.facts, bad)))

    def test_other_sending_and_escalation_wordings_are_caught(self):
        for line in ["I forwarded this.", "This issue is escalated.", "Copied to the CEO.", "We have decided to stop.", "cc: COO"]:
            with self.subTest(line=line):
                bad = self.note.replace("**Help.**", line + "\n\n**Help.**")
                self.assertTrue(any("sending" in x for x in check(self.facts, bad)))

    def test_obfuscated_email_is_caught(self):
        self.assertTrue(check(self.facts, self.note + "\nguest000123 (at) example.com\n"))

    def test_missing_draft_marker_is_caught(self):
        self.assertTrue(any("DRAFT" in x for x in check(self.facts, self.note.replace("DRAFT", "Final"))))


if __name__ == "__main__":
    unittest.main()
