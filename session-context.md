# session-context

## Current state (2026-05-17)

Pilot is live on cron. Repo: https://github.com/jsimo20/boston-pm-tracker (private). 36 tests green.

- Python 3.12. Deps: httpx, anthropic, jinja2, beautifulsoup4, python-dotenv.
- Pipeline: `collect` → Stage 1 filter → `extract` (Claude Haiku, cached system prompt) → Stage 3 filter → `score` → `digest`.
- GitHub Action `pm-digest` (file: `.github/workflows/daily.yml`) runs every 3rd day of the month at 13:00 UTC (`0 13 */3 * *`). Writes `data/jobs.db` + `digests/YYYY-MM-DD.md` back to main with `[skip ci]`. `ANTHROPIC_API_KEY` set as repo secret.
- **307-company seed** (expanded from 14). 237 Greenhouse, 65 Lever, 5 existing pre-discovery. Recent collect run: 10,822 postings → 124 kept Stage 1 across 38 companies. `size_band` is metadata only — not used as a filter anywhere.
- Application tracking: digest carries forward unapplied roles (top 20 by score per queue). `cli review` interactive picker with `a/d/s/o/b/q`. `mark-applied`, `dismiss`, `unmark` non-interactive forms also exist.
- BIB full universe: 2,252 companies scraped from builtinboston.com (all sizes, Hybrid/OnSite/Fully-Remote). Raw data at `data/builtinboston_companies_with_slugs.json`. Diff at `data/builtinboston_universe_diff.json`.

## Open threads

- **Next immediate win: fold in ~34 more Greenhouse + ~5 Lever companies** found via better slug guessing in `data/ats_gap_analysis.json`. Script `scripts/probe_ats_gap.py` identifies them.
- **Ashby adapter** is the highest-ROI next build: ~16/300 sampled not-found companies are on Ashby (~100+ extrapolated across full 1,950 gap). API: `https://jobs.ashbyhq.com/{slug}` — public, no auth. Snyk is already a known Ashby company.
- **~82% of the 1,950 gap companies are on Workday/ICIMS/Taleo/custom pages** — confirmed via gap analysis. These are mostly large enterprises (Fidelity, Biogen, Moderna, BlackRock, Mastercard). Workday has no public API; would require per-tenant scraping. Deferred.
- **SmartRecruiters probe is a false positive** — their careers endpoint returns 200 for any slug. Do not use it as a detection signal without a more specific check.
- **GH Action deprecation warning**: `actions/checkout@v4` and `actions/setup-python@v5` move to Node 24 in June 2026. Bump versions before then.
- **Workflow file is still named `daily.yml`** despite the 3-day cadence and `pm-digest` display name. Rename later if it bothers future-us; not breaking anything.
- **Top companies with current Stage 1 PM roles**: Veeva (30), Toast (11), Klaviyo (9), Datadog (7), The Engine (7), AlphaSense (4), Constant Contact (4), SimpliSafe (3), Sophos (3), Starburst (3), VEIR (3), WHOOP (3), ZoomInfo (3). `extract` + `score` + `digest` not yet run on the expanded set.

## Recent sessions

### 2026-05-17 (session 2) — BIB universe expansion + ATS gap analysis
Used Playwright MCP to scrape all 113 pages of builtinboston.com (Hybrid/OnSite/Fully-Remote, all sizes) via JSON-LD structured data (note: script tag uses `application/ld&#x2B;json` encoding). Captured 2,252 companies with name + BIB slug. Ran concurrent async prober (`scripts/probe_ats.py`) against Greenhouse and Lever APIs for all companies — found 302 with valid endpoints (237 GH, 65 Lever). Merged with existing 14 seeds (9 overlapped) → 307-company `seeds/companies.json`. Ran collect: 10,822 postings fetched, 124 kept Stage 1, 38 companies with qualifying PM roles, 0 errors.

Gap analysis (`scripts/probe_ats_gap.py`) on 300-company sample of not-found: 34 more on GH (slug mismatch), 5 more on Lever, 16 on Ashby, 245 on other/unknown. SmartRecruiters endpoint confirmed false-positive (returns 200 for any slug). Workday confirmed as dominant platform for large enterprises in the gap — no public API.

### 2026-05-17 (session 1) — go-live + application tracking + manage-seeds skill
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
