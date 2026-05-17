# session-context

## Current state (2026-05-15)

Pilot pipeline working end-to-end on real ATS feeds. 14-company seed (Greenhouse + Lever). 34 tests green. First production run: 788 postings fetched → 19 kept after Stage 1 → 19 extracted → 14 main + 5 stretch + 0 discard. Plan at `~/.claude/plans/let-s-start-a-new-moonlit-hamster.md`.

- Python 3.12, dependencies: httpx, anthropic, jinja2, beautifulsoup4, python-dotenv.
- Pipeline: `collect` → Stage 1 filter → `extract` (Claude Haiku, cached system prompt) → Stage 3 filter → `score` → `digest`.
- Daily GitHub Action at 13:00 UTC writes `data/jobs.db` and `digests/YYYY-MM-DD.md` back to main.

## Open threads

- **Step 3 of execution plan**: `git init` + `gh repo create jsimo20/boston-pm-tracker --private` + `gh secret set ANTHROPIC_API_KEY` — proceeding now.
- **Step 4**: `gh workflow run daily-pm-digest` (manual `workflow_dispatch`) to validate the Action.
- **Coverage today**: ~1–3% of in-scope PM market. Expansion to 50–80 Greenhouse + Lever companies + Ashby adapter is highest leverage next move (would lift to ~25–35%).
- **6 companies dropped** from initial 20-company seed: Wayfair, DraftKings, Akamai (Workday), QuEra (no public ATS), Snyk (Ashby — 0 jobs at probe time), DataRobot (own ATS). Worth revisiting when we add Ashby/Workday adapters.
- **Workable / Ashby adapters** scaffolded only in plan, not yet implemented — defer until seed expands.

## Recent sessions

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
