# session-context

## Current state (2026-05-18)

Pilot is live on cron. Repo: https://github.com/jsimo20/boston-pm-tracker (private). 44 tests green.

- Python 3.12. Deps: httpx, anthropic, jinja2, beautifulsoup4, python-dotenv.
- Pipeline: `collect` → Stage 1 filter → `extract` (Claude Haiku, cached system prompt) → Stage 3 filter → `score` → `digest`.
- GitHub Action `pm-digest` (file: `.github/workflows/daily.yml`) runs every 3rd day of the month at 13:00 UTC (`0 13 */3 * *`). Writes `data/jobs.db` + `digests/YYYY-MM-DD.md` back to main with `[skip ci]`. `ANTHROPIC_API_KEY` set as repo secret.
- **338-company seed** (GH + Lever only). Latest collect run: 11,545 postings → 129 kept Stage 1, 91 main + 36 stretch, 0 errors. `size_band` is metadata only — not used as a filter anywhere.
- `data/jobs.db` is gitignored (199MB raw, 73MB after dropping `raw_json` column). Pipeline rebuilds it on every run. `raw_json` column removed from postings — all needed fields already parsed into dedicated columns.
- Application tracking: digest carries forward unapplied roles (top 20 by score per queue). CLI entry point is `.venv\Scripts\boston-pm-tracker.exe`. `review`, `mark-applied`, `dismiss`, `unmark` subcommands.
- BIB full universe: 2,252 companies scraped from builtinboston.com. Raw data at `data/builtinboston_companies_with_slugs.json`.

## Open threads

- **NEXT: Build Ashby adapter** — highest-ROI remaining build. ~16/300 sampled not-found companies are on Ashby → ~100+ extrapolated across full 1,950 gap. API: `GET https://jobs.ashbyhq.com/api/non-user-graphql` (POST, GraphQL) or scrape `https://jobs.ashbyhq.com/{slug}`. Public, no auth. Snyk is a known Ashby company to test against. Need to: (1) write `src/boston_pm_tracker/adapters/ashby.py`, (2) wire into `collect.py`, (3) probe the 16 known Ashby companies from `data/ats_gap_analysis.json` + the ~100 estimated in the unprobed remainder using `probe_full_gap.py` (add Ashby probe), (4) add rows to seeds.
- **SmartRecruiters reclassification** — 230/300 sampled gap companies hit SR false positive. Need to re-probe those 230 to determine their real ATS. Deferred until after Ashby.
- **~82% of the 1,950 gap companies are on Workday/ICIMS/Taleo/custom pages** — large enterprises (Fidelity, Biogen, Moderna, BlackRock, Mastercard). No public API. Deferred.
- **GH Action deprecation warning**: `actions/checkout@v4` and `actions/setup-python@v5` move to Node 24 in June 2026. Bump before then.
- **Workflow file is still named `daily.yml`** despite the 3-day cadence. Not breaking anything.
- **Cardata role** shows "Canada - Remote" but passed location filter — worth a manual check of the location logic.

## Recent sessions

### 2026-05-18 — full gap probe + seed expansion + raw_json cleanup
Ran `scripts/probe_full_gap.py` (new script) on the remaining 1,522 unsampled not-found companies. Found 111 (86 GH, 25 Lever); 83 already in seeds, 28 net new → seed now 338. Pipeline run: 11,545 fetched, 129 Stage 1, 91 main + 36 stretch. New role surfaced: Verve, Inc. Senior PM, Data Partnerships ($120–155K).

Also cleaned up repo: dropped `raw_json TEXT NOT NULL` column from postings (was 198MB of the 199MB DB size); gitignored `data/jobs.db`; fixed push blocker caused by 199MB file exceeding GitHub's 100MB limit. Removed `raw_json` from both adapter dataclasses, `upsert_posting` signature, and test fixtures. 44 tests green post-cleanup.

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
