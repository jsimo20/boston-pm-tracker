# session-context

## Current state (2026-05-17)

Pilot is live on cron. Repo: https://github.com/jsimo20/boston-pm-tracker (private). 36 tests green. Plan at `~/.claude/plans/let-s-start-a-new-moonlit-hamster.md`.

- Python 3.12. Deps: httpx, anthropic, jinja2, beautifulsoup4, python-dotenv.
- Pipeline: `collect` → Stage 1 filter → `extract` (Claude Haiku, cached system prompt) → Stage 3 filter → `score` → `digest`.
- GitHub Action `pm-digest` (file: `.github/workflows/daily.yml`) runs every 3rd day of the month at 13:00 UTC (`0 13 */3 * *`). Writes `data/jobs.db` + `digests/YYYY-MM-DD.md` back to main with `[skip ci]`. `ANTHROPIC_API_KEY` set as repo secret.
- 14-company seed (Greenhouse + Lever). Recent live run: 788 postings → 19 kept Stage 1 → 14 main + 5 stretch. Daily output around 0–10 actionable roles after stale filter.
- Application tracking: digest carries forward unapplied roles (top 20 by score per queue). `cli review` interactive picker with `a/d/s/o/b/q`. `mark-applied`, `dismiss`, `unmark` non-interactive forms also exist.

## Open threads

- **Coverage today: ~1–3% of in-scope PM market.** Biggest lever: expand seed to 50–80 Greenhouse + Lever companies + add Ashby adapter. Would lift to ~25–35%. Workday (the next tier — Wayfair, Akamai, etc.) is multi-day work with no clean public API; intentionally deferred.
- **6 companies dropped** from initial 20-company seed during slug verification: Wayfair, DraftKings, Akamai (Workday), QuEra (no public ATS), Snyk (Ashby — 0 jobs at probe), DataRobot (own ATS). Worth revisiting when Ashby/Workday adapters land.
- **Workable / Ashby adapters** scaffolded only in plan, not yet implemented — defer until seed expands.
- **GH Action deprecation warning**: `actions/checkout@v4` and `actions/setup-python@v5` move to Node 24 in June 2026. Bump versions before then.
- **Workflow file is still named `daily.yml`** despite the 3-day cadence and `pm-digest` display name. Rename later if it bothers future-us; not breaking anything.

## Recent sessions

### 2026-05-17 — go-live + application tracking + manage-seeds skill
Steps 3–4 of the execution plan: `git init`, created private repo `jsimo20/boston-pm-tracker`, set `ANTHROPIC_API_KEY` secret, ran `gh workflow run pm-digest` (17s, committed cleanly). Cron then changed from daily to every 3 days (`0 13 */3 * *`); closed-section entries now link the title to the original URL (archived ATS pages often resolve).

Two more QA-driven fixes before go-live:
- **Toast QA**: "East Coast, USA" Principal PM, Agent Platform was rejected as `wrong_location`. East Coast wholly contains our three target metros, so added `\beast coast\b|\bnortheast(?:ern)?\b` to keep conditions. Intentionally did NOT add West Coast.
- **Remote audit**: `NON_US_REMOTE_RE` only caught 6 country tokens. Expanded to ~25 (Japan, Costa Rica, Philippines, Brazil, etc.) plus the inverted "<Country>, Remote" phrasing. No current postings were affected — preventive fix against future feeds. Audited 122 remote-tagged postings; 9 PM-titled remote roles, 8 correctly kept, 1 correctly discarded for seniority floor (Planet Labs IC "Product Manager"). Honest coverage estimate: ~1–3% of the addressable PM market today, structurally capped around 35% even with full Greenhouse+Lever+Ashby coverage.

**Application tracking added** as a new feature:
- DB: `applied_at` and `dismissed_at` columns on `postings`, added via `_ensure_column()` so the live DB migrates idempotently.
- New module `review.py` with interactive picker. Sorted by score desc; keys `a/d/s/o/b/q` to act/skip/open URL/go back/quit. Uses `webbrowser.open()` from stdlib for `o`.
- CLI: `review`, `mark-applied <external_id>`, `dismiss <external_id>`, `unmark <external_id>`. `external_id` is the `gh_jid` number for Greenhouse, the slug for Lever.
- Digest: each queue now has a "new" section (first seen this run) and a "carried forward" section (top 20 by score, pending, not stale, not yet applied/dismissed). Stats footer adds `Pending unapplied` and `Applied lifetime`. Stale filter (`>30d`) still applies to carry-forward.

Added a project-level skill at `.claude/skills/manage-seeds/SKILL.md`. Future Claude sessions in this repo can manage `seeds/companies.json` (add/remove/swap/probe/audit) in plain English, without the user invoking a CLI. Encodes the conventions we learned the hard way: probe the ATS endpoint before adding (no 404s), don't auto-run the pipeline (saves Claude tokens), don't add Workable/Ashby rows until those adapters ship.

### 2026-05-15 — pilot QA and bug hunt
First live run against real ATS feeds. Iteratively fixed filter bugs surfaced by user QA:
- **Stage 1 was matching on raw JSON blob** — caused Dublin/SF roles to be kept because raw payload contained Boston office strings. Fixed: location check uses only the explicit `location` field.
- **Engineering-role exclusion was too aggressive** — discarded "Lead PM, Developer Experience" because "Developer" appeared in the product area. Fixed: a clear PM title stem now wins over the IC-role exclusion.
- **Stage 3 comp floor gated on `comp_base_min`** — discarded Klaviyo Senior PMs whose $136–204K range had a bottom $4K under the $140K floor. Fixed: gate on `comp_base_max` instead. Wide ranges that span the floor are kept.
- **"East Coast, USA" was rejected as wrong-location** — Toast's Principal PM, Agent Platform missed. Fixed: added `east coast` / `northeast(ern)` as in-scope (intentionally not `west coast`).
- **Non-US remote blocklist was thin** — only caught EMEA/UK/EU/India/Canada/APAC. Expanded to ~25 countries plus inverted "<Country>, Remote" phrasing.
- **UTC vs local date** — digest target was using local date but `first_seen_at` is stored UTC; produced empty digests around the date boundary. Fixed.
- **Added `python-dotenv` with `override=True`** — parent process exposes an empty `ANTHROPIC_API_KEY` to subprocesses, blocking the file load without it.

### 2026-05-14 — initial scaffold
Built three-layer pipeline (collect → agentic extract → score) with hard filters at Stages 1 and 3, deterministic scoring at Stage 4, and main vs stretch queue routing in the digest. Seeded 20 companies. Added stale-role exclusion: digest drops anything where source-side posted timestamp (Greenhouse `first_published`, Lever `createdAt`) is older than 30 days. Tests cover filter rules, adapter normalization, db schema, and scorer math.
