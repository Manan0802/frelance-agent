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

## Current status (2026-07-12)
- **Phase 1 (Engine B / outbound) = COMPLETE.**
- **Phase 1.5 (Engine A / inbound) = COMPLETE.**
- **Phase 2 (research-audit fixes + review dashboard) = COMPLETE.**
- **Phase 3 (resilience + missing pieces) = COMPLETE.**
- **Phase 4 (first live run + pricing wiring) = COMPLETE.**
- **Phase 5 (pricing symmetry for Engine A) = COMPLETE.**
- **Phase 6 (message quality / anti-hallucination) = COMPLETE.**
- **Phase 7 (two pitch angles) = COMPLETE.**
- **Phase 8 (portfolio-match relevance floor) = COMPLETE.**
- **Phase 9 (real portfolio data) = COMPLETE.**
- **Phase 10 (GitHub projects + WhatsApp kill switch + JSON parser fix) = COMPLETE.**
- **Phase 11 (capability-aware research + Engine A sources wired) = COMPLETE.** 88 tests green.
- **Engine A now fetches its own leads:** `backend/engine_a/sources.py::collect_jobs()` fans in
  HN-freelance + RemoteOK + WWR; `POST /run-inbound {}` (no body jobs) triggers a real fetch.
  A failing source is logged and skipped, never fatal.
- **Filter job boards on engagement model, NOT tech tags** — RemoteOK posters spray tags for reach
  (a live procurement job carried 45 tags incl. `python`, `data science`). Titles get a loose
  freelance/contract match; descriptions need an explicit phrase, since employment ads say
  "contract"/"consulting" incidentally. Live: 190 rows → 9, and what survives is genuinely
  contract work.
- **HN freelancer thread is ~1 lead/month**, not a pipeline — measured, the docs overstated it.
  ~85 of ~87 comments are `SEEKING WORK` (competitors advertising), not clients hiring.
- **`research_target()` takes the portfolio** and tells the model what Manan builds, so it hunts
  automation/AI openings instead of generic page-speed nitpicks that match no portfolio project.
- **`WHATSAPP_ENABLED=false` is set in `.env`** — live runs will NOT message Manan. Flip to `true`
  only when he asks; testing used to spam his phone.
- **All LLM JSON must go through `backend/llm/parse.py::parse_json()`** — Gemini fences its JSON in
  ```` ```json ````, and a bare `json.loads()` silently lost the payload (empty `pain_points`,
  which broke portfolio matching; and `score: 0`, which auto-rejected every job). Never add another
  bare `json.loads()` on an LLM response.
- **Test fakes were more polite than the real model** for ten phases and hid that bug. When faking
  an LLM boundary, make the fake emit the messy shape the real one does.
- **`data/portfolio_context.json` is now built from verified sources** (resume, github.com/Manan0802,
  manankumar.in), 8 real projects with real stacks and metrics. **Never add employer names, product
  names or job-role detail to it** — Manan's explicit rule; employer work appears as anonymous
  capability only. The file IS the enforcement: the writer can only cite what's in it.
  Project names are lookup keys (the dashboard resolves pricing tiers by matching stored
  `portfolio_used` strings) — **don't rename them**, and never put a comma in a name.
- **Relevance floor:** `matcher.MIN_SIMILARITY = 0.30` — measured, not guessed (genuine matches
  score 0.38-0.74 against the real portfolio, stretches/junk ≤0.19). `match_projects()` may return
  fewer than `top_k`, or **none**. **Re-measure the floor if the embedding model changes.**
  When nothing matches, both writers switch to `NO_PROJECT_RULES`: cite no project, name no tech.
  Prompt lesson learned the hard way — a late "name the tech you'd use" instruction overrides an
  earlier "don't"; delete the clause rather than trying to negate it.
- **Grounding rule (important):** `research_target()` returns `has_source` — whether a website was
  actually fetched. When false, the prompts forbid stating specifics (products, customers, history,
  setup), because Gemini will otherwise invent confident-sounding detail from just a name and
  category.
- **Two pitch angles (Phase 7) — both segments are good targets, they just need different offers:**
  - **No website** → the hook IS that absence ("searched, couldn't find your site") → offer to
    build it + optimise for Google/local search. Honest, concrete, needs no fabrication.
  - **Has website** → pitch from what was actually read off their site, and **never offer to build
    a website they already have**; offer what the cited past work supports.
  - Scoring splits too: no-website pitches are scored on **offer strength** (`OFFER_SCORE_PROMPT`),
    researched ones on **tailoring** (`SCORE_PROMPT`) — scoring the former on tailoring floors it
    at ~4/10 and makes the regen loop chase specifics that don't exist.
  - **Don't reduce this to "selling websites"** — for a business that has one, the pitch should
    reach for automation/AI/whatever the portfolio actually supports.
- Writers pass each portfolio project's real `tech` stack into the prompt via
  `writer.format_projects()` and forbid naming unlisted tech — without it the model invents
  stacks (once claimed "WordPress" for a React/Node project).
- **First live run done** — real Gemini + real WhatsApp digest confirmed delivered. `.env` is
  filled and is its own standalone file (no longer shared/symlinked with Manan's other projects).
- Engine B: ingest local-business targets (manual, or `backend/engine_b/maps_source.py` via a
  locally-run gosom/google-maps-scraper) → research (site + Gemini) → portfolio match
  (embeddings) → write message (self-eval regen) → WhatsApp digest (green-api) → review API
  → approve + CRM log.
- Engine A: fetch jobs (RemoteOK / WWR RSS / JobSpy) → LLM score + auto-reject → portfolio
  match → inbound proposal (self-eval regen) → WhatsApp digest → `/run-inbound` API.
- **Review dashboard:** `GET /dashboard` (htmx + Jinja2, no separate frontend) — every drafted
  message/proposal as a card with score, status, an in-place Approve button, and (for outbound
  messages) a live-computed pricing suggestion.
- LLM: Gemini via the `google-genai` SDK (the old `google-generativeai` package is fully
  deprecated), default model `gemini-2.0-flash-lite`, **Groq fallback on any Gemini error**.
- **Pricing:** `backend/pricing/suggest.py::suggest_rate()` — deterministic rate-band suggestion
  (no LLM, no live API); wired into the dashboard for **both** outbound messages (single
  geography-tiered band, from the target's location) and inbound proposals (**both** bands shown,
  since `JobLead` has no location — see BUILD_LOG Phase 5 for why not defaulting to the lower
  tier). Never injected into outreach/proposal text itself (writer's "never quote a price" rule stays).
- **No migration tool** (no Alembic). Schema changes so far are hand-applied additive `ALTER TABLE`
  on `data/freelancing_agent.db` — `create_all()` only creates missing tables, never adds columns
  to existing ones. Wire up Alembic if schema churn increases.
- Security: SSRF guard on website fetch; optional API-key gate + batch cap on APIs.
- Tests isolated via `tests/conftest.py` — **own DB file** (`data/test_freelancing_agent.db`),
  separate from the dev/live DB (they used to share one file; the test fixture's drop-all was
  silently wiping live data on every `pytest` run — fixed 2026-07-12).
- **Environment note:** built/tested on macOS this session — venv at `./venv/bin/python`, not
  the `./venv/Scripts/python.exe` this file used to assume. Update your own commands accordingly.
- Git: current branch is `phase1-engine-b`, pushed to `origin` (per-folder git identity routing:
  anything under `~/Desktop/manan/` pushes as `Manan0802` via a `~/.gitconfig` `includeIf` block
  Manan set up himself — never touch this yourself, it's outside this repo).
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
