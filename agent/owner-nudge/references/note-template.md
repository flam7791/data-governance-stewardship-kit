# Note template (owner-nudge v0.1.0)

DRAFT - for steward review

**To:** <data_owner>
**From:** <data_steward>
**Subject:** <domain> data quality, <latest_week>: <n> element below target / <n> elements below target

**What changed.** In <latest_week> the <domain> score was <score>% (<change_pp> points against <previous_week>; if the score rose, say so: a red element still needs action). <For each red element: <name> passed <pass_rate>% of checks against a <target>% target; <failed_records> records failed.>

**Why it matters.** <One line per red element, from its definition.>

**What I am asking.** Please acknowledge this and name who will fix it within <issue_sla_days> days. <If sla_ack_rate is below 0.8: one neutral sentence, e.g. "Recent issues took longer than the <issue_sla_days>-day target to be acknowledged.">

**Help.** I can walk your team through the failing records and the rule behind each element.

**Sample record IDs:** <sample_failed_ids per red element>

---

**Note for the steward (not part of the note):** <anything odd in the data or the request, or "none">
