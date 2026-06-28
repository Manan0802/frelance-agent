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
| **google-maps-scraper** | omkarcloud/google-maps-scraper | 50+ data points (emails/phones) for local businesses; ~10k leads/mo free | 🟢 CORE | Engine B fuel (local client finder) |
| **Bricks** (open-source Clay) | HN/show 45493974 | Local lead enrichment — AI agents + scraping over CSVs | 🟡 PHASE-1.5 | Engine B enrichment |
| **UpworkScribe AI** | AIXerum/Upwork-Auto-Jobs-Applier-using-AI | Alt Upwork applier — classify + tailored proposals + writing-style mimic | 🔵 REFERENCE | Cross-ref vs kaymen99 for better prompts |
| **Upwork Fellow** | Chrome extension | In-browser proposal gen with OpenAI | 🔵 REFERENCE | If we go browser-extension route |
| **Upwork Bot** | — | Job-alert monitor | 🔵 REFERENCE | JobSpy covers this |
| **n8n multi-platform workflow** | n8n.io/workflows/7782 | Monitors Upwork+Freelancer+Guru+PPH → AI proposals → Sheets | 🔵 REFERENCE | No-code alt if we ever drop Python glue |
| **OpenSales** | — | Full AI SDR team (research → real emails) | 🔵 REFERENCE | Heavy; revisit if scaling outbound |
| **b2b-sdr-agent-template** | iPythoning/b2b-sdr-agent-template | 10-stage SDR pipeline, WhatsApp/Telegram/Email, 4-engine memory | 🟡 PHASE-2 | Memory + multi-channel patterns to study |
| **OpenOutreach** | — | Service+market → LinkedIn leads → emails → outreach | 🔵 REFERENCE | Engine B alt |
| **Linki** | — | Open-source AI SDR, multichannel LinkedIn + cold email | 🔵 REFERENCE | Engine B alt |
| **Knotie-AI** | — | Inbound/outbound voice/chat sales agent | 🔵 REFERENCE | Voice outreach experiments |
| **gosom/google-maps-scraper** | gosom | Go-based maps scraper | 🔵 REFERENCE | Alt to omkarcloud |
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
| **camofox-browser** | jo-inc/camofox-browser | Anti-detect Firefox (Camoufox), C++-level fingerprint spoofing, MCP-compatible | 🟢 CORE (targeted) | Use ONLY for protected scrapes (LinkedIn/Contra/Upwork). Vanilla Playwright elsewhere. |

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

## Hunting Guide — what's worth finding MORE of

✅ Worth hunting: email-finder/verification (decision-maker emails for outbound), Python reply-triage agents, proposal/outreach personalization prompt sets, cold-email deliverability (warmup/spam-check).
🛑 Have enough: job scrapers, video gen, TTS, generic CRMs.
