# Design decisions

- **The register comes before the rules.** A rule without an owner, a steward and a business definition measures nothing anyone will act on. `dgkit check-config` fails the build when a critical data element lacks any of them.
- **A CDE is as good as its weakest rule.** Averaging rules hides the one that breaks downstream processes; the status uses the minimum.
- **Targets follow criticality.** Critical 99%, high 97%, medium 95%, with a one-point amber band, set once in `stewardship.json` and printed in every report.
- **IDs, never values.** Rules return the IDs of failing rows. Reports, facts.json and the nudge agent never carry a field value, so restricted personal data stays in the source systems. A CI step and a unit test check it.
- **Adoption is measured, not asserted.** Stages move from Aware to Defined (owner, steward, definitions), Measured (every CDE has a rule) and Managed (at least 80% of issues acknowledged within the SLA). An owner with good scores but slow acknowledgements is not Managed.
- **The agent drafts; the steward sends.** Change depends on the tone and timing of a human relationship, so the model only prepares a draft that a steward reviews, and a checker blocks drafts with invented figures, unknown IDs, email addresses or claims of sending.
- **Synthetic data, generated not committed.** Six weekly snapshots are generated from a seed in CI and compared with the committed example output, which keeps the repo small and the example reproducible.
