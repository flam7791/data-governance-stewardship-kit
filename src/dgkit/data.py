"""Loading snapshots, and the synthetic generator for the fictional Northwind Stays marketplace.

A snapshot is one folder per week with properties.csv and bookings.csv. All values are invented;
guest emails use the reserved example.com domain.
"""
from __future__ import annotations

import csv
import os
import random
from datetime import date, timedelta

WEEKS = [f"2026-W{w}" for w in range(40, 46)]
FIRST_MONDAY = date(2026, 9, 28)  # Monday of ISO week 40, 2026
COUNTRIES = ["AT", "BE", "CH", "DE", "DK", "ES", "FR", "GB", "GR", "IE", "IT", "NL", "PL", "PT", "SE"]
CITIES = {"AT": "Vienna", "BE": "Ghent", "CH": "Lugano", "DE": "Hamburg", "DK": "Aarhus", "ES": "Valencia",
          "FR": "Lyon", "GB": "York", "GR": "Chania", "IE": "Galway", "IT": "Bologna", "NL": "Utrecht",
          "PL": "Gdansk", "PT": "Porto", "SE": "Malmo"}

# Defect rate per week index 0..5 (invented). Listings improve, Bookings break in weeks 5-6, Guests flat.
RATES = {
    "bad_country":   [0.025, 0.018, 0.012, 0.008, 0.005, 0.004],
    "missing_city":  [0.040, 0.030, 0.022, 0.015, 0.010, 0.008],
    "bad_price":     [0.010, 0.008, 0.006, 0.004, 0.003, 0.003],
    "stale":         [0.120, 0.110, 0.095, 0.080, 0.065, 0.055],
    "dup_booking":   [0.002, 0.002, 0.003, 0.002, 0.018, 0.021],
    "orphan":        [0.005, 0.004, 0.005, 0.005, 0.014, 0.016],
    "bad_dates":     [0.001, 0.001, 0.002, 0.001, 0.024, 0.027],
    "bad_currency":  [0.006, 0.005, 0.006, 0.005, 0.006, 0.005],
    "no_guest":      [0.012, 0.013, 0.012, 0.014, 0.013, 0.012],
    "bad_email":     [0.034, 0.036, 0.033, 0.035, 0.034, 0.036],
}
# days until a data owner's team acknowledges an issue (invented, used to simulate the issue log)
ACK_DAYS = {"Listings": (1, 3), "Bookings": (6, 10), "Guests": (3, 6)}


def snapshot_date(week: str) -> date:
    return FIRST_MONDAY + timedelta(days=7 * WEEKS.index(week))


def generate(outdir: str, seed: int = 42, n_props: int = 500, n_bookings: int = 1500) -> None:
    rng = random.Random(seed)
    os.makedirs(outdir, exist_ok=True)
    props_base = []
    for i in range(1, n_props + 1):
        c = rng.choice(COUNTRIES)
        props_base.append({"property_id": f"P{i:05d}", "host_id": f"H{rng.randint(1, 300):04d}", "country": c,
                           "city": CITIES[c], "property_type": rng.choice(["apartment", "house", "room", "hotel"]),
                           "nightly_price_eur": round(rng.lognormvariate(4.6, 0.5), 2),
                           "verified_age_days": rng.randint(0, 170)})
    bk_counter = 0
    for wi, week in enumerate(WEEKS):
        snap = snapshot_date(week)
        d = os.path.join(outdir, week)
        os.makedirs(d, exist_ok=True)
        r = {k: v[wi] for k, v in RATES.items()}
        props = []
        for p in props_base:
            row = dict(p)
            if rng.random() < r["bad_country"]:
                row["country"] = rng.choice(["XX", "UK", "", "Germany"])
            if rng.random() < r["missing_city"]:
                row["city"] = ""
            if rng.random() < r["bad_price"]:
                row["nightly_price_eur"] = rng.choice([0, -1, 99999])
            age = p["verified_age_days"] + (181 if rng.random() < r["stale"] else 0)
            row["last_verified_at"] = (snap - timedelta(days=age)).isoformat()
            del row["verified_age_days"]
            props.append(row)
        with open(os.path.join(d, "properties.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(props[0].keys()))
            w.writeheader()
            w.writerows(props)
        bookings = []
        for _ in range(n_bookings):
            bk_counter += 1
            ci = snap - timedelta(days=rng.randint(1, 6)) + timedelta(days=rng.randint(7, 60))
            nights = rng.randint(1, 10)
            row = {"booking_id": f"B{bk_counter:07d}", "property_id": rng.choice(props_base)["property_id"],
                   "guest_id": f"G{rng.randint(1, 900000):07d}", "guest_email": f"guest{rng.randint(1, 900000):06d}@example.com",
                   "checkin": ci.isoformat(), "checkout": (ci + timedelta(days=nights)).isoformat(),
                   "currency": rng.choice(["EUR", "EUR", "EUR", "GBP", "USD", "CHF"]),
                   "created_at": (snap - timedelta(days=rng.randint(0, 6))).isoformat()}
            if rng.random() < r["orphan"]:
                row["property_id"] = f"P{rng.randint(90000, 99999):05d}"
            if rng.random() < r["bad_dates"]:
                row["checkout"] = (ci - timedelta(days=rng.randint(1, 3))).isoformat()
            if rng.random() < r["bad_currency"]:
                row["currency"] = rng.choice(["EURO", "", "eur"])
            if rng.random() < r["no_guest"]:
                row["guest_id"] = ""
            if rng.random() < r["bad_email"]:
                row["guest_email"] = rng.choice(["", "guest-at-example.com", "guest@", "n/a"])
            bookings.append(row)
            if rng.random() < r["dup_booking"]:
                bookings.append(dict(row))
        with open(os.path.join(d, "bookings.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(bookings[0].keys()))
            w.writeheader()
            w.writerows(bookings)
    # simulated acknowledgement times, used when an issue is raised for a rule in a week
    with open(os.path.join(outdir, "issue_acknowledgements.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["week", "domain", "ack_days"])
        for week in WEEKS:
            for dom, (lo, hi) in ACK_DAYS.items():
                w.writerow([week, dom, rng.randint(lo, hi)])


def load_snapshot(folder: str) -> dict[str, list[dict]]:
    out = {}
    for name in ("properties", "bookings"):
        path = os.path.join(folder, f"{name}.csv")
        if not os.path.exists(path):
            raise ValueError(f"snapshot {folder} is missing {name}.csv")
        with open(path, newline="", encoding="utf-8") as f:
            out[name] = list(csv.DictReader(f))
    return out


def load_acks(path: str) -> dict[tuple[str, str], int]:
    if not os.path.exists(path):
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {(r["week"], r["domain"]): int(r["ack_days"]) for r in csv.DictReader(f)}
