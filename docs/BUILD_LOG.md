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

## Phase 4 — First Live Run + Pricing Wiring (2026-07-12)

**Goal:** first real live run with actual API keys, and wire the Phase 3 pricing module into
something Manan can actually see.

**`.env` filled and de-shared:** it used to be a symlink into a `../claude-transfer/.env` shared
across ~4 of Manan's projects, which would have collided its `GROQ_API_KEY` with a different
project's. Manan wants every project's secrets fully separate — symlink removed, `freea` now has
its own standalone `.env` with Gemini/Groq/green-api/WhatsApp keys filled in.

**GitHub push unblocked:** the machine's default `gh`/git identity (`manankumar-ai`) doesn't have
write access to `Manan0802/frelance-agent`. Manan set up per-folder git identity routing himself
(`~/.gitconfig` `includeIf "gitdir:~/Desktop/manan/"` → a separate credential store for
`Manan0802`) — any repo under `~/Desktop/manan/` now pushes as Manan0802 automatically, everything
else on the machine still uses the default. Confirmed working; all prior local-only commits
pushed.

**First live run:** `/run` called for real against Gemini + green-api WhatsApp — draft generated,
digest delivered and confirmed received on Manan's phone. Minor content-quality note: the LLM
invented a tech stack ("WordPress") not present in the matched portfolio project's actual data —
worth watching, not fixed this round.

**How built (TDD):**

| Task | File(s) | What it does |
|---|---|---|
| 1 | `tests/conftest.py` | **Bug found via this session's own live run:** tests and the dev server both defaulted to the same sqlite file (`data/freelancing_agent.db`); the autouse fixture drops+recreates all tables before every test, which silently wiped real dev data on every `pytest` run (it wiped the live run's own test message). Tests now use `data/test_freelancing_agent.db` instead. |
| 2 | `backend/api/dashboard.py`, `backend/templates/partials/message_row.html`, `backend/static/dashboard.css`, `tests/test_dashboard.py` | Wires `suggest_rate()` into outbound message cards — `is_agentic` derived from whether the message's stored `portfolio_used` project names include an `ai_ml`-typed portfolio project, `client_geography` from the target's location. Computed live at render time (no schema change, nothing persisted, never injected into the draft text). Verified against real Gemini output on the live server. |

**Not done (still backlog):** same pricing wiring for Engine A proposals — `InboundProposal` has
no `portfolio_used` column to derive `is_agentic` from, would need a small schema addition first.
Also still open: embedding model swap, WhatsApp→Telegram, cron entrypoint script, Freelancer.com
API source, reply-triage, CRM follow-up scheduling.

**Result:** 40 tests green (38 prior + 2 new dashboard pricing tests; conftest fix touches no test
count, just isolates the DB).

## Phase 5 — Pricing Symmetry for Engine A (2026-07-15)

**Goal:** close the gap Phase 4 left open — inbound proposals had no pricing suggestion because
`InboundProposal` had no way to tell whether the pitch was agentic-AI or full-stack work.

**How built (TDD):**

| Task | File(s) | What it does |
|---|---|---|
| 1 | `backend/engine_a/proposal.py`, `backend/database/models.py`, `backend/engine_a/graph.py` | `write_proposal()` now returns `portfolio_used` (mirroring `engine_b/writer.py`'s contract), and `InboundProposal` gained a `portfolio_used` column to persist it. Three test fakes updated to match the real contract — Engine B's equivalents already included this field, so this is the two engines converging rather than a new pattern. |
| 2 | `backend/api/dashboard.py`, `backend/templates/partials/proposal_row.html` | Proposal cards now carry a pricing suggestion, derived the same way as outbound (matched project's `type == "ai_ml"` → agentic band). |

**Design decision worth keeping:** outbound targets have a `location`, so their card shows one
geography-adjusted band. `JobLead` has **no location field at all** — so for proposals there is
genuinely no geography to tier on. Defaulting to the lower "other" tier (0.6x) would have
systematically under-priced the international remote gigs RemoteOK/WWR/JobSpy mostly carry —
a silent, harmful default. Instead proposal cards show **both** bands with "geography unknown —
check the posting" stated on the card. If a location field is ever added to `JobLead`, this can
collapse to the single-band treatment outbound already uses.

**Schema migration note:** the dev DB predated the new column, and `create_all()` only creates
missing *tables*, never adds columns. Applied an additive `ALTER TABLE inbound_proposals ADD
COLUMN portfolio_used TEXT DEFAULT ''` — non-destructive, verified row counts unchanged before
and after (`inbound_proposals` was empty; `outreach_messages`/`outbound_targets` rows untouched).
**This project has no migration tool** (Alembic was in the PRD's stack list but never set up) —
fine at one-column-every-few-phases, but if schema churn picks up, wire up Alembic rather than
hand-writing more ALTERs.

**Result:** 41 tests green (40 prior + 1 new). Verified the rendered HTML on a running server with
a temporary seeded proposal (since the tests assert figures, not entity rendering), then removed
the seed and confirmed the DB was back to its prior state.

## Phase 6 — Message Quality / Anti-Hallucination (2026-07-15)

**Goal (Manan's steer):** automation/cron is NOT the priority — lead *quality* is. "Even 2 leads,
I'll call them manually." So this phase attacks pitch honesty and quality signal, not volume.

**Three chained findings, each surfaced by an actual live run rather than by tests:**

**1. The writer invented tech stacks.** A live run produced "using WordPress" while citing a
project whose real stack is React/Node. Root cause: `_draft()` only ever passed
`"{name}: {description}"` per project — the portfolio's `tech` field was **never in the prompt** —
while `RULES` simultaneously ordered the model to "name the tech you'd use". With no grounding it
had to invent one. Fixed with a shared `format_projects()` (in `writer.py`, imported by
`proposal.py` alongside the existing `_score` import) that includes each project's real stack,
plus an explicit rule against naming unlisted tech. Verified live: now cites "React and Node.js"
for CodewellImages, matching the portfolio exactly.

**2. The self-eval scorer was uselessly generous.** It scored 8/10 a message whose only
"personalization" was restating the city we had fed it ("I noticed you're based in Karol Bagh").
Because the regen gate is `score < 7`, it effectively never fired — the quality loop was dead
weight. `SCORE_PROMPT` is now an explicit rubric that names what does **not** count (restating
known facts, generic claims any competitor could receive, flattery) with a 0-3/4-6/7-8/9-10 band
description.

**3. Fixing (2) made hallucination worse — the important one.** Now rewarded for specificity but
still given no real data, the writer invented *"popular items like gulab jamun"* for a sweet shop
it knew nothing about. Investigation showed the real culprit: `research_target()` returns
confident-sounding output **whether or not anything was actually fetched**. For a business with no
website, Gemini writes a plausible research summary from just name/category/location — pure
speculation, indistinguishable downstream from real research.

Fix: `research_target()` now returns `has_source` (did the fetch actually yield content), and both
the research prompt and the writer prompt are explicitly constrained when it's false — state
nothing about products, customers, history, or current setup. A believable-sounding guess that
turns out wrong loses the client outright.

**Verified live:** a no-website target now produces hedged copy with zero invented specifics, and
honestly scores **4/10 instead of a false 8/10**.

**Strategic consequence worth acting on:** a target with no website cannot be genuinely
personalized — there is nothing to research — and the score now says so honestly. For the
"few high-quality leads worth calling" goal, prefer targets that **have** a website (the Maps
fetcher already returns a `website` field), since those are the only ones that yield real research
material. Consider filtering or ranking on this before scaling volume.

**Result:** 47 tests green (41 prior + 6 new: 2 writer-grounding/rubric, 4 in new
`test_research_grounding.py`).

## Phase 7 — Two Pitch Angles (2026-07-15)

**Corrects a wrong conclusion from Phase 6.** Phase 6 ended by recommending Manan *prefer targets
that have websites*, on the logic that no-website businesses can't be researched and therefore
can't be personalised. Manan pushed back, and he was right:

> "jinka website nahi unko aise toh pitch karte hain — maine bahut dhunda nahi mila, hum aise
> developer hain, itne mein aapki website bana denge, aur bonus mein bold denge Google search ke
> hisaab se optimize... aur jinka hai unko aur sahi se target karenge. Khali website thodi bechni
> humne."

The missing website **is** the verified fact, and it makes a concrete honest offer — no fabrication
required. The Phase 6 framing confused "nothing to research" with "not worth pitching".

**What changed:**

| Segment | Angle |
|---|---|
| No website | Lead with the hook: searched, couldn't find a site → offer to build it + the bonus of optimising it for Google/local search. Still explicitly forbidden from inventing anything else about the business. |
| Has website | Pitch from what was genuinely read off their site. **Explicitly told NOT to offer to build a website they already have** — instead offer what the cited past work actually supports (automation, an AI assistant, ordering, search visibility). |

**Scoring split with it.** The Phase 6 strict tailoring rubric is right for researched leads but
wrong for no-website ones: with nothing real to be specific about, it floored them at ~4/10 and
sent the regen loop chasing specifics that don't exist. `OFFER_SCORE_PROMPT` now judges those on
offer strength instead — concrete deliverable, the search-visibility bonus made concrete, credible
proof, clear ask — and `_score()` takes `has_source` to pick the rubric.

**Verified live on both paths:**
- No website → *"I couldn't find a website for Bansal Mithai Ghar... built with React and Node.js,
  like CodewellImages... visible in Google searches for Pitampura, Delhi"* — **7.0**, up from 4.0,
  with zero invented business detail.
- Real site fetched → *"Slow image loading... I noticed multiple image sizes and formats... with a
  visual search engine like ShopLens, built using CLIP, FAISS, and Python"* — no website rebuild
  offered, and it reached for a **different portfolio project**, which is the point: the system
  isn't just selling websites.

**Loose thread worth a look:** in that second example the match is a bit of a stretch — ShopLens is
visual *search*, pitched here for image *optimisation*. The matcher picked it on image-related
similarity and the writer papered over the gap. Worth watching whether portfolio matching needs a
relevance floor.

**Result:** 51 tests green (47 prior + 4 new in `test_pitch_angles.py`; one Phase 6 test updated
to assert intent rather than the old prompt's exact wording).

## Phase 8 — Portfolio-Match Relevance Floor (2026-07-16)

**Goal:** close the loose thread Phase 7 flagged — `match_projects()` always returned `top_k`
projects regardless of similarity, so the least-bad project got cited however irrelevant it was.
The live example: ShopLens (a visual *search* project, CLIP/FAISS) pitched as a fix for image
*optimisation*.

**Threshold chosen from measurement, not intuition.** Ran the real embedder
(`all-MiniLM-L6-v2`) against the real portfolio with representative need-texts:

| Need | Best score |
|---|---|
| AI agent → SARA | 0.537 |
| Website → CodewellImages | 0.514 |
| Fintech → InvestMate | 0.744 |
| Generic pain → CodewellImages (weakest genuine) | 0.381 |
| **Image-optimisation → ShopLens (the stretch)** | **0.189** |
| Unrelated legal query | 0.187 |
| Unrelated plumbing query | 0.082 |

Genuine matches and junk occupy non-overlapping bands with an empty gap between 0.189 and 0.381,
so `MIN_SIMILARITY = 0.30` sits in that gap with margin on both sides. **Re-measure if the
embedding model is ever swapped** (the audit floated `gemini-embedding-001`) — cosine
distributions are not comparable across models.

**The floor exposed two fabrication holes, both caught by live runs, not tests:**

1. With an empty project list, `format_projects([])` returned `""` while `RULES` still ordered
   "mention one relevant past project" — so the model invented a citation. Fixed: the empty case
   now states explicitly that nothing matched and forbids inventing one.

2. Even then, a live run emitted *"Using Next.js, I can help"* with no project cited. Cause: the
   prohibition sat in the `{projects}` slot **early** in the prompt, while `RULES`' "name the tech
   you'd use" is the **last and most direct** instruction — recency won. **Negating the instruction
   did not work; removing it did.** Both engines now select conditional rules (`NO_PROJECT_RULES`)
   when no project matched. Worth remembering as a general prompt lesson: don't try to override a
   later instruction from an earlier position, delete the later one.

**Verified live on the original stretch case:** now cites no project, names no tech, and pitches
from what was genuinely read off the site ("numerous preloaded scripts and images").

**Honest tradeoff this creates, worth a decision:** a no-match message is now plainer — no proof,
no tech named. `data/portfolio_context.json` carries a `skills` list (React, Next.js, FastAPI,
LangGraph, …) that is **real, verified data the writer has never been given** — it only ever sees
project descriptions. Feeding skills in would let these messages truthfully say "I work with
Next.js" instead of saying nothing. Left undone deliberately: it changes `write_message()`'s
signature across both engines, and whether to pitch tech Manan knows but has no listed project for
is his call, not a silent refactor.

**Result:** 57 tests green (51 prior + 6 in new `test_match_relevance.py`).

## Phase 9 — Real Portfolio Data (2026-07-21)

**Trigger:** Phase 8 ended asking whether the writer should be allowed to name skills Manan has but
has no listed project for. He answered better than the question deserved — he handed over the
source material: his resume (`Manan_Kumar_Tech.pdf`), `github.com/Manan0802`, and
`manankumar.in`. Ground the file in real data instead of deciding how much to let it guess.

**Manan's constraint on employer work (important, keep):** capability may be cited, but
**no employer name, product name, or job-role detail** ("company ka naam... ya main jo karta hoon,
yeh nahi aana chahiye"). Enforced structurally rather than by prompt instruction: those identifiers
simply aren't in `portfolio_context.json`, and the writer can only cite what it's given. There's a
leak check in the session log; re-run something like it if this file is ever edited.

**Corrections found by cross-checking the three sources:**

1. **`Bachatt` was listed as a personal project — it is his employer.** The file described it as
   "Personal finance platform using Sarvam-2B…" with a live URL. Pitching an employer's product as
   personal portfolio work to freelance clients is a real credibility and employment risk. Now
   present only as an anonymous capability entry ("Voice AI Advisor"). `SARA` had the same problem
   in milder form — its description named the internship employer; removed.
2. **`manankumar.in` lists InvestMate's stack as Python/FastAPI/PostgreSQL** — but the repo is
   100% JavaScript and the resume says MERN. Used MERN here. **His own website still carries the
   wrong stack; flagged to him to fix there.**
3. ShopLens was missing YOLO and Streamlit; several skills were missing or stale (the old file
   listed FinBERT, Pinecone, ChromaDB, Docker, Supabase, Playwright — none of which appear in the
   resume; kept them out rather than assert them).

**Added three real projects that were absent entirely:** NeoFin (MERN + Gemini 2.5 Flash PWA,
live), Crop Yield Predictor, Skills Dashboard. Portfolio went 5 → 8 projects, and metrics from the
resume (100+ users, sub-70ms updates, 40,000+ indexed items, R²=0.91) are now available as concrete
proof in pitches.

**Two implementation details worth not re-learning:**
- All four live URLs were verified reachable before inclusion — these get sent to clients.
- **Project names were kept short and unchanged where they already existed.** The dashboard resolves
  pricing tiers by looking up stored `portfolio_used` name strings against the portfolio, so
  renaming a project silently breaks tier resolution for messages already in the DB. Tests caught
  this. Also: `portfolio_used` is comma-joined then split, so a project name containing a comma
  would corrupt it — there's an assert guarding that now.

**Live-verified improvement (no-website angle):** *"I was looking for Aggarwal Sweets online but
couldn't find a website. I'd like to build one for you using React.js and Node.js, similar to the
site I built for CodewellImages. This would optimize your shop for Google search in Rohini, Delhi."*
— **8/10**, every claim true. Compare Phase 6's 4/10 hedge and Phase 7's 7/10.

**Open finding for next phase — the research step doesn't know what Manan can do.** A has-website
lead (a diagnostics site) produced research pain-points about *page-load speed and image
optimisation* — generic web-dev observations. Nothing in the portfolio matches that, so the
relevance floor correctly returned nothing and the message came out proof-less and weak.
`RESEARCH_PROMPT` asks for "concrete problems a web/AI dev could fix" without ever being told what
**this** dev actually builds, so it fixates on surface technical issues instead of the automation /
AI-assistant / RAG problems Manan is strongest at. Feeding his capability areas into the research
prompt is likely the single highest-leverage next fix for the has-website angle.

**Result:** 57 tests green (unchanged — this phase changed data, not behaviour; two tests did catch
the rename regression before it shipped).

## Phase 10 — GitHub Projects, WhatsApp Kill Switch, and a Serious Parser Bug (2026-07-21)

**Three things, one of them significant.**

**1. WhatsApp kill switch (`WHATSAPP_ENABLED`).** Manan asked to stop receiving messages —
every live pipeline run fires a real digest at his phone, *including the ones run while
developing*, so the testing in Phases 6-9 had been messaging him repeatedly. `send_whatsapp()` now
returns `False` without posting when the flag is off. Set false in his `.env`; `.env.example` keeps
`true`. Also made `test_send_posts_to_greenapi` set the flag explicitly, so the suite no longer
depends on the developer's local `.env`.

**2. GitHub projects added (8 → 15).** Went through all 30 repos at `github.com/Manan0802`.
Added: Job Search Agent, AI Content Agent, Freelance Outreach Agent (this repo), NexTrade,
6D Pose Estimation, Event Booking Platform, and an anonymous **Knowledge Compiler Agent** entry.

Roughly a third of the repos — `LLM-Wiki-category-wiki-Multi-agent`, `category-wiki`,
`Multiagent-system-Langraph` (M-CASS), `LLMwiki-Multiusecase`, `multi-agent`, `api-deployGCP`,
`Sara-fullautonmous-specs-audit-agent` — are **employer work** (B2B seller specs, catalog
normalisation, Indian B2B marketplace; they map directly onto the resume's internship bullets).
Per Manan's rule none are named or linked; that capability appears only as the anonymised
Knowledge Compiler Agent entry, leak-checked against employer/product/role names.

**3. The parser bug — the important one.** A has-website lead produced *no portfolio match* even
with 15 projects. Investigating the stored row showed why: `pain_points` was an **empty string**,
and `research_summary` contained the raw LLM response *including* ```` ```json ```` fences.

Gemini wraps JSON in fences. `json.loads()` raises on that, and both callers swallowed the error
into a fallback:

- `research_target()` dumped the whole raw string into `research_summary` and left `pain_points`
  empty. **`pain_points` is exactly what the matcher matches on** (`graph.py`:
  `match(r.get("pain_points") or target.name, ...)`), so researched leads were being matched on the
  *business name* — which is the real reason has-website leads kept returning no portfolio match
  through Phases 8-9. The writer never saw the pain either.
- `score_job()` fell back to `score: 0`, below `REJECT_THRESHOLD` (40) — so a fenced response
  **auto-rejected the job outright**. Engine A could have been silently rejecting everything.

Both now use a shared `backend/llm/parse.py::parse_json()`, which tries the raw text, any fenced
block, and the outermost `{...}` span before giving up. Verified live: `pain_points` populates
correctly and no fences survive into storage.

**Worth internalising:** this bug was invisible to the test suite for ten phases because every
test injects a fake `llm` that returns clean JSON. The fakes were more polite than the real model.
Where a boundary is faked, the fake should reproduce the messy shape the real thing emits.

**Still open (unchanged, now clearly the bottleneck):** with `pain_points` finally flowing, the
has-website case *still* matched nothing — the research came back with "slow page loading, image
rendering optimisation", which genuinely matches nothing Manan builds. `RESEARCH_PROMPT` is never
told what he does, so it hunts generic web-perf issues instead of the automation / AI-assistant /
knowledge-compiler problems he is strongest at. Feeding his capability areas into the research
prompt remains the highest-leverage next fix.

**Result:** 65 tests green (58 prior + 7 new: 1 WhatsApp kill switch, 6 in new `test_llm_json.py`).

## Phase 11 — Capability-Aware Research + Engine A Actually Reachable (2026-07-27)

**Two halves: finishing the pitch-quality chain, then making Engine A a real pipeline.**

### 1. The research step now knows what Manan builds

`RESEARCH_PROMPT` asked for "problems a web/AI dev could fix" but was never told what *this* dev
builds, so on has-website leads it returned page-speed and image-size findings — matching nothing
in the portfolio, so the relevance floor correctly returned no project and the pitch went out with
no proof. This is why the has-website angle had been weak since Phase 7.

`research_target()` now takes the portfolio and derives a capability summary from the projects'
own `pitch_for` tags, telling the model to hunt openings in those areas (manual/repetitive work,
things customers can't self-serve) and explicitly *not* to return web-perf nitpicks this developer
can't credibly pitch.

**Same diagnostics-lab lead, before and after:**
| | pain found | matched | pitch |
|---|---|---|---|
| before | "slow page loading, image rendering" | *(none)* | "can I help enhance your website's performance?" (7.0) |
| after | "automate customer support, chatbot for FAQs" | Job Search Agent + Knowledge Compiler Agent | "I'd leverage Python, FastAPI and LangGraph to create an AI-powered chatbot, similar to my Job Search Agent" (8.0) |

**A second JSON bug found on the way.** Phase 10 fixed the ```` ```json ```` fences, yet
`pain_points` was *still* arriving empty live. Cause: Gemini formats long values as multi-line
numbered lists, putting **literal newlines inside JSON string values** — invalid JSON, and
`json.loads()` rejects the whole object over it. Fixed with `strict=False`, which permits control
characters inside strings. Two distinct malformations, two separate live runs to find them; worth
assuming there will be a third.

### 2. Engine A had four fetchers and nothing calling them

RemoteOK, WWR, JobSpy and the new HN source were all unreachable from the running app — jobs could
only arrive by being hand-posted to `/run-inbound`. Added `engine_a/sources.py::collect_jobs()` and
wired `/run-inbound` to fetch when no jobs are supplied (capped at `MAX_TARGETS`; a board returning
hundreds of rows would otherwise fire an LLM scoring call per row).

A failing source is logged and skipped rather than fatal — which **paid off on the first live
run**: WWR raised `ModuleNotFoundError: feedparser`. That dependency was missing from
`requirements.txt` and had gone unnoticed for nine phases because nothing ever called `fetch_wwr`.
Added.

**New source — HN "Ask HN: Freelancer? Seeking freelancer?"** (free, no auth). The research doc
called this "top-tier, trivially automatable". Measured reality: across four threads (Apr–Jul 2026,
~87 top-level comments) **exactly one** was `SEEKING FREELANCER` (a client hiring); the rest are
`SEEKING WORK` — other freelancers advertising, i.e. competitors. **Treat it as ~1 lead/month of
good quality, not a pipeline.** That makes the filter the whole feature: naive ingestion would feed
~85 competitor ads into the scorer.

**Tag filtering doesn't work on job boards.** RemoteOK posters spray tags for reach — a live
"Junior Procurement Specialist" carried 45 tags including `python`, `java`, `data science`. Tags
say nothing about relevance. Filter on **engagement model** instead, which is what project scope
actually cares about. Titles get a loose match (a title is a deliberate claim about the
engagement); descriptions need an explicit phrase, because long employment ads mention
"contract"/"consulting" incidentally — real WWR rows ("Senior Sourcing Analyst", "Director,
Facility Security Officer") slipped through a looser first attempt.

**Live result:** RemoteOK 0/10 kept, WWR 8/180 kept — and what survives is
*A.Team "Senior Independent Software Developer ($90–$170/hr)"*, *Mindrift "Freelance Full-Stack
Developer"*, *Storetasker*. LLM scoring calls per run went from ~190 to 9.

**Verified end-to-end live:** `POST /run-inbound {}` fetches real sources → scores → persists.
Scorer sanity-checked separately on a known-good vs known-bad job: **92 vs 0**, so the mass
rejection was correct judgement, not a broken scorer. WhatsApp sends: **0** throughout
(`WHATSAPP_ENABLED=false`).

**Result:** 88 tests green (70 → 88; +6 HN, +10 sources/filter, +2 API wiring).

## Phase 12 — More Sources + Geography Targeting (2026-07-27)

**Manan's strategy, in his words:** pitch ~100 to land one, and weight hard toward countries that
pay in dollars/pounds/euros — *"do clients bhi mille toh utna earn"*. Two USD clients beat a run of
INR work. So: more sources, and make currency visible so he can prioritise.

**New sources (free, no auth):**
- **Remotive** — the best board here by some distance. It exposes a **structured `job_type`**
  (`full_time` / `contract` / `freelance` / `part_time`), so its freelance filter is *exact*
  instead of the regex guess every other board needs; it's registered freelance-by-default for
  that reason. Also carries `salary` and `candidate_required_location`.
- **Working Nomads** — carries a location, no engagement field, so the shared filter screens it.

**Reddit is blocked.** `r/forhire`'s public `.json` endpoint now returns **403** without OAuth, on
both `www.` and `old.` hosts. The research doc listed it as a free API. It now needs a registered
Reddit app (client id/secret) before it can be built — **that's on Manan**, flagged to him.

**Geography now survives the pipeline.** `JobLead` had no `location` column, so inbound proposals
always showed both rate bands labelled "geography unknown" — hiding the exact thing he's targeting
on. Added `JobLead.location` (additive `ALTER`, row counts verified before/after), threaded
source → lead → proposal, and the dashboard now shows a location pill highlighted when the client
is high-tier. Where a source genuinely has no location (the HN thread), the honest both-bands
treatment stays.

**Tier matching had to change with it.** `_tier_for()` compared the whole string against a country
set, but boards give *regions*: "Americas, Europe, Israel", "Northern America, Europe, UK". Nothing
ever matched. Now word-boundaried term matching **inside** the string — boundaried because a bare
`us` would otherwise hit inside "Belarus". "Worldwide" counts as high-tier, since such a posting is
open to US/EU clients.

**Live result:** leads per run **9 → 21**, of which **12 flagged high-currency**, with real rates
now visible:

| | |
|---|---|
| Senior Independent **AI Engineer / Architect** | Americas+Europe, **$120–$170/hour** |
| Senior Independent Software Developer | Americas+Europe, $90–$150/hour |
| A.Team, Mindrift, Storetasker | contract dev work |

The AI Engineer listing is squarely Manan's profile at his target rate.

**Honest read on volume:** these boards give ~20 freelance leads per run, not 100. Inbound boards
are a **low-volume/high-value** channel — the $120–170/hr listings are worth pursuing individually.
Hitting "pitch 100" needs **Engine B outbound volume**, which currently depends on the gosom Maps
scraper running locally in Docker. Pointing Engine B at businesses in USD/GBP/EUR cities is the
next real lever, and nothing in the code prevents it — `maps_source.fetch_google_maps()` takes
arbitrary query strings, so "dentist in Austin Texas" works exactly like "bakery in Delhi".

**Result:** 97 tests green (88 → 97; +4 board sources, +5 geography).

## Phase 13 — Source Expansion, Verified (2026-07-27)

Five parallel research passes, all under a hard rule after previous rounds proved stale:
**verify with an actual request, report the observed status code, and mark anything untested as
unverified.** That rule paid for itself repeatedly below.

### Sources added (3 → 7)

**Freelancer.com — the biggest find.** The project's own research doc said this needed OAuth plus
application review. That's the *bidding/write* API; the **active-projects read endpoint answers
with no credentials at all** (verified `200`). It is also the only source here carrying *actual
client project posts* rather than employer job ads.

`budget.minimum/maximum` and `currency.code` are structured, so the USD/GBP/EUR priority is an
exact filter. Both filters are load-bearing:
- **Currency** — unfiltered the feed is INR-dominated low-rate work.
- **Budget, on separate scales for hourly vs fixed.** The API's `min_avg_price` applies one number
  to both, so a live pull returned `USD 2-8` and `USD 15-25` (hourly *rates*) next to
  `EUR 750-1500` (a project *budget*). On one scale, either the junk gets in or real fixed-price
  work gets dropped. Live: 34 raw → **10 kept**, all real money — `EUR 750-1500`,
  `USD 5000-10000`, `EUR 3000-5000`, `USD 10000-20000`.

**Reddit — and a correction to my own earlier finding.** I tested `r/forhire`'s `.json` endpoint,
got `403`, and told Manan he'd need to register a Reddit app. **Wrong.** The `.rss` path is open
and unauthenticated (`200`, ~68KB of real content). No app needed — that ask is withdrawn.

Measured live: ~24% of posts are `[HIRING]` (a client with work), the rest `[FOR HIRE]`
(freelancers advertising — competitors). Across r/forhire + r/hiring that's **~100 client posts a
week**, more than any other free source here. Two implementation notes: `"[FOR HIRE]"` contains
`"hire"`, so the tag is anchored to the start of the title — a substring check inverts the meaning
and fills the pipeline with competitor ads; and Reddit rate-limits this path hard (observed
`x-ratelimit-remaining: 0` after one request, ~13s reset), so requests are spaced and a failing
sub is skipped.

**Himalayas** — free, no auth, ~96k jobs, same structured-`employmentType` advantage as Remotive
over a far larger corpus, plus `locationRestrictions` and salary. Density is the catch: ~5-9%
contract-shaped, 20 per request regardless of `limit`, so it paginates conservatively.

### Verified dead — stop revisiting these

| Source | Observed | |
|---|---|---|
| Upwork RSS | **`410 Gone`** | confirmed twice, independently |
| Upwork job search, Workana, Wellfound RSS, EU Remote Jobs | `403` | bot-walled |
| Truelancer | `429` on first request | hostile to automation |
| PeoplePerHour RSS/HTML, JustRemote, Twine | `200` **but no listings** | JS shells / anti-bot pages, not feeds |
| RemoteOK RSS | `410` | (its JSON API still works) |
| IndieHackers feed | `200` | every item paywalled "IH+ Subscribers Only" |
| Clutch.co, DesignRush, GoodFirms | `403` | Cloudflare-gated |
| Guru, NoDesk, Pangian, lobste.rs jobs, wip.co | `404` | |

A `200` is not evidence of a usable feed — several of the above return HTML shells while reporting
success. Check for actual items, not the status code.

### Not code — worth Manan's own time

- **Contra** (0% commission, portfolio-first, lowest barrier for zero reviews), then **A.Team**,
  **Braintrust**, **Gun.io**. These are apply-and-be-matched networks with no ingestible feed;
  automating them isn't possible and isn't the point. Note A.Team/Mindrift/Storetasker listings
  **already reach him** through Remotive/WWR.
- **Agency subcontracting** — likely the strongest USD channel per unit of effort, because one
  agency relationship yields repeat work. The directories are Cloudflare-gated, but agencies are
  just businesses with websites, so **Engine B already handles them** if fed agency names — e.g. a
  Maps query for "web design agency in Austin".
- **Discord/Slack** `#jobs` channels — real, but monitoring needs a bot invited per server with
  admin permission, and most communities prohibit it. Join 3-5 manually; the agent can draft replies.

### Conversion research — evidence that should change the plan

- **"Pitch 100 → land 1-2" is optimistic but reachable.** Median cold-email reply is ~3.4%; small
  businesses reply at ~7%; lists under 50 recipients average 5.8% vs 2.1% for large sends. 100
  tightly-targeted SMB pitches ≈ 5-7 replies ≈ **0.5-2 clients**. Sustained, budget 200-400/month.
- **The real ceiling is deliverability, not generation.** New domains need 14-21 days of warmup
  with zero cold sends, then **25-30 cold emails per inbox per day** — Gmail/Yahoo/Microsoft enforce
  <0.3% complaint rates. **So "pitch 100" is ~4 days of sending on one inbox, not one morning**, and
  it must go from a secondary domain, never his main one. **Flag before any live sending.**
- **Follow-ups carry ~42% of all replies** — currently not built at all. The single biggest gap.
- **50-125 word emails reply at 8.2% vs 3.9% for 200+.** The writer's 120-word cap is right;
  ~90 would be better.
- **Deep personalisation ~18% vs ~9% for basic templates** — directly validates the grounding and
  anti-hallucination work, and argues against trading personalisation for volume.
- **Don't put a Loom in message one** — permission-first, record only for repliers.
- Everything about the current design that the evidence touches — never auto-send, human approval,
  no price in message one — is **corroborated**. No change warranted.

**Result:** 128 tests green (97 → 128). Live: 40 leads/run across 7 sources, 18 with a stated
budget/rate, including `$120-$170/hour` AI engineering and `USD 5000-10000` project work.

## Phase 14 — Engine B Volume Without Docker (2026-07-27)

**The problem this solves.** Engine B is where "pitch 100" volume has to come from — inbound
boards give ~40 leads/run and no more. But its only lead source was the gosom Maps scraper, which
needs a Docker container running. So in practice Engine B had no usable source at all.

**OpenStreetMap Overpass** answers it: free, no auth, no key, **no Docker**, global.

Measured live — one Austin bbox across dentists / lawyers / accountants / estate agents returned
**76 named businesses, 35 of them with no website**. That no-website half is the *best* segment,
not waste: "I searched and couldn't find your site" is a **verified fact** rather than an
inference, and that pitch already scores 8/10 (Phase 7). Overpass states the absence definitively.

**Also shipped:** prebuilt city bounding boxes (`engine_b/areas.py`) defaulting to US/UK/EU
markets — Delhi available but deliberately not a default — and `POST /run` with no targets now
fetches them. Previously targets could *only* be hand-posted, which cannot reach volume by
definition. Capped at `MAX_TARGETS`; one city returns ~200 businesses and each costs several LLM
calls.

**Live volume, 4 default cities, one run: 733 businesses — 422 with no website.** Seven times the
"pitch 100" target. Category mix: 198 dentists, 136 estate agents, 136 doctors, 94 lawyers, 63
clinics, plus insurance/accountants/veterinary.

**The honest limit, and it's a real strategic tension.** Measured precisely on Austin (148
businesses):

| Segment | Has a phone number |
|---|---|
| **No website** (the best segment to *pitch*) | **7/79 — 9%** |
| Has a website | 60/69 — **87%** |

**The businesses easiest to pitch are the hardest to reach.** That inverse correlation makes sense —
a business absent from the web is absent from OSM's contact tags too — but it means the no-website
angle, which scores 8/10, currently has no delivery channel for ~91% of its leads. Options, none
built: the gosom Maps scraper (has phone numbers, needs Docker) as a complement for exactly this
segment; contact-form submission for the has-website half; or the enrichment backlog
(Prospeo/FullEnrich free tiers). **Worth deciding before scaling outbound volume — generating 422
unreachable pitches is not progress.**

### Debugging the first live run — two wrong assumptions, both corrected by measurement

The first 4-city run failed on London and Dublin with all mirrors exhausted. Rather than guess,
I measured every candidate mirror with an identical light query:

| Mirror | Result |
|---|---|
| **overpass-api.de** | **`200` in ~2s** |
| overpass.private.coffee | ReadTimeout at 40s |
| overpass.kumi.systems | ReadTimeout at 40s |
| maps.mail.ru | `504` |
| overpass.osm.ch | `200` but **0 elements** (regional instance) |
| overpass.osm.jp | ConnectError — **SSL hostname mismatch, broken** |

**Wrong assumption 1: the mirror order.** It led with `private.coffee` (which the research pass had
found working, and which now times out) and listed a mirror whose certificate is broken. Reordered
to put the verified-working endpoint first; dropped the dead ones.

**Wrong assumption 2: that heavy queries caused the 504s.** They don't. A 5-category query `504`'d
while a strictly *heavier* 6-clause query succeeded seconds later **on the same endpoint**. The
public service is **load-flaky, not query-flaky** — which means the correct response is retry with
backoff, not a smaller query. Attempts now cycle back round the mirrors instead of giving up after
one pass. Worth remembering generally: an intermittent failure that correlates with nothing in your
input is a load problem, and shrinking your request is treating the wrong cause.

### Target categories, chosen on evidence

`dentist, doctors, clinic, veterinary, driving_school` + offices `lawyer, accountant, estate_agent,
insurance, financial`. Picked for margin plus manual workload — appointment booking and
document-heavy intake is exactly what an automation pitch lands on, and these showed the highest
no-website rates in the live data (~38/49 for London dentists). Restaurants and retail are
deliberately excluded: low margin, and already served by aggregators.

**Result:** 149 tests green (128 → 149).

## Phase 15 — Strategy Corrections: What We Sell, To Whom, Where (2026-07-27)

Four corrections from Manan in one session, each of which the code was quietly getting wrong.

### 1. "Khali website se paisa nahi banega"

The no-website angle literally instructed the model to *"offer to build one"* plus an SEO bonus.
A website is the cheapest thing he sells, and leading with it anchors the entire relationship at
that price.

Now the missing site is read as **evidence** the business runs manually, and the offer is the
outcome — an AI assistant, automated booking or intake, whatever the cited past work supports. A
site may be *how* it's delivered; it is not the pitch. The researched angle likewise reaches for
the highest-value thing the portfolio supports rather than cosmetic site tweaks, and offer scoring
now rewards outcomes over deliverable lists.

His framing: *"all-rounder, sara kaam"* — AI, software, consulting, business solutions. The
portfolio has 15 projects spanning agents, RAG, CV, ML, fintech, dashboards and apps; the pitch
should reach for whichever fits, not default to the commodity one.

### 2. "Chote se bada sabko" — 10 categories → 145

Targets were five clinic types and five office types. Now seven OSM tag families:

| Family | Covers |
|---|---|
| `craft` | electrician, plumber, carpenter, HVAC, roofer, painter, builder, locksmith… |
| `healthcare` | physiotherapist, psychotherapist, optometrist, laboratory, rehab… |
| `office` | lawyer, accountant, architect, engineer, recruiter, **company, IT, consulting, research** |
| `shop` | car repair, furniture, hardware, optician, salon, printing, tailor… |
| `amenity` | clinics, driving/language schools, banks, coworking, event venues |
| `tourism` / `leisure` | hotels, guesthouses, gyms, studios |
| industrial | factories, warehouses, wholesale (via `landuse`/`building`) |

**Queried per tag family, not as one query.** A single query over all of it reliably 504s on a
load-flaky endpoint, and one failure would cost the whole city rather than one slice. Results are
deduped, since a firm can match two families.

### 3. "Overseas, India, sab jagah" — 45 cities → 214, across 81 countries

North America 39 · Europe 64 · Middle East 10 · Asia-Pacific 20 · Oceania 10 · South America 15 ·
Africa 16 · **India 39** (metros plus tier-2: Indore, Nashik, Varanasi, Guwahati, Raipur, Ranchi…).

Cities are stored as a **centre point** with the bbox derived, not four hand-written numbers each.
At this size that matters: one mistyped coordinate can silently produce an inverted or
planet-sized box, and Overpass reports that as a *timeout* rather than an error. The longitude
span also widens by `1/cos(latitude)` — a fixed-degree box covers far less ground in Stockholm
than in Singapore.

### 4. "~120-130 currencies are stronger than the rupee"

So tiering became an **exception list**, not a whitelist of ~30 Western countries — that whitelist
was silently discounting most of the world. Now 69 of 81 targeted countries price at the premium
band; only 12 (India, South Asia, parts of Sub-Saharan Africa) sit on the discounted one.

**A nuance worth keeping:** per-unit currency strength is the *wrong* test. The yen is weaker than
the rupee per unit, yet Japanese rates are far higher — Manan raised exactly this case. The list
tracks **prevailing dev rates**, not exchange rates. Tokyo, Seoul, Warsaw, Istanbul, São Paulo,
Mexico City, Bangkok, Jakarta, Manila and Cairo all correctly price high.

**Two bugs this surfaced, both caught by testing rather than assumed:**
- `"US"`, `"UK"`, `"UAE"` were being dropped onto the discounted band, because place-detection
  required 3+ letters.
- A **Delhi client was quoted the premium band** — the exception list held country names while
  Engine B targets carry bare city names or street addresses. Major lower-rate cities are listed now.

### Data-quality fixes from the live run (Austin: 148 → 658 businesses)

- **238 of 658 had no category.** Five tag families were added to the query but `_to_target` still
  read only the original four, so `craft=electrician` and `healthcare=physiotherapist` arrived
  uncategorised. The writer prompt uses this (`"a {category} in {location}"`), so those pitches were
  all degraded. Another 50 carried `building=yes`, which classifies nothing — "a yes in Austin"
  reads worse than saying nothing.
- **Infrastructure was being pitched.** Industrial land returned electricity substations, power
  plants, a water treatment works and municipal depots — over half that slice. Elements tagged
  `power=*` or `man_made=*` are now skipped.
- **Branded corporate branches dropped.** Broadening to offices pulled in Google, Meta, McKinsey,
  Accenture and Cloudflare locations. They don't hire solo freelancers by cold email, and OSM omits
  their `website` tag — so the pipeline would have told Google *"I searched and couldn't find your
  website"*. Verified on live data: `brand:wikidata` was set on those corporates and on 1 of 31
  local firms.

**Result:** 178 tests green (149 → 178). Austin alone now yields 658 businesses, 386 without a
website.

## Phase 16 — Follow-Up Sequencing (2026-07-27)

**The biggest gap the Phase 13 conversion research found, and it was unbuilt:** follow-ups carry
**~42% of all replies**. Every pitch sent without one was leaving most of its return unclaimed.
Supporting evidence: 3-5 step sequences reply at ~8.3%, 4-7 touches is the usual optimum, and
"just checking in" notes underperform substantive follow-ups by **15x** on meetings booked.

**Scheduling** (`backend/crm/followups.py`) is a pure function of `(sent_at, followups_sent, now)`
— no clock inside the logic and no background job; the daily run asks what is due and acts on the
answer. Four steps at **3 / 7 / 16 / 30 days**, measured from the *original* send so a skipped or
delayed step doesn't shift everything after it. Two behaviours worth stating:

- A lead untouched for 90 days receives its **next** step, not four messages at once.
- Anything `replied` / `won` / `lost` / `unsubscribed` / `bounced` drops out. Chasing someone who
  already answered is the worst touch available.

**Content** (`backend/crm/followup_writer.py`) gives each step a distinct angle rather than a
nudge: (1) one concrete thing you'd build first and why that one, (2) proof — what the cited
project actually achieved, (3) a smaller ask (a short call, not the project), (4) a polite close
that leaves the door open with no final-notice pressure. The original message is passed in so the
model can avoid restating it, and the Phase 6-8 grounding rules carry over unchanged: no invented
business detail, no tech outside the cited project's stack, no price.

**Two bugs found by running it live rather than trusting green tests:**

1. **Follow-ups scored 0.0 and 2.0.** `write_followup` inherited `_score`'s `has_source=True`
   default, which put no-website leads on the *tailoring* rubric — the exact failure Phase 7 split
   the rubrics to avoid, reintroduced by reusing the helper without thinking about its default.
   Threaded through; the same leads now score 6-8.
2. **Output collapsed to 10-18 word telegrams** — *"Let's automate order tracking with LangGraph.
   Would that interest you?"* The cause was mine: I had written the rationale **inside the prompt**,
   including the phrase "11-word telegrams", and the model anchored on that number. Rationale moved
   to a code comment; length given as a **range with a floor** rather than a cap. Output is now
   31-43 words in full sentences.

   Worth generalising: prompt text is instructions to the model, not a changelog. Explaining *why*
   a rule exists inside the prompt can actively work against it.

**Schema:** `CrmRecord.followups_sent` added (additive `ALTER`, row counts verified unchanged).

**Also verified this phase** — the Phase 15 Overpass data-quality fixes, against live Austin data:
`building=yes` junk **50 → 0**, `landuse=commercial` noise **71 → 0**, blank categories
**238 → 52**, and the category mix now reads like real businesses (hairdresser 46, dentist 44,
beauty 38, doctors 29, sports centre 29, company 24, hotel 23, fitness centre 23).

**Result:** 201 tests green (178 → 201).

## Phase 17 — Unattended Engine B, and Making It Sound Human (2026-07-27)

**Manan's ask:** *"Engine B should also be automated completely so that, on my behalf only, it will
help me find clients and pitch for me."* Two research passes ran alongside the build — one on
reaching the leads, one on sending — and both changed the plan.

### Built

**`run_daily.py` + `backend/automation/daily.py`** — cron entrypoint. Sources businesses for a
rotating slice of cities, researches each, drafts the pitch, leaves everything queued. **It never
contacts a client**; the only outbound message is a summary to Manan, and a test asserts
`sent_to_clients == 0`. City rotation is derived from the date, so cron needs no state file, and
both the city slice and target count are capped — one city returns ~480 businesses and each costs
several LLM calls. A dead Overpass mirror is caught and reported rather than silently breaking a job
nobody watches. `--dry-run` checks a city for free.

**Batch approve** (`POST /dashboard/approve-all`) — Manan's chosen middle path over full auto-send:
everything up to the send runs unattended, his part collapses to one click. Defaults to score 7+,
capped, skips already-approved drafts (a second click would otherwise double the CRM records).

**Humanising** (`backend/engine_b/humanize.py`) — the phase's real work, and Manan's stated
priority: *"proper humanize message chahiye"*. Nine tell-families are detected, taken from this
project's **own live drafts** rather than a listicle: corporate filler verbs (`leverage`,
`streamline`, `optimize`), LLM adjectives (`seamless`, `robust`, `elevate`), the delve family,
boilerplate openers, rhetorical scare questions (*"Can you afford to lose potential customers?"* —
which appeared in three separate drafts), "not just X but Y", stacked em-dashes, padding
connectives, and vague benefit-speak.

Detection feeds the regen loop and **names the specific tell** in the rewrite prompt. That detail
carries the feature: telling a model to "sound more human" without saying what it did wrong returns
the same text. A clean draft costs no extra call. Live result — *"You're likely handling enquiries
and bookings manually, given I couldn't find a website for Lone Star Pediatric Dental…"* — 43 words,
zero tells, 8/10.

### Manan's decisions this phase

**No AI-disclosure line.** The EU AI Act Article 50 research (below) led to a disclosure being built
and wired in; he reviewed it and said no. It now sits behind `ai_disclosure_enabled` (default
`False`) rather than being deleted — one setting away if he changes his mind. He also chose to
accept the Germany/UK-sole-trader exposure. Both are recorded here as his calls, not oversights.

**Batch approve over full auto-send** — after seeing that a human click doesn't prevent bans but
does catch content bugs.

### Research findings that changed the picture

**Reaching the leads.** OSM gives name + street address and essentially nothing else — a tag census
of 160 no-website Austin businesses found **74% with a street address, 7.5% with a phone, and zero
emails or socials**. Enrichment APIs (Prospeo, Hunter, Snov, Apollo, FullEnrich — all key-gated
when tested) are built to infer `firstname.lastname@company.com` from a corporate domain, so they
**structurally cannot help a dentist with no domain**. The verified path is **gosom's Maps scraper**
(confirmed alive: `pushed_at 2026-07-26`, MIT, real source tree, `Entry.Phone` in its struct) —
business owners claim Google Business Profiles without building websites, so Google has phones
exactly where OSM doesn't. Its email extraction scrapes `entry.WebSite`, so it cannot produce emails
for this segment either.

**The honest conclusion: the no-website segment is a PHONE segment.** Automation can find, qualify,
research and draft for it; it cannot deliver it. That's a ceiling, not a gap to engineer around.

**Sending.** Four of seven providers — **Postmark, Resend, Mailgun, Brevo** — explicitly prohibit
scraped lists and cold outreach in their own terms. Using them isn't risky, it's a terms breach that
kills the account. **Amazon SES** is permissive on content but pauses at 0.5% complaints. **Google
Workspace is the realistic path**, ~₹300-400/month all-in including a separate domain, which
comfortably fits the project budget. Never from `manankumar.in`.

**Legal, as it applies to our actual list:** US CAN-SPAM permits B2B cold email with conditions.
**UK PECR treats sole traders as individual subscribers requiring consent** — and Engine B targets
electricians, plumbers, hairdressers and single-practitioner clinics, so a meaningful slice of the
UK list falls there. Germany effectively requires consent even B2B. **EU AI Act Article 50 applies
from August 2026** — next month — requiring disclosure on AI-generated text.

**On the human click:** it does **not** protect against bans, which are driven by complaint rate,
bounce rate and velocity. It protects **content quality** — and every one of this project's six
phases of content bugs (invented tech stacks, fabricated business details, stretched portfolio
matches) was caught by a human reading output.

### Open — the Gmail MCP distinction

Manan suggested sending via the Gmail MCP. Worth recording why that doesn't close the loop: the MCP
is a **Claude session tool**, available only while he's in a session. Cron runs at 08:00 with no
session attached, so nothing would send. Autonomous sending needs the agent's **own** Gmail API
OAuth credentials — a separate integration, gated on the domain/Workspace/warmup setup above.

**Result:** 244 tests green (201 → 244).


## Phase 18 — Making a Draft Sendable (2026-07-28)

**Manan's ask:** *"continue lets accelerate from tomorrow business karna shuru karte."*

The gap between Phase 17 and doing business was not lead quality or draft quality. It was that
**the drafts had nowhere to go.** Engine B could source, research, personalise and score — and
then hand Manan a card with no address on it. Overpass carries an `email` tag for close to nobody
(Phase 13 measured 0% on the no-website segment), so every run was producing work that couldn't be
delivered.

### Built

**`backend/engine_b/contacts.py`** — reads the business's own website for a way in. `mailto:` links
and footer addresses first; if the homepage has none, it follows a contact page (`/contact`,
`/kontakt`, `/contacto`, …) and tries again. Returns `{"email", "contact_url"}`; a contact form is a
real channel, it just costs a manual submit instead of a paste.

Two decisions inside it are load-bearing:

- **Redirects are followed manually, re-running the SSRF guard on each hop.** Following blindly
  would let a redirect walk the fetcher onto a private address; not following at all (what
  `research.py` does, deliberately) loses the plain `http://` → `https://` hop that most small
  business sites still start with.
- **The junk list is what live pages actually return**, not defensive padding: `logo@2x.png` matches
  a naive email regex, and `noreply@wixpress.com`, `you@example.com` and `sentry@sentry.io` all
  appear on pages that publish no real address.

**`backend/engine_b/subject.py`** — a cold email needs a subject line, and a bad one costs more than
a bad body since it decides whether the body is read at all. Written from the **final** draft (after
the humanise and score regens), in its own LLM call. Folding it into `WRITE_PROMPT` would save a
call, but that prompt is tuned across several phases and this project has already watched a
late-added rule there override earlier ones (Phase 16). The cleanup strips exactly what the model
emits unprompted: a `Subject:` label, exclamation marks, an ALL-CAPS opener, and `Re:`/`Fwd:` faking
a reply thread — that last one is a deception, not a tactic, so it is removed rather than allowed.

**Dashboard** — each card now names its channel and the list is ordered **sendable first, then best
score**. An unreachable 9/10 sitting above a sendable 7/10 costs the only genuinely scarce resource
here, which is Manan's morning. Unreachable drafts stay visible rather than being hidden: they are
the running measure of how much sourcing effort goes to businesses nobody can contact. The email
link is a `mailto:` with subject and body pre-filled, so approve-then-send is one click into his
mail app. **Nothing auto-sends — that rule is unchanged.**

### Measured (don't re-learn)

- **The fetch cap was the feature.** At 200KB, extraction found nothing on most real sites.
  `dishoom.com` is **1.05MB** and `deliciouslyella.com` **1.15MB**, mostly inline JS, and both keep
  the contact link and footer address well past the first 200KB. Raising the cap to 2MB turned a
  miss into a hit. Read the whole page or don't bother.
- **JS-rendered sites yield nothing to a plain fetcher.** Several probed sites had no `href`
  containing "contact" anywhere in the HTML — the nav is built client-side. That is the hard ceiling
  of non-browser extraction, and the reason the remaining gap needs a headless browser or the Maps
  scraper rather than a better regex.
- **Overpass degrades badly under load.** With 90s timeouts × 6 attempts × 7 tag families, one city
  can take the better part of an hour when the mirrors are busy. Fine for cron, painful for
  measurement — start sourcing before you need the answer.

### Schema

`outbound_targets.contact_url` and `outreach_messages.subject`, both hand-applied additive
`ALTER TABLE` (still no Alembic in this project).

**Result:** 273 tests green (244 → 273).

<!-- Next session: append "## Phase 19 — ..." here. Do not edit sections above. -->
