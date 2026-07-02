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

<!-- Next session: append "## Phase 2 — ..." here. Do not edit sections above. -->
