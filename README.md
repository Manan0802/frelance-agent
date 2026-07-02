# Freelancing Agent

Personal AI **freelance client-acquisition** system for Manan (AI engineer, New Delhi).
Finds good-rate freelance clients, drafts personalized outreach, tracks the pipeline.
**Human always approves + sends manually — never auto-send.**

> **Scope:** freelance / project-based clients only. Full-time job-hunting is a separate agent — out of scope here.

## Status (2026-07-02)
- **Engine B (outbound)** ✅ — local business → research → portfolio-matched message → WhatsApp digest → review → CRM.
- **Engine A (inbound gigs)** ✅ — fetch gigs → LLM score → proposal → digest. (Source priority pivoting to freelance-first.)
- **23 tests green.** Not yet run live (needs `.env` + real data).

## Quick start
```bash
python -m venv venv
./venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
./venv/Scripts/python.exe -m pytest -q                          # expect 23 passed
cp .env.example .env                                            # then fill keys
```
Run the API: `./venv/Scripts/python.exe -m uvicorn backend.main:app --reload`

## Where to resume — read these first
1. `CLAUDE.md` — scope, strategy, dev workflow, next steps (auto-loaded by Claude Code).
2. `docs/BUILD_LOG.md` — append-only phase history (what/why/how each phase was built).
3. `docs/PLATFORM_COVERAGE.md` — platform vision + add-a-platform checklist.
4. `docs/research/FREELANCE_PLATFORMS.md` + `INSIDER_SOURCES.md` — where the clients are.
5. `docs/superpowers/specs/` (design) + `docs/superpowers/plans/` (step-by-step).

## Layout
```
backend/
  engine_b/   outbound (targets → research → match → write → notify)
  engine_a/   inbound gigs (fetch → score → proposal → notify)
  portfolio/  portfolio_context.json loader (the shared "brain")
  notify/     green-api WhatsApp digest
  api/        FastAPI routes (/run, /run-inbound, /messages, /approve)
data/portfolio_context.json   Manan's skills + projects
tests/        pytest (all boundaries dependency-injected; no network in tests)
```

## Rules
Never auto-send · no mass spam · data local-only except LLM calls · TDD, commit per task, push to `main`.
Every phase: append to `docs/BUILD_LOG.md` (never edit old entries) + keep docs aligned.
