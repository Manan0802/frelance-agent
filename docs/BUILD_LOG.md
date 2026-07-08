# 🏗️ BUILD LOG — Freelancing Agent

**Append-only phase history.** Never delete or overwrite past entries. Each phase records
*what* was built, *why*, *how*, key files, decisions, tests, and commit range — so any future
session (or Manan, weeks later) has the full context and nothing goes missing as we advance.

Rule for future sessions: when you finish a phase, **append a new `## Phase N` section below**
(don't edit old ones). Update `CLAUDE.md` status line separately. Keep commit hashes.

Repo: https://github.com/Manan0802/frelance-agent · Branches: `main` + `phase1-engine-b`
Stack: Python 3.13, FastAPI, SQLAlchemy(SQLite), LangGraph patterns, Gemini, sentence-transformers,
green-api (WhatsApp), pytest. Venv at `./venv`.

---

## Phase 0 — Research & Design (2026-06-28)

**Goal:** Turn the raw PRD into an optimized, research-backed build plan.

**What happened:**
- Read `FREELANCING_AGENT_PRD.md` (original vision).
- Clarified Manan's situation: cold-start (real skills + portfolio, **zero platform reputation**),
  edge = production AI-agent dev, north star = steady good-rate quality clients, budget ~₹500-1500/mo.
- Researched existing open-source tools (kaymen99 repos, JobSpy, omkarcloud maps, Bricks, camoufox,
  agentic-inbox, MoneyPrinterTurbo, VoxCPM, etc.).

**Key decisions (don't lose these):**
1. **Two-engine model** instead of PRD's one engine:
   - Engine B (outbound/direct) FIRST — converts best for a no-reputation dev (no platform gatekeeper).
   - Engine A (inbound/bidding) second — job boards + proposals.
2. **Fork bases:** `kaymen99/Upwork-AI-jobs-applier` (A) + `kaymen99/sales-outreach-automation-langgraph` (B).
3. **WhatsApp via green-api** (not Telegram, not Twilio) — free-form, pure-Python, self-notify only.
4. **Gemini primary** (matches fork repos), Groq fallback later.
5. Tool sprawl controlled: everything tiered in `docs/research/TOOL_REGISTRY.md` (nothing discarded).

**Artifacts:** `docs/superpowers/specs/2026-06-28-freelancing-agent-design.md` (design spec),
`docs/research/TOOL_REGISTRY.md`, `docs/superpowers/plans/2026-06-28-phase1-engine-b.md` (plan).

---

## Phase 1 — Engine B (Outbound / Direct) (2026-06-28)

**Goal:** Runnable outbound pipeline: local business → research → personalized message →
WhatsApp digest → human review → CRM log. **Never auto-send.**

**How built (TDD, one task = failing test → code → green → commit):**

| Task | File(s) | What it does |
|---|---|---|
| 1 | `backend/config.py`, `database/connection.py`, `main.py` | Scaffold, settings, SQLite engine, `/health` |
| 2 | `backend/database/models.py` | `OutboundTarget`, `OutreachMessage`, `CrmRecord` |
| 3 | `backend/portfolio/context.py`, `data/portfolio_context.json` | Portfolio "brain" loader (Pydantic) |
| 4 | `backend/engine_b/ingest.py` | Maps dicts → targets, dedup (incl. within-batch, fixed) |
| 5 | `backend/engine_b/research.py`, `llm/gemini.py` | Fetch site + Gemini → summary + pain points |
| 6 | `backend/engine_b/matcher.py` | sentence-transformers embed → top-2 portfolio projects |
| 7 | `backend/engine_b/writer.py` | Personalized message + self-eval regen (<7/10 → redo) |
| 8 | `backend/notify/whatsapp.py` | green-api digest sender |
| 9 | `backend/engine_b/graph.py` | Orchestrator: research→match→write→persist→notify |
| 10 | `backend/api/routes.py` | `POST /run`, `GET /messages`, `PATCH /messages/{id}/approve` (+CRM log) |

**Design principle:** every LLM/HTTP boundary is **dependency-injected** so tests never hit
the network (fake `fetch`/`llm`/`embed`/`poster`/`http` passed in tests).

**Security fixes (from commit review):**
- **SSRF guard** in `research.py`: only http(s), block private/loopback/link-local/reserved IPs,
  redirects disabled. Test: `test_ssrf_guard_blocks_internal_addresses`.
- **Optional API-key gate** + **`MAX_TARGETS=50` batch cap** on `/run` & `/approve` (bounds LLM
  cost + WhatsApp volume; gate is no-op locally, enforced when `API_KEY` set).

**Result:** 14 tests green. Committed `051dfe9`..`ad12c93` (+docs `082d2c9`).

---

## Phase 1.5 — Engine A (Inbound / Bidding) (2026-07-02)

**Goal:** Pull jobs from free boards, score vs portfolio, draft proposals for top jobs,
surface via same review/CRM machinery. Mirrors Engine B's shape.

**How built (TDD, tasks A1–A8):**

| Task | File(s) | What it does |
|---|---|---|
| A1 | `database/models.py` (+`JobLead`, `InboundProposal`) | Inbound job + proposal tables |
| A2 | `backend/engine_a/remoteok.py` | RemoteOK JSON API → JobLead dicts, tag filter |
| A3 | `backend/engine_a/weworkremotely.py` | WWR RSS (feedparser) → JobLead dicts |
| A4 | `backend/engine_a/jobspy_source.py` | JobSpy adapter (injectable scrape) |
| A5 | `backend/engine_a/scorer.py` | LLM skill/budget score, auto-reject < 40 |
| A6 | `backend/engine_a/proposal.py` | Inbound proposal writer (reuses `engine_b.writer._score`) |
| A7 | `backend/engine_a/graph.py` | Orchestrator: dedup→score→top-N→match→write→notify |
| A8 | `backend/api/routes.py` (+`/run-inbound`) | Engine A endpoint (api-key gated, capped) |

**Key decisions:**
- Reused Engine B's `matcher`, `writer._score`, `format_digest`/`send_whatsapp` — no duplication.
- Fetchers injectable (`http`/`parse`/`scrape`) so JobSpy/feedparser aren't imported in tests.
- Added `tests/conftest.py` autouse fixture (drop+create schema per test) — fixed cross-test
  SQLite pollution that surfaced when Engine A's count assertions ran in the full suite.

**Result:** 23 tests green total. Committed `922d3f1`..`7c56e05`.

**NOT done yet:** no live run (needs `.env` + real data). React dashboard, APScheduler cron,
reply-triage, camoufox, Groq fallback, enrichment → Phase 2+.

---

## Scope clarification (2026-07-02)

**Decision (Manan):** this project is **FREELANCE / project-based clients ONLY**. Job-hunting
(full-time employment) is a **separate agent** Manan is building — keep this one out of that lane.

**Impact on Engine A:** the orchestrator/scorer/proposal code is generic and stays (it works for
freelance gigs). But **source priority pivots**: away from employment boards (RemoteOK/WWR/JobSpy
full-time listings) → toward freelance-gig + direct-client sources: Upwork, Freelancer.com,
PeoplePerHour, Contra, Fiverr, **HN "Freelancer? Seeking freelancer?"** (NOT "Who is hiring?"),
Reddit `[Hiring]` gig posts, X gig requests, and Engine B outbound (local businesses). When adding
new sources, only add freelance/contract ones.

**Not deleting** the existing RemoteOK/WWR/JobSpy fetchers — they can filter for contract/freelance
gigs — but they're no longer the priority. See updated `PLATFORM_COVERAGE.md` / `INSIDER_SOURCES.md`.

## Phase 2 — Research Audit Fixes + Review Dashboard (2026-07-06)

**Goal:** act on the 7-pass deep research audit (see the artifact linked from project memory)
run before this phase — correct stale doc claims, migrate off a dead SDK, and give Manan an
actual UI to review/approve drafts instead of raw JSON. Research-only findings on pricing and
India payments/tax were deliberately left as reference, not code — nothing to build there yet.

**Environment note:** this session runs on macOS, not the Windows the docs assumed. Created a
fresh `venv/` here (`./venv/bin/python`, not `./venv/Scripts/python.exe`) and confirmed the
existing 23 tests passed before changing anything.

**How built (TDD, one task = failing test → code → green → commit):**

| Task | File(s) | What it does |
|---|---|---|
| 1 | `docs/research/*.md`, `docs/PLATFORM_COVERAGE.md` | Corrected stale claims: Upwork RSS discontinued Aug 2024 (was documented as live), X/Twitter free API tier removed Feb 2026, Camoufox flagged unstable (maintainer handoff) with Patchright added as the new default, OpenSales/Linki/OpenOutreach downgraded to unverified. Catalogued new finds (gosom fallback, Prospeo/FullEnrich, PocketFlow reference, open-sdr, freelancer-rates dataset). |
| 2 | `backend/llm/gemini.py`, `requirements.txt`, `tests/test_gemini.py` | `google-generativeai` has ended all support (surfaced as a `FutureWarning` during the very first test run on the new venv — the research audit missed this, the test run caught it). Migrated to the `google-genai` client SDK; default model bumped `gemini-1.5-flash` → `gemini-2.0-flash-lite` (highest free-tier RPM as of 2026-07). `generate()` now takes an optional `model` override. |
| 3 | `backend/api/dashboard.py`, `backend/templates/`, `backend/static/dashboard.css`, `tests/test_dashboard.py` | New `GET /dashboard` — htmx + Jinja2 (no separate frontend build, matches the audit's "React is overhead for a solo tool" finding). Shows every outbound message and inbound proposal as a card (name, score, status pill, full draft, Approve button). `PATCH /dashboard/messages/{id}/approve` and `.../proposals/{id}/approve` patch status in place via htmx, no page reload. Refactored `routes.py`'s message-approve logic into a shared `approve_message()`/`approve_proposal()` pair so the JSON API and the dashboard don't duplicate it. |

**Design decision:** dashboard is server-rendered (Jinja2 templates + htmx from CDN), not React —
this was the audit's explicit recommendation for a single-user personal tool, and it means the
whole app is still one FastAPI process with no separate build/deploy step.

**Not done in this phase (left as backlog per the audit):** embedding model swap (MiniLM →
gemini-embedding-001, optional/low-urgency), WhatsApp → Telegram reconsideration, APScheduler →
plain OS cron for the daily entrypoint, a pricing agent, payments/tax tooling (both researched,
neither built — see the audit artifact for the payments/tax findings, which need a CA's
confirmation on the Section 44ADA point before anyone relies on them).

**Result:** 29 tests green (23 baseline + 6 new: 2 gemini, 4 dashboard).

---

## Phase 3 — Resilience + Missing Pieces (2026-07-08)

**Goal:** pick up the Phase 2 backlog — nothing should be a single point of failure, and Engine
B should be able to find its own leads instead of needing them passed in manually.

**How built (TDD, one task = failing test → code → green → commit):**

| Task | File(s) | What it does |
|---|---|---|
| 1 | `backend/llm/gemini.py`, `backend/config.py`, `tests/test_gemini.py` | `generate()` had zero fallback — any Gemini error (rate limit, outage, bad key) broke research/scoring/writing outright. Added a Groq (Llama 3.3 70B) fallback on any Gemini exception, matching the original design intent. New `GROQ_API_KEY` setting. |
| 2 | `backend/engine_b/maps_source.py`, `tests/test_maps_source.py` | New `fetch_google_maps()` — Engine B previously had **no automated lead source at all**; targets could only arrive via manually-crafted API calls. **Correction discovered while building this:** `omkarcloud/google-maps-scraper` (the CORE pick in `TOOL_REGISTRY.md` since Phase 0) has pivoted to a closed-source desktop app + paid hosted API — its GitHub repo now contains zero source code, just marketing docs. The 2026-07 research audit missed this (it only checked star count/activity, not whether the repo still had code in it). Rebuilt the fetcher against `gosom/google-maps-scraper` instead (MIT, confirmed active, real REST API) — verified the exact request/response contract from its official `examples/examples-api/python/scrape.py` client before writing the default implementation, rather than guessing. New `MAPS_SCRAPER_BASE_URL`/`MAPS_SCRAPER_API_KEY` settings; requires running the gosom service locally (`docker run gosom/google-maps-scraper`) for the real (non-test) path. |
| 3 | `backend/pricing/suggest.py`, `tests/test_pricing.py` | The original PRD's "Pricing Helper Agent" (§5.4) was designed but never built. Added a pure, deterministic `suggest_rate()` — no LLM call, no live rate API (none exists free, per the research audit) — using the rate bands the audit found ($60-95/hr agentic AI, $40-70/hr full-stack, geography-tiered). Internal/dashboard reference only; the writer's "never quote a price in the first message" rule is untouched. |

**Lesson worth keeping:** two separate research passes (the Phase 2 audit fork, then this
session's own check) both initially trusted `omkarcloud/google-maps-scraper`'s star count and
"active" status without checking whether the repo still contained code — a repo can look alive
(stars, recent README edits) while having quietly turned into pure marketing for a paid product.
Worth an actual `gh api repos/.../contents` check before depending on any "OSS tool" claim, not
just a description/star-count glance.

**Not done in this phase (still backlog):** wiring `suggest_rate()` into the writer/dashboard
(needs a clean signal for "is this an agentic-AI pitch" — the matched portfolio project's `type`
field looks like the right source, not built yet), embedding model swap, WhatsApp → Telegram,
APScheduler → plain cron entrypoint script, payments/tax tooling (research-only, needs a CA's
sign-off on the Section 44ADA point before anyone relies on it).

**Result:** 38 tests green (29 prior + 9 new: 1 Groq-fallback test added to `test_gemini.py`, 3 in
new `test_maps_source.py`, 5 in new `test_pricing.py`).

<!-- Next session: append "## Phase 4 — ..." here. Do not edit sections above. -->
