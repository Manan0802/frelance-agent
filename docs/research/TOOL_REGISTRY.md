# 🧰 Tool Registry — Freelancing Agent

**Rule:** Nothing is deleted. Every tool we evaluate lives here, tiered by *when* it earns a place in the system. "Skip" never means discard — it means **REFERENCE tier** (shelf it, revisit when the situation calls for it).

**Tier legend**
- 🟢 **CORE** — Phase 1. Goes into the first working system.
- 🟡 **PHASE-1.5 / PHASE-2** — Adopt after the first client / once the core proves out.
- 🔵 **REFERENCE** — Parked on purpose. Real and useful, but not for our current stage/goal. Pull off the shelf when the trigger condition hits.

**Context that drives tiering:** cold-start (no platform reputation), edge = production AI-agent dev, channel = outbound/direct > platform bidding, budget ≈ ₹500–1500/mo, north star = steady good-rate quality clients.

---

## 1. Client Finding — Engines A (inbound/bid) + B (outbound)

| Tool | Repo / Source | What it does | Tier | Where it slots |
|---|---|---|---|---|
| **Upwork-AI-jobs-applier** | kaymen99/Upwork-AI-jobs-applier | LangGraph: scrape Upwork → score (7/10 gate) → personalized cover letters → interview prep | 🟢 CORE | Engine A base (scorer + proposal writer) |
| **sales-outreach-automation-langgraph** | kaymen99/sales-outreach-automation-langgraph | LangGraph + Gemini: research lead (LinkedIn/site/news/pain) → personalized outreach → CRM | 🟢 CORE | Engine B base (outbound) |
| **JobSpy** | speedyapply/JobSpy | Aggregates Indeed/LinkedIn/Glassdoor/Google/ZipRecruiter jobs in one lib | 🟢 CORE | Engine A job aggregation (replaces 4 scrapers) |
| **google-maps-scraper (gosom)** | gosom/google-maps-scraper | Go, MIT, 36 documented data points (title/address/website/phone/category/...), CLI + Web UI + REST API (async job: POST /api/v1/scrape → poll GET /api/v1/jobs/{id}) | 🟢 CORE | Engine B fuel (local client finder) — implemented in `backend/engine_b/maps_source.py`, requires running the service locally (`docker run gosom/google-maps-scraper`) |
| **google-maps-scraper (omkarcloud)** | omkarcloud/google-maps-scraper | ~~Was a free Python-integrable scraper~~ | 🔴 NO LONGER OPEN-SOURCE (2026-07 finding) | **Pivoted to a closed-source desktop app + paid hosted API** (200 free searches/mo, then paid). The GitHub repo now contains zero source code, only marketing docs. Do not build against this — use gosom above instead. |
| **Bricks** (open-source Clay) | HN/show 45493974 | Local lead enrichment — AI agents + scraping over CSVs | 🟡 PHASE-1.5 | Engine B enrichment |
| **UpworkScribe AI** | AIXerum/Upwork-Auto-Jobs-Applier-using-AI | Alt Upwork applier — classify + tailored proposals + writing-style mimic | 🔵 REFERENCE | Cross-ref vs kaymen99 for better prompts |
| **Upwork Fellow** | Chrome extension | In-browser proposal gen with OpenAI | 🔵 REFERENCE | If we go browser-extension route |
| **Upwork Bot** | — | Job-alert monitor | 🔵 REFERENCE | JobSpy covers this |
| **n8n multi-platform workflow** | n8n.io/workflows/7782 | Monitors Upwork+Freelancer+Guru+PPH → AI proposals → Sheets | 🔵 REFERENCE | No-code alt if we ever drop Python glue |
| **OpenSales** | — | Full AI SDR team (research → real emails) | 🔵 REFERENCE (unverified 2026-07 — no concrete GitHub hits found, re-confirm before relying on it) | Heavy; revisit if scaling outbound |
| **b2b-sdr-agent-template** | iPythoning/b2b-sdr-agent-template | 10-stage SDR pipeline, WhatsApp/Telegram/Email, 4-engine memory | 🟡 PHASE-2 | Memory + multi-channel patterns to study |
| **OpenOutreach** | — | Service+market → LinkedIn leads → emails → outreach | 🔵 REFERENCE (unverified 2026-07 — no concrete GitHub hits found, re-confirm before relying on it) | Engine B alt |
| **Linki** | — | Open-source AI SDR, multichannel LinkedIn + cold email | 🔵 REFERENCE (unverified 2026-07 — no concrete GitHub hits found, re-confirm before relying on it) | Engine B alt |
| **Knotie-AI** | — | Inbound/outbound voice/chat sales agent | 🔵 REFERENCE | Voice outreach experiments |
| **LinkedIn Leads Discover** | — | Seed profile → hundreds of similar prospects | 🔵 REFERENCE | Engine B targeting (needs camoufox) |
| **AI Lead Generator** | — | Scrape LinkedIn → OpenAI scores → best channel | 🔵 REFERENCE | Engine B scoring ideas |
| **OutreachStudio** | — | Cold email platform — sequences, open/reply tracking | 🟡 PHASE-2 | Outbound sequencing + deliverability |
| **Sales Outreach (LangGraph)** | = kaymen99 above | (same as CORE) | 🟢 CORE | — |
| **awesome-ai-lead-generation** | curated list | Master list of lead-gen/enrichment tools | 🔵 REFERENCE | Hunting ground |
| **awesome-ai-agents-for-sales** | curated list | Master list of sales AI agents | 🔵 REFERENCE | Hunting ground |
| **MakeMoneyWithAI** | curated list | AI income projects | 🔵 REFERENCE | Hunting ground |

## 2. Scraping Resilience

| Tool | Repo | What it does | Tier | Slot |
|---|---|---|---|---|
| **camofox-browser** | jo-inc/camofox-browser | Anti-detect Firefox (Camoufox), C++-level fingerprint spoofing, MCP-compatible | 🔵 REFERENCE (unstable) | **2026-07 status: maintainer handoff to CloverLabsAI, latest releases self-described as experimental/not production-ready.** Best raw detection score when it works, but don't depend on it right now. |
| **Patchright** | Playwright-patch (not a separate browser) | ~67% headless-detection reduction, stable, production-ready | 🟢 CORE (targeted) | **New default** for protected scrapes (LinkedIn/Contra/Upwork) while Camoufox is unstable. Weaker than Camoufox on hard targets (Cloudflare/DataDome) but usable now. Vanilla Playwright elsewhere. |

## 3. Reply Handling / Inbox

| Tool | Repo | What it does | Tier | Slot |
|---|---|---|---|---|
| **cloudflare/agentic-inbox** | cloudflare/agentic-inbox | AI agent reads inbound email + acts. Cloudflare Workers + Agents SDK + Durable Objects + R2 | 🟡 PHASE-1.5 (pattern only) | CRM "client replied → suggested response". Stack-locked to CF — rebuild pattern in our stack (Gmail API + Gemini), don't fork. |

## 4. CRM / Pipeline

| Tool | Repo | Tier | Note |
|---|---|---|---|
| **Twenty CRM** | twentyhq/twenty | 🔵 REFERENCE | Overkill to self-host for single-user. Our own SQLite first. Adopt if multi-user/SaaS. |

## 5. Freelance Ops (DEFER until clients exist — YAGNI now, all REFERENCE/PHASE-2)

| Category | Tools | Tier |
|---|---|---|
| Project mgmt | Plane, OpenProject, Worklenz, AppFlowy, Leantime | 🟡 PHASE-2 |
| Contracts / e-sign | DocuSeal, Contract-Builder, The Plain Contract, Open eSignForms, AI Contract Generator | 🟡 PHASE-2 |
| Invoicing / billing | Invoice Ninja, SolidInvoice, InvoiceShelf, Crater, Kill Bill | 🟡 PHASE-2 |
| Client portal / files | Portal, Atrium, ProjectSend, Freelancer Office, Client Portal (onboarding) | 🔵 REFERENCE |
| Time tracking | Kimai, Traggo, ActivityWatch, Wakatime | 🔵 REFERENCE |
| Portfolio / proof | awesome-landing-pages, Testimonials, Cal.com, Docusaurus | 🟡 PHASE-2 (Cal.com useful early for discovery calls) |
| Analytics | PostHog, Plausible, Umami, Matomo, MS Clarity | 🔵 REFERENCE |
| Knowledge base | Outline, BookStack, Wiki.js | 🔵 REFERENCE |
| Automation glue | n8n, Activepieces, Windmill | 🔵 REFERENCE (Python glue first) |
| Email marketing | Listmonk, Mautic | 🔵 REFERENCE (mass-email conflicts with no-spam rule) |

## 6. "Grow Presence" / Content (Phase-2 inbound engine)

| Tool | Repo | What it does | Tier | Trigger to activate |
|---|---|---|---|---|
| **MoneyPrinterTurbo** | harry0703/MoneyPrinterTurbo | Topic → short video (script→stock footage→TTS→subs→render). No GPU. | 🔵 REFERENCE | When building personal-brand/inbound content |
| **VoxCPM / VoxCPM2** | OpenBMB/VoxCPM | Tokenizer-free TTS + voice clone (~0.5B, GPU). | 🔵 REFERENCE | Voice cold-outreach / video VO experiments (Edge-TTS free covers basic needs) |
| **Open Generative AI** | (MuAPI) | 200+ image/video models | 🔵 REFERENCE | Content/marketing visuals |

## 7. Out-of-Scope (parked — unrelated to freelance goal, kept for curiosity)

| Tool | Why parked |
|---|---|
| AutoHedge, Trading Agents, Fincept Terminal | Finance/trading agents — different domain. Reference only for multi-agent architecture patterns. |

---

## 8. New finds (2026-07 audit — not yet tiered into a build slot)

| Tool | Repo / Source | What it does | Tier | Note |
|---|---|---|---|---|
| **Prospeo / FullEnrich** | prospeo.io / fullenrich.com | Free-tier decision-maker email finders (75/mo, 50/mo) | 🔵 REFERENCE | Manual-assist fallback when Bricks can't find a contact — no OSS equivalent exists in this space |
| **PocketFlow cold-email tutorial** | The-Pocket/PocketFlow-Tutorial-Cold-Email-Personalization | Minimalist LLM framework tutorial: prospect → research → "personalization opportunity" analysis → opener | 🔵 REFERENCE | Prompt-structure ideas for Engine B's writer, not a framework swap |
| **MatthewDailey/open-sdr** | GitHub | Company research + lead-gen agent (Firecrawl + Gemini/Anthropic), CLI + MCP server | 🔵 REFERENCE | Closest open-source cousin to Engine B's research step; generic B2B not freelance-specific, stops before personalize→notify→approve→CRM |
| **davidmasse/freelancer-rates** | GitHub | Open dataset + analysis of what drives Upwork freelancer rate/success | 🔵 REFERENCE | The one genuinely open, forkable rate-benchmark dataset found — feeds a future pricing agent |
| **Ever® Jobs™** | ever-jobs/ever-jobs | Aggregates 50+ job/gig sources via ATS APIs (incl. Upwork, RemoteOK) | 🔵 REFERENCE | Employment-board-heavy — filter carefully for freelance-only scope before adopting |

## Hunting Guide — what's worth finding MORE of

✅ Worth hunting: email-finder/verification (decision-maker emails for outbound), Python reply-triage agents, proposal/outreach personalization prompt sets, cold-email deliverability (warmup/spam-check).
🛑 Have enough: job scrapers, video gen, TTS, generic CRMs.
