# Data quality and stewardship scorecard: Northwind Stays (fictional)

Week 2026-W45 (compared with 2026-W44) · 10 critical data elements · 4 green, 3 amber, 3 red · 3 issues raised this week

> Every figure is measured from the weekly snapshots by the rules in `config/dq_rules.json`. Reports show record IDs, never values: restricted personal fields stay in the source systems.

## 1. Data owners

| Domain | Data owner | Score | Change (pts) | Green / amber / red | Adoption stage | Issues acknowledged in SLA (4 wks) |
|---|---|---|---|---|---|---|
| Listings | Head of Supply Operations | 98.1% | -0.10 | 3 / 1 / 0 | Managed | 100.0% |
| Bookings | Head of Booking Operations | 98.2% | -0.18 | 1 / 1 / 2 | Measured | 0.0% |
| Guests | Head of Customer Service | 97.4% | +0.09 | 0 / 1 / 1 | Measured | 33.0% |

### Trend (average pass rate per week)

| Domain | 2026-W40 | 2026-W41 | 2026-W42 | 2026-W43 | 2026-W44 | 2026-W45 |
|---|---|---|---|---|---|---|
| Listings | 95.5% | 96.2% | 96.9% | 97.8% | 98.2% | 98.1% |
| Bookings | 99.6% | 99.8% | 99.6% | 99.8% | 98.4% | 98.2% |
| Guests | 97.6% | 98.0% | 97.5% | 97.4% | 97.3% | 97.4% |

## 2. Critical data elements, week 2026-W45

| CDE | Name | Domain | Dimension | Pass rate | Target | Status | Failed records | Sample record IDs |
|---|---|---|---|---|---|---|---|---|
| CDE-01 | Property country | Listings | validity | 99.2% | 99.0% | green | 4 of 500 | P00066, P00164, P00287, P00322 |
| CDE-02 | Property city | Listings | completeness | 99.4% | 97.0% | green | 3 of 500 | P00307, P00393, P00463 |
| CDE-03 | Nightly price | Listings | validity | 99.6% | 99.0% | green | 2 of 500 | P00337, P00425 |
| CDE-04 | Listing verification date | Listings | timeliness | 94.2% | 95.0% | AMBER | 29 of 500 | P00007, P00041, P00085, P00096, P00101 |
| CDE-05 | Booking identifier | Bookings | uniqueness | 98.0% | 99.0% | **RED** | 31 of 1531 | B0007554, B0007570, B0007639, B0007707, B0007725 |
| CDE-06 | Booked property | Bookings | consistency | 98.6% | 99.0% | AMBER | 22 of 1531 | B0007521, B0007550, B0007582, B0007591, B0007718 |
| CDE-07 | Stay dates | Bookings | consistency | 96.7% | 99.0% | **RED** | 51 of 1531 | B0007511, B0007518, B0007560, B0007563, B0007571 |
| CDE-08 | Booking currency | Bookings | validity | 99.5% | 97.0% | green | 7 of 1531 | B0007831, B0008290, B0008356, B0008650, B0008704 |
| CDE-09 | Guest identifier | Guests | completeness | 98.8% | 99.0% | AMBER | 18 of 1531 | B0007505, B0007515, B0007576, B0007887, B0008072 |
| CDE-10 | Guest contact email | Guests | validity | 95.9% | 97.0% | **RED** | 63 of 1531 | B0007523, B0007542, B0007596, B0007651, B0007656 |

## 3. Issue log (red elements)

| Issue | Domain | Failed records | Acknowledged after (days) | Within SLA |
|---|---|---|---|---|
| ISS-2026-W40-CDE-02 | Listings | 22 | 3 | yes |
| ISS-2026-W40-CDE-04 | Listings | 52 | 3 | yes |
| ISS-2026-W41-CDE-04 | Listings | 50 | 3 | yes |
| ISS-2026-W42-CDE-04 | Listings | 41 | 1 | yes |
| ISS-2026-W43-CDE-04 | Listings | 34 | 3 | yes |
| ISS-2026-W43-CDE-10 | Guests | 62 | 5 | yes |
| ISS-2026-W44-CDE-07 | Bookings | 37 | 10 | no |
| ISS-2026-W44-CDE-10 | Guests | 68 | 6 | no |
| ISS-2026-W45-CDE-05 | Bookings | 31 | 8 | no |
| ISS-2026-W45-CDE-07 | Bookings | 51 | 8 | no |
| ISS-2026-W45-CDE-10 | Guests | 63 | 6 | no |

## 4. Follow-up for the data stewards

- **Bookings** (Head of Booking Operations): 2 critical data element(s) red in 2026-W45; 0% of issues in the last 4 weeks acknowledged within the 5-day SLA.
- **Guests** (Head of Customer Service): 1 critical data element(s) red in 2026-W45; 33% of issues in the last 4 weeks acknowledged within the 5-day SLA.

Status: **draft notes need data-steward approval before they are sent**. dgkit and the owner-nudge agent never contact anyone; a steward reviews and sends.

Adoption stages: Aware -> Defined (owner, steward, definitions) -> Measured (every CDE has a rule) -> Managed (>= 80% of issues acknowledged within SLA).
