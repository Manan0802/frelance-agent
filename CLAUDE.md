# CLAUDE.md — Freelancing Agent (project context for Claude Code)

Personal AI client-acquisition system for Manan (AI engineer, New Delhi). Finds good-rate
clients, drafts personalized outreach, tracks pipeline. **Human always approves + sends
manually — never auto-send.**

## SCOPE (read first — don't drift)
**This project = FREELANCE / project-based clients only.** People/businesses who need a project
built and pay per-project. **Job-hunting (full-time/employment) is OUT OF SCOPE** — Manan has a
separate job agent for that. So prioritize **freelance-gig + direct-client** sources (Upwork,
Freelancer.com, PeoplePerHour, Contra, Fiverr, HN "freelancer seeking freelancer", Reddit `[Hiring]`
gigs, X gig requests, local-business outbound). Pure employment job boards (Indeed/LinkedIn-jobs/
RemoteOK/WWR full-time listings) are **deprioritized** — only use their contract/freelance slices, if at all.

## Current status (2026-07-08)
- **Phase 1 (Engine B / outbound) = COMPLETE.**
- **Phase 1.5 (Engine A / inbound) = COMPLETE.**
- **Phase 2 (research-audit fixes + review dashboard) = COMPLETE.**
- **Phase 3 (resilience + missing pieces) = COMPLETE.** 38 tests green total.
- Engine B: ingest local-business targets (manual, or `backend/engine_b/maps_source.py` via a
  locally-run gosom/google-maps-scraper) → research (site + Gemini) → portfolio match
  (embeddings) → write message (self-eval regen) → WhatsApp digest (green-api) → review API
  → approve + CRM log.
- Engine A: fetch jobs (RemoteOK / WWR RSS / JobSpy) → LLM score + auto-reject → portfolio
  match → inbound proposal (self-eval regen) → WhatsApp digest → `/run-inbound` API.
- **Review dashboard:** `GET /dashboard` (htmx + Jinja2, no separate frontend) — every drafted
  message/proposal as a card with score, status, and an in-place Approve button.
- LLM: Gemini via the `google-genai` SDK (the old `google-generativeai` package is fully
  deprecated), default model `gemini-2.0-flash-lite`, **Groq fallback on any Gemini error**.
- **Pricing:** `backend/pricing/suggest.py::suggest_rate()` — deterministic rate-band suggestion
  (no LLM, no live API), internal/dashboard reference only, not wired into the writer yet.
- Security: SSRF guard on website fetch; optional API-key gate + batch cap on APIs.
- Tests isolated via `tests/conftest.py` (drop+create schema per test).
- **Environment note:** built/tested on macOS this session — venv at `./venv/bin/python`, not
  the `./venv/Scripts/python.exe` this file used to assume. Update your own commands accordingly.
- Git: current branch is `phase1-engine-b` (this doc previously said `main` — flagging the
  mismatch rather than silently merging/switching; confirm with Manan before assuming either).
- **NOT yet run live** — needs `.env` filled + real data. First live run is next.
- See `docs/BUILD_LOG.md` Phase 2 entry for the full research-audit-driven changelist (doc
  corrections, Gemini SDK migration, dashboard) and what's still backlog (pricing agent,
  payments/tax tooling, embedding swap, WhatsApp→Telegram reconsideration, cron simplification).

## Read these first
- `docs/BUILD_LOG.md` — **append-only phase history** (what/why/how each phase was built). Read this
  to understand everything done so far. **After finishing any phase, APPEND a new section — never
  edit/delete old ones.** This is how we keep full context so nothing goes missing as we advance.
- `docs/superpowers/specs/2026-06-28-freelancing-agent-design.md` — the design + two-engine strategy
- `docs/superpowers/plans/2026-06-28-phase1-engine-b.md` — the executed Phase-1 plan
- `docs/PLATFORM_COVERAGE.md` — vision (volume + quality, national + international), which platforms
  are covered now vs planned, and the "add-a-platform" checklist. Goal = reach many platforms.
- `docs/research/FREELANCE_PLATFORMS.md` — 70+ freelance platforms catalog, tiered by fit + access
- `docs/research/INSIDER_SOURCES.md` — hidden-gig channels (HN "who's hiring", Reddit, X) + how to monitor
- `docs/research/TOOL_REGISTRY.md` — every evaluated open-source tool, tiered (nothing discarded)
- `FREELANCING_AGENT_PRD.md` — original vision doc

## Strategy (don't lose this)
- Manan is cold-start: real skills + portfolio, **zero platform reputation**. So **outbound/direct
  (Engine B) converts better than platform bidding** right now.
- Two engines share one brain (`data/portfolio_context.json`) + one cockpit (dashboard + WhatsApp).
  - Engine A (inbound/bid): JobSpy + job boards → scorer → proposal writer. **Phase 1.5.**
  - Engine B (outbound): Maps scraper → research → personalized message. **DONE.**
- Fork bases: `kaymen99/Upwork-AI-jobs-applier` (Engine A), `kaymen99/sales-outreach-automation-langgraph` (Engine B). Same stack (LangGraph + Gemini).
- Budget tiny (~₹500-1500/mo): free + open-source first. Gemini primary, Groq fallback (1.5+).

## Dev workflow (follow exactly)
- Windows, Python 3.13, venv at `./venv`. Run python via `./venv/Scripts/python.exe`.
- Tests: `./venv/Scripts/python.exe -m pytest -q` (must be green before any commit).
- **TDD, one task at a time:** write failing test → run (see it fail) → minimal code → run (green) → commit.
- **Commit per task**, then `git push origin main`. Never push red tests.
- Install deps incrementally per task (heavy ones like torch only when needed).
- All LLM/HTTP boundaries are dependency-injected so tests never hit the network.
- Secrets in `.env` (gitignored) — never commit keys. Copy from `.env.example`.

## Next up (Phase 2)
1. **First live run:** fill `.env` (GEMINI_API_KEY, GREENAPI_ID/TOKEN, MANAN_WHATSAPP),
   feed real Delhi businesses (omkarcloud maps) → Engine B; real job tags → Engine A →
   real WhatsApp digest. (Manan does this next week on his device.)
2. **React dashboard** (review cockpit): lead cards, proposal editor, approve/skip, CRM board.
3. **APScheduler daily cron** — one entrypoint that runs both engines each morning.
4. **Reply-triage** (agentic-inbox pattern) via Gmail API + Gemini.
5. Camoufox for protected scrapes; Groq fallback; enrichment (Bricks).

## Constraints
Never auto-send. No mass spam. Data local-only except LLM calls (no PII). Quality > quantity.
