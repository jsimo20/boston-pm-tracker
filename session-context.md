# session-context

## Current state (2026-05-27)

Pipeline healthy end-to-end with email delivery. Latest run: 398 companies → 12,427 fetched → 135 Stage 1 → **90 main + 41 stretch** in [digests/2026-05-27.md](digests/2026-05-27.md). Next cron firing 2026-05-28 13:00 UTC.

- Python 3.12. Deps: httpx, anthropic, jinja2, beautifulsoup4, python-dotenv. 47 tests green.
- Pipeline: `collect` → Stage 1 filter → `extract` (Claude Haiku) → Stage 3 filter → `score` → `digest`.
- GitHub Action `pm-digest` (`.github/workflows/daily.yml`): checkout@v5 → setup-python@v6 → uv install → compute DIGEST_DATE → run pipeline → commit digests/ → **email via Gmail SMTP** (`dawidd6/action-send-mail@v6`). Cron `0 13 */3 * *`. Secrets: `ANTHROPIC_API_KEY`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`.
- Claude PR reviewer wired at `.github/workflows/claude-review.yml` + `.claude/agents/python-code-reviewer.md` + `.claude/context/*.md`. Fires on PR open/sync for `.py`, `.claude/**`, `claude-review.yml`. Same `ANTHROPIC_API_KEY` secret.
- 398-company seed (Greenhouse + Lever + Ashby). `data/jobs.db` gitignored, rebuilt every CI run.

## Open threads

- **SmartRecruiters reclassification** — 230/300 sampled gap companies hit SR false positive. Need re-probe to determine real ATS. Deferred.
- **~82% of the 1,950 gap companies are on Workday/ICIMS/Taleo** (Fidelity, Biogen, Moderna, BlackRock, Mastercard). No public API. Deferred.
- **Code reviewer not installed in other `dev/projects/` repos** — HomeAssistant, ThreadKeystores, app_clip, serato-dj-agent all missing the 6-file scaffold. Batch-install pattern in commit `3f43e03`.
- **Greenhouse BOM passthrough** still unhandled at the adapter — `extract.py` strips defensively as a catchall, but symmetric fix to greenhouse.py (matching Lever PR #1) is optional cleanup.
- **Workflow named `daily.yml`** despite 3-day cadence. Cosmetic.
- **Cardata role** shows "Canada - Remote" but passed location filter — worth a manual location-logic check.

## Recent sessions

### 2026-05-27 — pipeline debug, reviewer install, email delivery

Three things shipped:

1. **Pipeline unblocked after 9 days of silently-empty digests.** The `ANTHROPIC_API_KEY` GitHub secret was pasted on 2026-05-17 with a leading U+FEFF BOM; every extract call failed instantly at SDK `x-api-key` header construction (pattern signature: all 135 errors firing in 2ms). Confirmed by zero key usage in the Anthropic portal since 5/17. Fix: defensive `.strip().replace(_BOM, "")` on env-var read at [extract.py](src/boston_pm_tracker/extract.py) + user re-pasted the secret cleanly. First populated digest in weeks. Adapter-level BOM strips in ashby.py / lever.py are belt-and-suspenders. The earlier workflow surface failures (`git add data/jobs.db` exit 1, since the file is gitignored) were a separate bug fixed in commit `a2c6929` along with actions bump to v5/v6.

2. **Claude PR reviewer installed** (commit `3f43e03`) — 6 files copied from `jsimo20/repo-template`. Smoke-tested on PR #1 (Lever BOM defense): reviewer caught 1 MEDIUM (missing regression test) + 1 LOW (`.strip()` before `.replace()` ordering). Both addressed, merged. Reviewer won't run on changes to its own workflow file (self-modification guard) or on non-Python paths (rubric is Python-focused).

3. **Email delivery** via PR #2 (`0ace3f3`) — `dawidd6/action-send-mail@v6` + Gmail SMTP app password. `convert_markdown: true` so the digest renders as HTML in `jsimonelli16@gmail.com` inbox after each run. End-to-end verified 2026-05-27.

Sidebar: GitHub Actions had a 90-min auth-service incident on 2026-05-26 that returned `remote: Your account is suspended` 403s on the runner — misleading error string, account was fine. Lesson saved as [feedback-ci-auth-status-check](C:\Users\James\.claude\projects\c--Users-James-dev-projects-boston-pm-tracker\memory\feedback_ci_auth_status_check.md): check provider status page first when CI auth errors contradict local probes.

### 2026-05-18 — full gap probe + seed expansion + raw_json cleanup
Ran `scripts/probe_full_gap.py` on the remaining 1,522 unsampled not-found companies. Found 111 (86 GH, 25 Lever); 83 already in seeds, 28 net new → seed now 338. Pipeline: 11,545 fetched, 129 Stage 1, 91 main + 36 stretch. Surfaced Verve Inc. Senior PM, Data Partnerships ($120–155K).

Also cleaned up repo: dropped `raw_json TEXT NOT NULL` column from postings (was 198MB of the 199MB DB size); gitignored `data/jobs.db`; fixed push blocker caused by 199MB file exceeding GitHub's 100MB limit. Removed `raw_json` from both adapter dataclasses, `upsert_posting` signature, and test fixtures. 44 tests green post-cleanup.

### 2026-05-17 (session 2) — BIB universe expansion + ATS gap analysis
Used Playwright MCP to scrape all 113 pages of builtinboston.com via JSON-LD (note: script tag uses `application/ld&#x2B;json` encoding). Captured 2,252 companies. Ran concurrent async prober (`scripts/probe_ats.py`) against GH and Lever — found 302 valid endpoints (237 GH, 65 Lever). Merged with 14 existing seeds (9 overlapped) → 307-company `seeds/companies.json`. Collect: 10,822 postings, 124 Stage 1, 38 companies with qualifying PM roles, 0 errors.

Gap analysis on 300-company sample of not-found: 34 more on GH (slug mismatch), 5 more on Lever, 16 on Ashby, 245 other/unknown. SmartRecruiters endpoint confirmed false-positive (returns 200 for any slug). Workday confirmed as dominant platform for large enterprises in the gap.

### 2026-05-17 (session 1) — go-live + application tracking + manage-seeds skill
`git init`, created private repo `jsimo20/boston-pm-tracker`, set `ANTHROPIC_API_KEY` secret, ran `gh workflow run pm-digest` (17s, committed cleanly). Cron then changed from daily to every 3 days; closed-section entries now link title to original URL.

QA-driven fixes pre go-live:
- **Toast QA**: added `\beast coast\b|\bnortheast(?:ern)?\b` to keep conditions (intentionally not West Coast).
- **Remote audit**: expanded `NON_US_REMOTE_RE` from ~6 to ~25 country tokens + inverted "<Country>, Remote" phrasing. No current postings affected — preventive. Honest coverage estimate: ~1–3% of addressable PM market today, structurally capped ~35% even with full GH+Lever+Ashby.

Application tracking added: `applied_at` / `dismissed_at` columns via `_ensure_column()`; `review.py` interactive picker (a/d/s/o/b/q); CLI `review`, `mark-applied`, `dismiss`, `unmark`; digest now has "new" and "carried forward" sections per queue with stale filter (>30d).

Added project-level skill at `.claude/skills/manage-seeds/SKILL.md` for managing `seeds/companies.json` in plain English.

### 2026-05-15 — pilot QA and bug hunt
First live run against real ATS feeds. Iteratively fixed filter bugs surfaced by user QA:
- Stage 1 was matching on raw JSON blob (kept Dublin/SF roles when payload had Boston office strings) — gated on explicit `location` field only.
- Engineering-role exclusion too aggressive (discarded "Lead PM, Developer Experience") — clear PM title stem now wins over IC-role exclusion.
- Stage 3 comp floor gated on `comp_base_min` (discarded Klaviyo $136–204K range) — switched to `comp_base_max`; wide ranges spanning the floor are kept.
- Non-US remote blocklist thin (EMEA/UK/EU/India/Canada/APAC only) — expanded to ~25 countries + inverted phrasing.
- UTC vs local date — digest target was local but `first_seen_at` is UTC, producing empty digests around date boundary. Fixed.
- Added `python-dotenv` with `override=True` because parent process exposes empty `ANTHROPIC_API_KEY` to subprocesses.
