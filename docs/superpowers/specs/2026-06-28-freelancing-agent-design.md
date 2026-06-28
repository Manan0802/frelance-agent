# Freelancing Agent — Design Spec v1

**Owner:** Manan · **Date:** 2026-06-28 · **Status:** Draft for review
**Supersedes/refines:** `FREELANCING_AGENT_PRD.md` (the original PRD remains the vision doc; this is the optimized, research-backed build design)

---

## 1. North Star (revised from clarifications)

Steady flow of **serious, good-rate clients** + ability to **manage the work** + a system that **genuinely understands the whole pipeline**. Quality + rate over feature count.

**Operating reality that shapes everything:**
- Cold start: real skills + genuine portfolio (SARA@IndiaMART, InvestMate, ShopLens, Bachatt, client sites) but **zero freelance-platform reputation**.
- Edge: **production AI-agent engineering** (premium positioning) + fast full-stack/website delivery (volume).
- Budget: ~₹500–1500/mo. Free + open-source first.
- Hard rule (from PRD, kept): **never auto-send.** Agent drafts; Manan reviews + sends.

---

## 2. The core architectural decision: TWO engines, not one

The PRD assumed one engine (scan job boards → propose). For a cold-start dev that under-converts because platforms gatekeep by reputation. We run **two engines** sharing one brain (portfolio context) and one cockpit (dashboard + notifications).

### Engine A — Inbound / Bidding
- **Sources:** JobSpy aggregation (Indeed/LinkedIn/Glassdoor/Google), RemoteOK, We Work Remotely, Upwork RSS, Contra/Wellfound (work-sample channels).
- **Flow:** fetch → dedupe → auto-reject → score → personalized proposal → digest.
- **Why:** work-sample channels judge skill not platform badge; still worth proposals where reputation matters less.

### Engine B — Outbound / Direct (the cold-start unlock)
- **Sources:** Google Maps scraper (local businesses with bad/no sites), targeted startup/SMB lists (AI-automation need).
- **Flow:** find target → enrich (decision-maker + email) → deep research (site/LinkedIn/news/pain) → hyper-personalized first message → digest.
- **Why:** **no platform gatekeeper.** Clients judge the work + the pitch. Highest near-term conversion for Manan.

Both engines converge into: **Scorer/Qualifier → Writer → Pricing → Notification (Telegram) → Dashboard review → CRM/Tracker → Follow-ups.**

---

## 3. Fork-vs-Build map (the build philosophy: leverage + customize + fill gaps)

| Component | Decision | Source | Customization we own |
|---|---|---|---|
| Job aggregation (inbound) | USE | `JobSpy` | config + filters |
| RemoteOK / WWR fetch | BUILD (thin) | ~30 lines each | — |
| Local-biz finder (outbound) | USE | `omkarcloud/google-maps-scraper` | query lists, output mapping |
| Scorer / qualifier | FORK + MODIFY | `kaymen99/Upwork-AI-jobs-applier` | our weights, auto-reject rules, portfolio match |
| Inbound proposal writer | FORK + MODIFY | same repo | our 10 proposal rules, voice, RAG |
| Outbound research + message | FORK + MODIFY | `kaymen99/sales-outreach-automation-langgraph` | our segments, message templates |
| Portfolio match (RAG) | BUILD | sentence-transformers + ChromaDB | core to our edge |
| Pricing agent | BUILD | 1 LLM call + rate tree | our rate logic |
| CRM / tracker | BUILD | own SQLite | lifecycle states |
| Orchestrator | FORK pattern → BUILD | kaymen99 LangGraph node patterns | our two-engine StateGraph |
| Dashboard | BUILD | React + Vite (minimal first) | review cockpit |
| Glue / scheduling | BUILD (Python) | APScheduler | not n8n (dev-owned control) |
| Scraping resilience | USE (targeted) | `camofox-browser` | only protected-site slices |
| Reply triage | BUILD (pattern from CF agentic-inbox) | Gmail API + Gemini | Phase 1.5 |

Full tool inventory (nothing discarded, all tiered): see `docs/research/TOOL_REGISTRY.md`.

---

## 4. Tech stack (revised from PRD)

**Kept from PRD:** LangGraph, FastAPI, SQLite→Supabase, SQLAlchemy+Alembic, APScheduler, Pydantic v2, httpx, feedparser, sentence-transformers, ChromaDB, React+Vite+Tailwind+shadcn, Zustand, React Query.

**Changed / decided:**
- **LLM:** Gemini (Flash/Pro) primary — matches kaymen99 outbound repo + Manan's existing usage. Groq (Llama 3.3 70B) fallback. (PRD had these reversed; aligning primary with the fork to reduce porting.)
- **Notifications:** **WhatsApp via green-api** (third-party REST, free tier) replaces Twilio WhatsApp. Pure-Python HTTP, full free-form digests (no template/session limits), QR-link Manan's WhatsApp once. Email (Gmail SMTP) as second channel. Fallback: dashboard in-app. *(Notifications are self-only — no client spam — so unofficial-API ban risk is negligible.)*
- **Scraping:** Playwright default; **Camoufox** only for bot-protected targets.
- **Glue:** Python/APScheduler, not n8n (keep control in code; n8n parked in REFERENCE).

---

## 5. Components (isolation boundaries)

Each unit = one purpose, clear interface, independently testable.

1. **Sources** (`agents/lead_finder/*`) — per-platform fetchers returning a common `RawLead`. Engine A + B sources are siblings.
2. **Dedup** (`utils/deduplication.py`) — SHA256(title+client+platform), 7-day window, cross-platform.
3. **Scorer** (`agents/scorer/*`) — auto-reject filter + LLM scoring + red-flag detection → `ScoredLead`.
4. **Portfolio matcher** (`agents/proposal_writer/portfolio_matcher.py`) — embed job vs portfolio projects, top-2.
5. **Writer** (`agents/proposal_writer/*`) — inbound proposal / outbound message, rules + RAG + self-eval (regen if personalization < 7/10).
6. **Pricing** (`agents/pricing/*`) — rate tree → suggestion + floor + positioning.
7. **CRM** (`agents/crm/*`) — lifecycle state machine + follow-up scheduler.
8. **Notifier** (`agents/notifier/*`) — Telegram + email; fallback to dashboard.
9. **Orchestrator** (`agents/orchestrator.py`) — two-engine LangGraph StateGraph.
10. **API + Dashboard** — FastAPI endpoints + React review cockpit.

Data models: per PRD §6 (leads, scored_leads, proposals, crm_records, notifications, agent_runs), plus an `outbound_targets` table for Engine B.

---

## 6. Daily flow (end-to-end)

`09:00 scheduler → Engine A (job sources) + Engine B (target research) in parallel → dedupe → auto-reject → score → top N → write (proposal/message) → price → Telegram + email digest → Manan reviews dashboard (≤20 min) → approve/edit/skip → manual send → CRM logs + schedules follow-up → throughout day: reply alerts + follow-up reminders.`

---

## 7. Phasing (sequenced for "first good-rate client fast")

- **Phase 1 (lean money-maker):** Engine B slice — Maps scraper → enrich → research+message (fork kaymen99) → Telegram digest → review → CRM log. + Portfolio context JSON. **Goal: land first client.**
- **Phase 1.5:** Engine A (JobSpy + RemoteOK/WWR + scorer + proposal writer), dashboard, reply triage (agentic-inbox pattern).
- **Phase 2:** ops stack as needed (Cal.com, invoicing, contracts, PM), grow-presence content engine, camoufox-backed LinkedIn/Contra, follow-up automation, pricing self-tuning.

(Detailed task breakdown → implementation plan, next step.)

---

## 8. Decisions (confirmed)

1. **Fork-vs-Build map (§3)** — ✅ approved as-is.
2. **Notifications** — ✅ WhatsApp via **green-api** (not Telegram, not Twilio). See §4.
3. **Phase 1 = Engine B (outbound/local) first** — ✅ approved.

---

## 9. Constraints & risks (kept from PRD, updated)

- Never auto-send. No mass spam (kills Listmonk/Mautic for Phase 1). Data local-only except LLM calls (no PII).
- Scraper fragility → JobSpy + Maps + outbound reduce dependence on beating bot-walls; Camoufox for the rest.
- Cold-start lead quality → tune scoring on real data after week 1.
- LLM hallucination in proposals → self-eval + regen loop.
