# session-context

State that changes between sessions. The stable contract lives in `CLAUDE.md`. For session-by-session history, see `git log`.

## Last touched

2026-05-27 — pipeline debug + Claude PR reviewer install + email delivery via Gmail SMTP. See commits `a2c6929`..`HEAD` for detail.

## Open threads

- **SmartRecruiters reclassification** — 230/300 sampled gap companies hit SR false positive (endpoint returns 200 for any slug). Need re-probe to determine real ATS. Deferred.
- **~82% of the 1,950 gap companies on Workday/ICIMS/Taleo** — Fidelity, Biogen, Moderna, BlackRock, Mastercard. No public API. Deferred.
- **Code reviewer not installed in other `dev/projects/` repos** — HomeAssistant, ThreadKeystores, app_clip, serato-dj-agent all missing the 6-file scaffold. Batch-install pattern in commit `3f43e03`.
- **Greenhouse BOM passthrough** still at the adapter level. `extract.py` strips defensively as catchall, but symmetric fix to `greenhouse.py` (matching Lever PR #1) is optional cleanup.
- **Workflow file named `daily.yml`** despite 3-day cadence. Cosmetic.
- **Cardata role** shows "Canada - Remote" but passed location filter — worth a manual location-logic check.
