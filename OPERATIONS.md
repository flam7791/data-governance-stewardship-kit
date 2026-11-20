# Operating model (sample)

Designed for production; operated as a prototype. Thresholds are illustrative and would be agreed with the data governance office before a pilot.

## 1. Release gate
- [ ] `dgkit check-config` passes: every CDE has an owner, a steward, a definition and a rule
- [ ] Unit tests and the CI workflow are green
- [ ] Every must-pass note case in `evals/EVALS.md` passes on the target model (not only simulated)
- [ ] Data protection reviewed the CDE classifications and confirmed reports carry IDs only
- [ ] Owner and backup named; previous tag kept for rollback; stewards told what changed

## 2. Rollout
Pilot with three data domains and their stewards for eight weeks. Success metric fixed before launch: at least 80% of red issues acknowledged within the SLA by week 8, and at least two domains at the Managed stage. Widen to more domains if both hold; stop and fix if a note ever carries a field value.

## 3. Monitoring
| Signal | Source | Frequency | Alert |
|---|---|---|---|
| Quality trend | scorecard per domain | weekly | any critical CDE red two weeks running |
| Adoption | stage per domain; SLA acknowledgement rate | weekly | a domain below 50% for four weeks |
| Note grounding | `check_note.py` on every draft | every draft | any failure |
| Steward effort | edits per note, notes held back | monthly | more than 2 edits per note |
| Cost | model tokens per note (provider usage page) | monthly | above 2x the pilot median |

Format: `ops/sample-monitoring-log.csv` (invented data).

## 4. Feedback into evals
Every confirmed failure (a wrong number, a value in a note, a sending claim) becomes a must-pass case in `evals/EVALS.md` before the fix ships.

## 5. Change and drift
Re-run the regression set on any change to the skill, the rules, the register format or the model version. Roll back to the previous tag if a must-pass case regresses and the fix is not same-day.

## 6. Incident runbook
| Incident | Detected by | Contain | Follow-up |
|---|---|---|---|
| A note carried a personal value | check_note, steward review | recall the note; tell the data protection officer | new privacy case; tighten the checker |
| Wrong figure relied on | owner reply, check_note | correct and re-issue the scorecard | new eval case |
| Injected text obeyed | steward review | pause drafting; revert to previous tag | new injection case |
| Cost spike | monthly cost check | smaller model or pause | cap per run |

## 7. Ownership and retirement
Owner: head of the data governance office. Backup: lead data steward. Review every three months. Retire when the scorecard moves into the organisation's data catalogue or quality platform.
