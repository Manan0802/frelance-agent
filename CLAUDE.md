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
- **Phase 11 (capability-aware research + Engine A sources wired) = COMPLETE.**
- **Phase 12 (more sources + geography targeting) = COMPLETE.**
- **Phase 13 (source expansion, verified) = COMPLETE.** 40 leads/run, 7 inbound sources.
- **Phase 14 (Engine B volume without Docker) = COMPLETE.**
- **Phase 15 (strategy corrections: what we sell, to whom, where) = COMPLETE.**
- **Phase 16 (follow-up sequencing) = COMPLETE.**
- **Phase 17 (unattended Engine B + humanised copy) = COMPLETE.** 244 tests green.
- **Phase 18 (delivery: contact + subject) = COMPLETE.** 278 tests green.
- **Phase 19 (skill audit + what the first real drafts exposed) = COMPLETE.** 307 tests green.
- **CURRENT BLOCKER IS NOT CODE.** 24 drafts sit in the queue, 19 with a contact channel, and
  **none have been sent** (verified 2026-08-08 — status still `draft`, 0 CRM records). Nothing is
  known about whether the pitch works. **Do not build more automation before a single reply
  exists** — n8n/Camofox/Agentic Inbox are all queued behind that one fact.
- **Outreach rules are set from measured data, not taste** (`cold-email` skill benchmarks):
  subject **2-4 words** (2-word gets 60% more opens; 2→4 costs 17.5% of replies), body
  **40-75 words** (under 75 = +83% replies), `you/your` must outnumber `I/we` (#2 ranked
  mistake), and **never ask for a call/demo on first contact** (#7). No numbers, no business
  name in the subject. The follow-up schedule (3/7/16/30) was audited and **validated** — leave it.
- **A block page is not their website, and "couldn't read it" is not "they don't have one."**
  Neither fetcher checked the status code, so a 403/Cloudflare challenge became site content and
  live drafts told real businesses *"your website's 403 error is hiding your patient support
  info"*. **Re-measured 2026-08-08: all three of those sites 403 even to a browser User-Agent**
  — so we could not tell a bot-block from a broken site, which is exactly why asserting either
  was reckless. A failed fetch is never evidence about *their* site. Fixing that exposed the
  mirror image. **Three states, not two** (`writer.angle_for`):
  no site / unreadable / read — **only the first supports claiming an absence**.
  **8 drafts out of 25 targets carried one of those false claims while 307 tests were green.**
- **A Facebook page is not a website** — OSM's `website` tag is often a social page, which sent
  our strongest segment the researched angle (the one told *not* to offer a website).
- **Volume breaks things tests never see:** 125 LLM calls in a burst 429'd Gemini *and* the Groq
  fallback, and the run died losing every draft before it (commit was after the loop). Now
  backoff retry + **per-target commit**.
- **Run the dashboard under `pm2`, not a background shell** — a backgrounded server dies on
  session teardown (happened three times). `pm2 start ... --name freea-dashboard && pm2 save`.
- **Full handoff lives in the Obsidian vault** — `manan-memory/Projects/freea/` (8 notes).
  Start any new session from `freea-open-threads`.
- **Reachability, measured live (Austin, 608 businesses):** 256 have a website, 352 don't; only 60
  of 608 carry an OSM `email` tag. Probing 50 website-having rows → **34% email, 16% contact form,
  50% nothing** (20 of those 50% have a phone). So **~128 reachable leads from one city**. The
  no-website segment held at **8% phone (29/352)** — qualify-able, still not deliverable.
- **Two traps found only in live data:** the published address is often a *vendor's*
  (`webreporting@gargle.com` on a dental site) — `best_email()` prefers the business's own domain,
  but off-domain is NOT a reject since small businesses run on gmail; and **one inbox can be three
  leads** (`startnow@austincc.edu` × 3 campuses) — `send_order()` marks repeats and sinks them,
  because three cold emails into one inbox is how a sending domain gets reported.
- **A draft is only a lead if it has a channel.** `backend/engine_b/contacts.py` reads the target's
  own site for a `mailto:`/footer address, then follows a contact page; `backend/engine_b/subject.py`
  writes the subject from the **final** draft in its own call (never folded into `WRITE_PROMPT` —
  that prompt is tuned and late rules override earlier ones). The dashboard names the channel per
  card, orders **sendable first then best score**, and the `mailto:` link carries subject + body so
  send is one click. Still never auto-sends.
- **The page-fetch cap WAS the feature — measured.** At 200KB extraction found nothing on most real
  sites: `dishoom.com` is 1.05MB, `deliciouslyella.com` 1.15MB, and both keep the contact link and
  footer address past the first 200KB. Cap is now 2MB. **JS-rendered sites still yield nothing** —
  no `href` containing "contact" exists in their HTML at all. That gap needs a headless browser or
  the Maps scraper, not a better regex.
- **Overpass degrades badly under load:** 6 attempts × 7 tag families means one city can take most
  of an hour when mirrors are busy. Fine for cron, painful for live measurement.
- **The client timeout was killing the only working mirror (fixed).** Re-measured 2026-07-28 with
  the *real* query, not a toy one: `kumi.systems` returned 200 elements at **93s** while
  `overpass-api.de` 504'd at 13s (though .de serves a light query in 2s). Our client gave up at 90s.
  Timeout is now 150s. **Revises the old "load-flaky, not query-flaky" note — weight matters too.**
  Always benchmark mirrors with the actual query.
- **Engine B runs unattended:** `run_daily.py` (cron entrypoint) rotates cities by date, sources →
  researches → drafts → queues, and **never contacts a client** (a test asserts it). `--dry-run`
  checks a city without spending LLM calls.
- **Batch approve:** `POST /dashboard/approve-all` (button defaults to score 7+) — Manan's chosen
  middle path over full auto-send. Approve marks ready; it still sends nothing.
- **Messages must not read like AI** (`backend/engine_b/humanize.py`) — 9 tell-families taken from
  this project's own live drafts (`leverage`, `seamless`, "I hope this email finds you well",
  "Can you afford to…"). A flagged draft is regenerated **with the specific tell named** — saying
  "sound more human" without naming it returns the same text.
- **MANAN'S DECISIONS (don't silently revert these):** no AI-disclosure line on outbound
  (`ai_disclosure_enabled=False`, machinery kept behind the flag); he accepted the Germany /
  UK-sole-trader email exposure after it was flagged.
- **The no-website segment is a PHONE segment.** Measured: 74% have a street address, 7.5% a phone,
  **0% an email or socials**. Enrichment APIs infer emails from corporate domains and structurally
  cannot help a dentist with no domain. gosom's Maps scraper (verified alive, MIT) has phones —
  Google Business Profiles exist where websites don't. Automation can find/qualify/draft for this
  segment but **cannot deliver it**.
- **Postmark / Resend / Mailgun / Brevo forbid cold outreach in their terms** — using them is a
  terms breach, not a risk. Google Workspace (~₹300-400/mo, separate domain) is the realistic path.
- **The Gmail MCP can't power automation** — it's a Claude *session* tool, and cron runs with no
  session. Autonomous sending needs the agent's own Gmail API OAuth.
- **Follow-ups are built** (`backend/crm/followups.py` + `followup_writer.py`) — they carry ~42%
  of replies. Pure scheduling function over `(sent_at, followups_sent, now)`: 4 steps at
  3/7/16/30 days from the ORIGINAL send, one step per run (never a burst), and replied/won/lost
  drop out. Each step has its own angle — **never a "just checking in" nudge, that's 15x worse.**
- **Prompt text is instructions, not a changelog.** A follow-up rule explained itself inside the
  prompt ("a bare cap produced 11-word telegrams") and the model anchored on that number,
  emitting 10-18 word messages. Keep rationale in comments; give ranges with a floor, not caps.
- **WE DO NOT SELL WEBSITES.** Manan: *"khali website se paisa nahi banega"* — the offer is
  AI/automation/software/consulting, an all-rounder range drawn from the 15-project portfolio.
  A missing website is **evidence the business runs manually**, not the product to sell. Never let
  a prompt drift back to "I'll build you a website".
- **Targets: 145 categories × 214 cities × 81 countries.** Trades, healthcare, professional
  services, companies/startups/IT, retail, hospitality, gyms, industry — solo tradespeople through
  factories and corporates. India has 39 cities (incl. tier-2), and `areas_for(["India"])` selects
  a whole country.
- **Pricing tiers are an EXCEPTION LIST, not a rich-country whitelist** — ~120-130 currencies beat
  the rupee, so 69 of 81 countries price at the premium band. It tracks **prevailing dev rates, not
  exchange rates**: the yen is weaker per unit than the rupee but Japan pays far more, so Japan is
  high tier. Lower-rate list includes major **cities** too, since leads carry bare city names
  (a country-only list quoted a Delhi client the premium band).
- **Overpass hygiene (all found in live data):** read the category from *every* queried tag family
  or pitches go out with a blank category; ignore `building=yes`; skip `power=*`/`man_made=*`
  (substations and treatment plants aren't clients); skip `brand`/`brand:wikidata` (Google/Meta
  branch offices aren't clients either).
- **Engine B now sources its own leads with no Docker:** `backend/engine_b/overpass_source.py`
  (OpenStreetMap Overpass — free, no auth, no key) + `backend/engine_b/areas.py` (prebuilt city
  bboxes, defaulting to **US/UK/EU**; Delhi available but not default). `POST /run` with no
  targets fetches them. One Austin bbox = 76 businesses, 35 with **no website** — the best pitch
  segment, since the absence is a verified fact.
- **Overpass gotchas (measured, don't re-learn):** use `overpass-api.de` first — `private.coffee`
  and `kumi.systems` read-time-out, `overpass.osm.jp` has a broken SSL cert, `overpass.osm.ch`
  returns 0 elements. The 504s are **load-flaky, not query-flaky** (a heavier query succeeded
  seconds after a lighter one failed), so **retry with backoff — don't shrink the query**.
- **Live volume: 733 businesses / 4 cities / one run, 422 with no website** — 7x the "pitch 100" target.
- **Overpass gives reach, not contacts — and the correlation is inverse.** Measured on Austin:
  no-website rows have a phone only **9%** of the time (7/79), has-website rows **87%** (60/69).
  **The best segment to pitch is the hardest to reach.** No delivery channel exists yet for ~91%
  of no-website leads — gosom Maps (has phones, needs Docker), contact-form submission, or
  enrichment are the options. **Decide this before scaling outbound; 422 unreachable pitches
  aren't progress.**
- **Sources:** Freelancer.com (**no-auth read API — the docs' "needs OAuth" is about the *bidding*
  API**; only source with real client project posts, structured currency+budget), Reddit
  (`.rss` works unauthenticated — `.json` 403s; ~100 client posts/week, biggest volume),
  Himalayas (~96k jobs, structured `employmentType`), Remotive, Working Nomads, HN-freelance,
  RemoteOK, WWR.
- **Filter traps worth remembering:** `[FOR HIRE]` contains "hire" (anchor the tag, don't
  substring-match, or the pipeline fills with competitor ads); Freelancer.com hourly *rates* and
  fixed *budgets* need separate floors or junk gets through; a `200` is not proof of a usable feed
  (PeoplePerHour/JustRemote/Twine return HTML shells).
- **Verified dead — don't revisit:** Upwork RSS (410), Workana/Wellfound/Clutch (403), Truelancer
  (429), PeoplePerHour/JustRemote/Twine (JS shells), IndieHackers feed (paywalled).
- **Deliverability is the real volume ceiling, not lead generation** — new domains need 14-21 days
  warmup, then ~25-30 cold emails/inbox/day. "Pitch 100" is ~4 days of sending, from a **secondary
  domain, never his main one**. Warn before any live sending.
- **Follow-ups carry ~42% of replies and are not built** — the biggest remaining gap.
- **Targeting priority (Manan's strategy):** volume + **USD/GBP/EUR clients** — two of those beat a
  run of INR work. `JobLead.location` is carried source → lead → proposal; the dashboard
  highlights high-tier (high-currency) leads, and pricing uses the real geography when known.
- **Sources now:** HN-freelance, **Remotive** (best — structured `job_type`, salary, location),
  **Working Nomads**, RemoteOK, WWR. Live: 21 leads/run, 12 high-currency.
- **Reddit `r/forhire` is 403 without OAuth** — the research doc's "free API" claim is stale.
  Needs Manan to register a Reddit app before it can be built.
- **Inbound boards are low-volume/high-value** (~20/run, incl. $120-170/hr listings). "Pitch 100"
  volume must come from **Engine B outbound** — and `maps_source.fetch_google_maps()` takes any
  query string, so pointing it at USD cities ("dentist in Austin Texas") is the next lever.
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
