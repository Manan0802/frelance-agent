# 🚀 FREELANCING AGENT — COMPLETE PRD
## Product Requirements Document v1.0
**Owner:** Manan | **Status:** Pre-Build | **Last Updated:** June 2026

---

## 📌 TABLE OF CONTENTS
1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Success Metrics](#3-goals--success-metrics)
4. [System Overview & Architecture](#4-system-overview--architecture)
5. [Module Specifications (Detailed)](#5-module-specifications)
   - 5.1 Lead Finder Agent
   - 5.2 Scorer / Qualifier Agent
   - 5.3 Proposal Writer Agent
   - 5.4 Pricing Helper Agent
   - 5.5 CRM / Tracker Agent
   - 5.6 Notification Agent
   - 5.7 Dashboard (Frontend)
6. [Data Models & Schema](#6-data-models--schema)
7. [Tech Stack (Justified)](#7-tech-stack)
8. [API Integrations & Data Sources](#8-api-integrations--data-sources)
9. [Portfolio Context System](#9-portfolio-context-system)
10. [LangGraph Agent Flow](#10-langgraph-agent-flow)
11. [Daily Run Flow (End-to-End)](#11-daily-run-flow)
12. [Notification System Design](#12-notification-system-design)
13. [Hard Constraints & Rules](#13-hard-constraints--rules)
14. [Open Source Tools to Research](#14-open-source-tools-to-research)
15. [Relevant MCPs to Integrate](#15-relevant-mcps)
16. [Phase-wise Build Plan](#16-phase-wise-build-plan)
17. [Folder Structure](#17-folder-structure)
18. [Environment Variables](#18-environment-variables)
19. [Known Risks & Mitigations](#19-known-risks--mitigations)
20. [Future Scope (Phase 2+)](#20-future-scope)

---

## 1. EXECUTIVE SUMMARY

**Freelancing Agent** is a personal AI-powered client acquisition middleware system. It sits between Manan and freelancing platforms — scanning 100+ job listings daily, qualifying the best ones, drafting highly personalized proposals, suggesting smart pricing, and tracking all outreach — all while Manan only spends 20 minutes/day on final review + send.

> **Core Philosophy:** Agent does 90% of the work. Manan approves. Auto-send never happens.

**Target:** ₹50k/month side income initially → scale as income stabilizes.  
**Timeline:** First client ASAP.  
**Platforms:** Upwork, LinkedIn, Twitter/X, RemoteOK, Freelancer.com, Contra, Fiverr, We Work Remotely.

---

## 2. PROBLEM STATEMENT

Manual freelancing is broken for a working professional:
- **Time drain:** Scrolling 200+ listings to find 8 worth-it ones = 2-3 hours wasted daily
- **Generic proposals:** Copy-paste templates get ignored; personalization takes 30 min per proposal
- **Pricing confusion:** No benchmark → either undersell or lose the bid
- **Follow-up chaos:** No system → leads go cold, missed replies
- **Context switching:** Managing job hunt + work job + building projects = burnout

**Current state:** 0 freelancing income, 0 structured outreach, profiles not set up.  
**Desired state:** Passive lead engine running daily, Manan reviews curated list + sends.

---

## 3. GOALS & SUCCESS METRICS

### Primary Goals
| Goal | Metric | Target |
|------|--------|--------|
| Income | Monthly freelance earnings | ₹50k/month |
| Efficiency | Time spent on client acquisition | < 20 min/day |
| Lead Quality | % of shown leads that get proposals sent | > 60% |
| Conversion | Proposals sent → client reply rate | > 15% |
| First client | Days to first paid project | < 45 days |

### Secondary Goals
- Build a reusable portfolio context system (master JSON)
- ATS-ready resume integrated into proposal writer
- Zero manual platform browsing

---

## 4. SYSTEM OVERVIEW & ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FREELANCING AGENT SYSTEM                     │
│                                                                     │
│   ┌─────────────┐     ┌──────────────┐     ┌──────────────────┐   │
│   │  SCHEDULER  │────▶│  ORCHESTRATOR │────▶│   LEAD FINDER    │   │
│   │ (APScheduler│     │  (LangGraph   │     │   AGENT          │   │
│   │  / Manual)  │     │   StateGraph) │     │  (Multi-Platform)│   │
│   └─────────────┘     └──────────────┘     └────────┬─────────┘   │
│                               │                      │              │
│                               ▼                      ▼              │
│                    ┌──────────────────┐    ┌─────────────────┐    │
│                    │  SCORER/QUALIFIER │    │  Raw Leads DB   │    │
│                    │      AGENT       │    │  (SQLite/       │    │
│                    │                  │    │   Supabase)     │    │
│                    └────────┬─────────┘    └─────────────────┘    │
│                             │                                       │
│                             ▼                                       │
│                    ┌──────────────────┐                            │
│                    │  PROPOSAL WRITER │◀─── Portfolio Context JSON │
│                    │      AGENT       │◀─── Resume (ATS Updated)   │
│                    │  + PRICING AGENT │◀─── Past Proposals DB      │
│                    └────────┬─────────┘                            │
│                             │                                       │
│                             ▼                                       │
│                    ┌──────────────────┐                            │
│                    │  NOTIFICATION    │──▶ WhatsApp (Twilio)       │
│                    │      AGENT       │──▶ Email (Gmail SMTP)      │
│                    └────────┬─────────┘                            │
│                             │                                       │
│                             ▼                                       │
│                    ┌──────────────────┐                            │
│   MANAN ◀─────────│    DASHBOARD     │                            │
│   (Review+Approve) │  (React + FastAPI│                            │
│                    │   + WebSockets)  │                            │
│                    └────────┬─────────┘                            │
│                             │                                       │
│                             ▼ (After Manan Approves)               │
│                    ┌──────────────────┐                            │
│                    │   CRM / TRACKER  │──▶ Follow-up Drafts        │
│                    │      AGENT       │──▶ Status Updates          │
│                    │                  │──▶ Negotiation Tracking    │
│                    └──────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
```

### High-Level Data Flow
```
Platforms → Lead Finder → Raw Leads DB
Raw Leads → Scorer → Scored + Filtered Leads
Filtered Leads + Portfolio Context → Proposal Writer → Draft Proposals
Draft Proposals + Market Data → Pricing Agent → Price-Tagged Proposals
Everything → Notification Agent → Manan's WhatsApp + Email
Manan reviews Dashboard → Approves/Edits/Rejects
Approved → CRM Tracker logs → Follow-up queue
```

---

## 5. MODULE SPECIFICATIONS

---

### 5.1 LEAD FINDER AGENT

**Purpose:** Scan all freelancing platforms and collect relevant job listings daily.

#### Platforms & Methods

| Platform | Method | Endpoint / Tool | Reliability |
|----------|--------|-----------------|-------------|
| RemoteOK | Public JSON API | `https://remoteok.com/api` | ✅ Free, stable |
| We Work Remotely | RSS Feed | `https://weworkremotely.com/categories/remote-programming-jobs.rss` | ✅ Free |
| Freelancer.com | Official API | `https://www.freelancer.com/api/docs` (needs registration) | ✅ Free tier |
| Upwork | RSS Feed | `https://www.upwork.com/ab/feed/jobs/rss?...` | ⚠️ Limited, needs query params |
| LinkedIn Jobs | Playwright scraping | Custom scraper | ⚠️ Rate limits |
| Twitter/X | Twitter API v2 | Search tweets: `#hiring`, `#freelance`, `need developer` | ⚠️ Free tier = 500k tweets/month |
| Contra | Playwright scraping | `contra.com/opportunities` | ⚠️ No public API |
| Fiverr | No active scanning | Fiverr = inbound only, optimize profile separately | ℹ️ N/A for finder |
| Google Jobs | SerpAPI / JobSpy | `JobSpy` Python library | ✅ Aggregates multiple |

#### Search Keywords per Skill Category

```python
SEARCH_QUERIES = {
    "ai_ml": [
        "LangGraph developer", "LangChain developer", "RAG pipeline",
        "AI agent developer", "multi-agent system", "OpenAI integration",
        "chatbot developer", "NLP engineer", "agentic AI", "LLM integration",
        "vector database", "Pinecone Chroma", "AI automation"
    ],
    "full_stack": [
        "MERN stack developer", "React developer", "Node.js backend",
        "full stack web developer", "MongoDB Express React",
        "Next.js developer", "REST API developer"
    ],
    "fintech": [
        "fintech developer", "trading platform", "portfolio tracker",
        "stock market app", "financial dashboard", "payment integration",
        "investment app", "wealth management app"
    ],
    "data_science": [
        "data scientist", "Python data analysis", "pandas numpy",
        "machine learning engineer", "data pipeline", "ETL developer",
        "data visualization", "Power BI Tableau developer"
    ],
    "general_web": [
        "website developer", "web developer India", "React website",
        "landing page developer", "portfolio website", "business website"
    ]
}
```

#### Lead Finder Output Schema
```python
class RawLead(BaseModel):
    id: str                    # UUID generated
    source_platform: str       # "remoteok" | "upwork" | "linkedin" | etc.
    title: str                 # Job title
    description: str           # Full job description
    budget_raw: str            # Raw budget string e.g. "$500-$1000"
    budget_min: float | None   # Parsed minimum
    budget_max: float | None   # Parsed maximum
    budget_type: str           # "fixed" | "hourly" | "unknown"
    client_name: str | None
    client_location: str | None
    client_rating: float | None
    client_reviews_count: int | None
    payment_verified: bool | None
    skills_required: list[str]
    url: str                   # Direct link to listing
    posted_at: datetime
    fetched_at: datetime
    raw_json: dict             # Full original response stored
```

#### Deduplication Logic
- Hash = `SHA256(title + client_name + platform)`
- If hash exists in DB within last 7 days → skip
- Cross-platform deduplication: same job posted on multiple sites → keep highest quality source

---

### 5.2 SCORER / QUALIFIER AGENT

**Purpose:** Score every raw lead across multiple dimensions. Show Manan only top 8-10.

#### Scoring Dimensions

```
TOTAL SCORE = weighted sum of all dimensions (0-100)
```

| Dimension | Weight | Scoring Logic |
|-----------|--------|---------------|
| Skill Match | 30% | LLM analyzes description vs. Manan's skills JSON → 0-100 match % |
| Budget Quality | 25% | Dynamic: US client $500+ = high, Indian ₹5k = low |
| Client Legitimacy | 20% | Payment verified + reviews count + rating |
| Project Clarity | 15% | Is scope clear? Vague "build me an app" = low |
| Competition Level | 10% | How many proposals already? (if available) |

#### Auto-Reject Rules (Hard Filters — Agent Drops These Without Showing)
```python
AUTO_REJECT_CONDITIONS = [
    "budget < $30 AND client_location = 'IN'",          # Price war
    "budget < $50 AND type = 'fixed'",                  # Underpaying
    "description contains ['logo design', 'video edit', 'SEO only', 'content writing']",
    "client_reviews_count < 0 AND payment_verified = False",  # Zero credibility
    "title contains ['urgent', '2 hours', 'asap cheap']",     # Red flags
    "duplicate_score > 0.85",                           # Near-duplicate listing
    "job_posted_at < now() - 5 days",                   # Too old
]
```

#### Red Flag Detection (LLM-powered)
LLM reads description and flags:
- "Work first, payment later"
- Unrealistic scope ("Build Facebook in 3 days")
- No clear deliverable
- Competitor dumping ("Other devs quoted $50")
- Suspicious phrasing patterns

#### Scorer Output Schema
```python
class ScoredLead(RawLead):
    score_total: float             # 0-100
    score_skill_match: float
    score_budget: float
    score_client_legit: float
    score_clarity: float
    score_competition: float
    red_flags: list[str]           # List of detected red flags
    auto_rejected: bool
    rejection_reason: str | None
    skill_matched: list[str]       # Which of Manan's skills matched
    recommended: bool              # Top 8-10 flag
```

---

### 5.3 PROPOSAL WRITER AGENT

**Purpose:** Write a 100% personalized proposal for each top-scored lead. No templates. No generic openers.

#### Proposal Writing Rules (System Prompt)

```
RULES FOR EVERY PROPOSAL:
1. NEVER start with "Hi, I am Manan..." → Start with the client's problem
2. Address the SPECIFIC problem from job description in line 1
3. Mention ONE specific detail from the job post (shows you read it)
4. Include ONE relevant project from portfolio that matches this job type
5. Mention the tech stack you'll use for THIS specific project
6. Keep it under 200 words for Upwork / 300 words for email
7. End with ONE clear question or call to action
8. Pricing: DO NOT commit in proposal — "Let's discuss scope first"
9. Tone: Confident, peer-to-peer, not sycophantic
10. DO NOT say: "I am perfect for this", "I have 5 years", generic intros
```

#### Proposal Template Slots (Dynamic Fill)
```
[CLIENT_PAIN_POINT_OPENER]
[SPECIFIC_JOB_DETAIL_REFERENCE]
[RELEVANT_PORTFOLIO_MATCH]
[PROPOSED_APPROACH_2_LINES]
[TECH_STACK_MENTION]
[CONFIDENCE_CLOSER]
[CALL_TO_ACTION]
```

#### Portfolio Matching Logic
```python
def match_portfolio(job_description: str, portfolio: dict) -> list[dict]:
    """
    Vector-embed job description.
    Vector-embed each portfolio project summary.
    Return top 2 most similar projects.
    """
```

#### Proposal Output Schema
```python
class ProposalDraft(BaseModel):
    id: str
    lead_id: str
    draft_text: str               # The full proposal
    word_count: int
    portfolio_projects_used: list[str]
    tone_score: float             # LLM self-eval: 0-10
    personalization_score: float  # LLM self-eval: 0-10
    version: int                  # 1 = initial, 2+ = edited by Manan
    manan_edits: str | None       # What Manan changed
    status: str                   # "draft" | "approved" | "sent" | "rejected"
    created_at: datetime
```

---

### 5.4 PRICING HELPER AGENT

**Purpose:** Suggest smart pricing for each lead. Not a fixed rate card — dynamic based on context.

#### Pricing Decision Tree

```
INPUT: job description + client_location + budget_raw + competition_level

→ Step 1: Detect client country
    US/UK/Canada/Australia → High rate tier
    Europe → Medium-high tier
    India → Medium tier (but negotiate up)
    Southeast Asia → Medium-low tier

→ Step 2: Project complexity
    Simple website/landing page → $200-500
    MERN full-stack app → $500-2000
    AI/ML integration → $800-3000
    Full agentic system (RAG, LangGraph) → $1500-5000+
    Data pipeline / analysis → $300-1500

→ Step 3: Client's stated budget
    Budget > suggested → Quote at budget level (don't undersell)
    Budget < suggested → Quote 20% above stated (room to negotiate down)
    No budget stated → Quote based on complexity, add "open to discuss"

→ Step 4: Competition check
    Many proposals already → Slightly competitive but don't price war
    Few proposals → Quote full rate confidently

→ OUTPUT: {
    suggested_rate: "$X fixed" or "$X/hr",
    rate_justification: "US client, AI agent scope, low competition",
    negotiation_floor: "$Y (minimum to accept)",
    positioning_note: "Position as AI specialist, not generalist"
}
```

---

### 5.5 CRM / TRACKER AGENT

**Purpose:** Track every proposal from draft → sent → replied → negotiation → won/lost. Generate follow-ups.

#### Lead Lifecycle States
```
FOUND → SCORED → PROPOSAL_DRAFTED → MANAN_APPROVED → SENT → 
VIEWED → REPLIED → IN_NEGOTIATION → WON / LOST / GHOSTED
```

#### Follow-up Logic
```python
FOLLOWUP_RULES = {
    "sent_no_reply": {
        "trigger_days": 3,
        "action": "draft_followup_1",
        "message_type": "gentle_bump"
    },
    "followup1_no_reply": {
        "trigger_days": 7,
        "action": "draft_followup_2", 
        "message_type": "value_add"  # Share a relevant insight/solution
    },
    "followup2_no_reply": {
        "trigger_days": 14,
        "action": "mark_ghosted"
    },
    "in_negotiation": {
        "trigger": "client_counter_offer",
        "action": "draft_negotiation_response"
    }
}
```

#### CRM Schema
```python
class ProposalRecord(BaseModel):
    id: str
    lead_id: str
    platform: str
    job_title: str
    client_name: str
    proposal_sent_at: datetime | None
    proposal_text: str
    price_quoted: str
    status: str                        # lifecycle state
    client_messages: list[dict]        # [{role, content, timestamp}]
    followup_count: int
    next_followup_date: date | None
    outcome: str | None                # "won" | "lost" | "ghosted"
    project_value: float | None        # If won, how much
    notes: str | None
    created_at: datetime
    updated_at: datetime
```

---

### 5.6 NOTIFICATION AGENT

**Purpose:** Push daily digest + real-time alerts to Manan via WhatsApp and Email.

#### Notification Types

| Type | Trigger | Channel | Content |
|------|---------|---------|---------|
| Daily Digest | Every morning 9 AM | WhatsApp + Email | Top 8-10 leads with scores + proposal previews |
| New Urgent Lead | Score > 85, posted < 2 hrs | WhatsApp | Single lead alert with link |
| Client Replied | CRM detects new message | WhatsApp | Client reply + suggested response |
| Follow-up Due | CRM follow-up timer | Email | Lead to follow up + draft message |
| Weekly Summary | Every Sunday | Email | Stats: proposals sent, replies, wins, income |

#### WhatsApp Message Format (Daily Digest)
```
🚀 FREELANCING AGENT DAILY DIGEST
📅 Date: {date}

━━━━━━━━━━━━━━━━━━
TOP LEADS TODAY
━━━━━━━━━━━━━━━━━━

1️⃣ [{score}/100] {job_title}
   💰 Budget: {budget}
   📍 Client: {location} | {reviews} reviews
   🎯 Match: {matched_skills}
   🔗 {url}

2️⃣ [{score}/100] {job_title}
   ...

[Total: X leads found | Y filtered | Z shown]

→ Open Dashboard to review proposals:
   http://localhost:3000 (or deployed URL)
━━━━━━━━━━━━━━━━━━
```

#### Implementation
- **WhatsApp:** Twilio WhatsApp API (free sandbox for testing, $0.005/message production)
- **Email:** Gmail SMTP via `smtplib` (free with Google account)
- **Fallback:** If WhatsApp fails → Email. If Email fails → log to dashboard.

---

### 5.7 DASHBOARD (FRONTEND)

**Purpose:** Central review + approval interface. Where Manan spends his 20 min/day.

#### Pages / Views

**1. Home / Today's Leads**
- Card grid of top 8-10 leads
- Each card shows: score, title, budget, platform, skill match badges
- Click → expands to full job description + proposal draft
- Buttons: ✅ Approve | ✏️ Edit | ❌ Skip
- Inline proposal editor (edit before approve)

**2. Proposals Manager**
- Table view: all proposals sent
- Status column with lifecycle state
- Filter by: platform, status, date, score
- Click proposal → full thread view

**3. CRM / Pipeline**
- Kanban board: SENT → REPLIED → NEGOTIATING → WON/LOST
- Drag-to-move cards
- Each card: client name, project value, last activity

**4. Analytics**
- Proposals sent per week
- Reply rate %
- Win rate %
- Total earned (manually updated)
- Platform performance comparison
- Best-performing proposal style (tracked by which ones got replies)

**5. Settings**
- Portfolio JSON editor (update skills, projects)
- Notification preferences
- Scoring weight tuners
- Auto-reject rules manager
- Manual "Run Agent Now" button

#### Tech
- **Framework:** React + Vite
- **UI:** Tailwind CSS + shadcn/ui
- **State:** Zustand
- **Data fetching:** React Query → FastAPI
- **Real-time:** WebSockets for live status updates

---

## 6. DATA MODELS & SCHEMA

### SQLite Tables (Local Dev → Migrate to Supabase)

```sql
-- Raw leads from all platforms
CREATE TABLE leads (
    id TEXT PRIMARY KEY,
    source_platform TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    budget_min REAL,
    budget_max REAL,
    budget_type TEXT,
    client_name TEXT,
    client_location TEXT,
    client_rating REAL,
    client_reviews_count INTEGER,
    payment_verified INTEGER,
    skills_required TEXT,        -- JSON array
    url TEXT UNIQUE NOT NULL,
    posted_at DATETIME,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    dedup_hash TEXT UNIQUE
);

-- Scoring results
CREATE TABLE scored_leads (
    id TEXT PRIMARY KEY,
    lead_id TEXT REFERENCES leads(id),
    score_total REAL,
    score_skill_match REAL,
    score_budget REAL,
    score_client_legit REAL,
    score_clarity REAL,
    score_competition REAL,
    red_flags TEXT,              -- JSON array
    auto_rejected INTEGER DEFAULT 0,
    rejection_reason TEXT,
    skill_matched TEXT,          -- JSON array
    recommended INTEGER DEFAULT 0,
    scored_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Proposal drafts
CREATE TABLE proposals (
    id TEXT PRIMARY KEY,
    lead_id TEXT REFERENCES leads(id),
    draft_text TEXT NOT NULL,
    word_count INTEGER,
    portfolio_projects_used TEXT, -- JSON array
    tone_score REAL,
    personalization_score REAL,
    price_suggested TEXT,
    price_justification TEXT,
    negotiation_floor TEXT,
    version INTEGER DEFAULT 1,
    manan_edits TEXT,
    status TEXT DEFAULT 'draft',  -- draft|approved|sent|rejected
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- CRM tracking
CREATE TABLE crm_records (
    id TEXT PRIMARY KEY,
    proposal_id TEXT REFERENCES proposals(id),
    lead_id TEXT REFERENCES leads(id),
    platform TEXT,
    job_title TEXT,
    client_name TEXT,
    price_quoted TEXT,
    sent_at DATETIME,
    status TEXT DEFAULT 'sent',
    client_messages TEXT,         -- JSON array of {role, content, ts}
    followup_count INTEGER DEFAULT 0,
    next_followup_date DATE,
    outcome TEXT,                 -- won|lost|ghosted
    project_value REAL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Notifications log
CREATE TABLE notifications (
    id TEXT PRIMARY KEY,
    type TEXT,                    -- daily_digest|urgent_lead|client_reply|followup
    channel TEXT,                 -- whatsapp|email
    content TEXT,
    sent_at DATETIME,
    status TEXT                   -- sent|failed
);

-- Agent run logs
CREATE TABLE agent_runs (
    id TEXT PRIMARY KEY,
    run_type TEXT,                -- auto|manual
    started_at DATETIME,
    completed_at DATETIME,
    leads_found INTEGER,
    leads_rejected INTEGER,
    leads_shown INTEGER,
    proposals_drafted INTEGER,
    status TEXT,                  -- running|completed|failed
    error_message TEXT
);
```

---

## 7. TECH STACK

### Backend & Agent
| Component | Technology | Justification |
|-----------|------------|---------------|
| Agent Orchestration | **LangGraph 0.2+** | Same as SARA — multi-agent StateGraph, familiar |
| LLM | **Groq (Llama 3.3 70B)** | Free tier, fast inference, consistent with NexTrade |
| LLM Fallback | **Gemini 1.5 Flash** | Backup when Groq rate limits hit |
| Backend API | **FastAPI** | Async, fast, Pydantic native, perfect for LangGraph |
| Database | **SQLite → Supabase** | SQLite for local dev, Supabase for prod (free tier) |
| ORM | **SQLAlchemy + Alembic** | Migrations, type-safe queries |
| Scheduler | **APScheduler** | In-process cron, no extra infra |
| Web Scraping | **Playwright (async)** | Handles JS-rendered pages (LinkedIn, Contra) |
| HTTP Client | **httpx** | Async HTTP for APIs |
| RSS Parsing | **feedparser** | For We Work Remotely, Upwork RSS |
| Vector Embeddings | **sentence-transformers** | Portfolio matching, local, free |
| Vector Store | **ChromaDB** | Local vector store for portfolio matching |
| Data Validation | **Pydantic v2** | All schemas |
| Env Management | **python-dotenv** | .env file |

### Frontend
| Component | Technology | Justification |
|-----------|------------|---------------|
| Framework | **React + Vite** | Fast HMR, familiar |
| UI Components | **shadcn/ui + Tailwind** | Clean, customizable |
| State | **Zustand** | Simple, no boilerplate |
| Data Fetching | **React Query** | Cache + async state |
| Real-time | **WebSockets** | Live lead updates |
| Charts | **Recharts** | Analytics page |
| Kanban | **@dnd-kit** | CRM pipeline drag-drop |

### Notifications
| Channel | Technology | Cost |
|---------|------------|------|
| WhatsApp | Twilio WhatsApp API | Sandbox free, ~$0.005/msg prod |
| Email | Gmail SMTP (smtplib) | Free |
| Fallback | Dashboard in-app notification | Free |

### Hosting (Zero Cost)
| Service | Platform | Plan |
|---------|----------|------|
| Backend + Agent | **Railway** | Free tier (500 hrs/month) |
| Frontend | **Vercel** | Free tier |
| Database (prod) | **Supabase** | Free tier (500 MB) |
| Scheduler | Runs inside FastAPI | No extra infra |

---

## 8. API INTEGRATIONS & DATA SOURCES

### 8.1 RemoteOK (Primary — Free & Easy)
```python
import httpx

async def fetch_remoteok(tags: list[str]) -> list[dict]:
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "FreelancingAgent/1.0"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        jobs = resp.json()[1:]  # First item is metadata
        # Filter by tags
        return [j for j in jobs if any(t in j.get('tags', []) for t in tags)]
```

### 8.2 We Work Remotely (RSS — Free)
```python
import feedparser

def fetch_weworkremotely():
    feeds = [
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss"
    ]
    all_entries = []
    for url in feeds:
        feed = feedparser.parse(url)
        all_entries.extend(feed.entries)
    return all_entries
```

### 8.3 Upwork (RSS — Limited)
```
Base URL: https://www.upwork.com/ab/feed/jobs/rss
Query params: q=langgraph+developer&sort=recency
Note: Upwork RSS returns limited data. For full data → apply for Upwork API
Upwork API Application: https://developers.upwork.com/
```

### 8.4 Freelancer.com API
```
Registration: https://developers.freelancer.com/
Endpoint: GET /api/projects/0.1/projects/active/
Auth: OAuth 2.0
Note: Free tier available with rate limits
```

### 8.5 LinkedIn Jobs (Playwright Scraping)
```python
from playwright.async_api import async_playwright

async def scrape_linkedin_jobs(keyword: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&f_WT=2"
        await page.goto(url)
        # Extract job cards
        # NOTE: LinkedIn has anti-scraping. Use rotating user agents + delays
```

### 8.6 Twitter/X API (Job Tweets)
```
API v2 endpoint: GET /2/tweets/search/recent
Query: "(hiring OR #freelance OR need developer) (AI OR LangChain OR React) -is:retweet lang:en"
Free tier: 500k tweets/month read access
Setup: developer.twitter.com → Create App → Bearer Token
```

### 8.7 Contra (Playwright Scraping)
```
URL: https://contra.com/opportunities
Method: Playwright headless browser
Note: No public API. Scrape opportunities page, filter by skill tags.
```

### 8.8 JobSpy Library (Aggregator)
```python
# pip install python-jobspy
from jobspy import scrape_jobs

jobs = scrape_jobs(
    site_name=["indeed", "linkedin", "glassdoor"],
    search_term="LangGraph developer",
    results_wanted=20,
    hours_old=24,
    country_indeed="India"  # or "USA"
)
```

---

## 9. PORTFOLIO CONTEXT SYSTEM

**Purpose:** A structured JSON file that acts as Manan's "brain" for proposal writing. Agent reads this to write personalized, accurate proposals.

### portfolio_context.json (Master File)

```json
{
  "personal": {
    "name": "Manan",
    "title": "AI Engineer & Full-Stack Developer",
    "location": "New Delhi, India",
    "education": "B.Tech Software Engineering, DTU (Delhi Technological University)",
    "current_role": "Software Engineer (Full-Time)",
    "years_experience": 1,
    "tagline": "I build AI agents and full-stack applications that solve real business problems"
  },
  "skills": {
    "ai_ml": ["LangGraph", "LangChain", "RAG pipelines", "Multi-agent systems",
              "FinBERT", "sentence-transformers", "OpenAI API", "Groq", "Gemini API",
              "HuggingFace", "ChromaDB", "Pinecone", "vector databases"],
    "full_stack": ["React", "Node.js", "Express", "MongoDB", "FastAPI", "Python",
                   "REST APIs", "WebSockets", "Next.js"],
    "data": ["Pandas", "NumPy", "Matplotlib", "Data preprocessing", "EDA"],
    "tools": ["Git", "Docker", "Railway", "Vercel", "Supabase", "Playwright"]
  },
  "projects": [
    {
      "name": "SARA",
      "type": "ai_ml",
      "description": "LangGraph-based multi-agent system built during AI Engineering internship at IndiaMART. Handles complex multi-step workflows with agent routing and state management.",
      "tech": ["LangGraph", "Python", "Groq", "RAG"],
      "outcome": "Built in production, handles real business queries at IndiaMART",
      "pitch_for": ["AI agent", "LangGraph", "multi-agent", "automation", "agentic AI"],
      "url": null
    },
    {
      "name": "Client Website (CodewellImages)",
      "type": "full_stack",
      "description": "Built a live business website for a professional photography client. Clean, responsive, production-deployed.",
      "tech": ["React", "Node.js"],
      "outcome": "Live at codewellimages.in",
      "pitch_for": ["website", "web development", "business site", "portfolio site"],
      "url": "https://codewellimages.in"
    },
    {
      "name": "InvestMate",
      "type": "fintech",
      "description": "MERN stack + Gemini AI portfolio tracker with AI-powered investment insights.",
      "tech": ["MongoDB", "Express", "React", "Node.js", "Gemini API"],
      "outcome": "Full-stack fintech app with AI integration",
      "pitch_for": ["fintech", "investment app", "portfolio tracker", "MERN", "financial dashboard"],
      "url": null
    },
    {
      "name": "ShopLens",
      "type": "ai_ml",
      "description": "Visual product search engine using CLIP + FAISS for similarity search.",
      "tech": ["CLIP", "FAISS", "Python", "computer vision"],
      "outcome": "E-commerce visual search capability",
      "pitch_for": ["computer vision", "image search", "e-commerce AI", "similarity search"],
      "url": null
    },
    {
      "name": "Bachatt",
      "type": "fintech",
      "description": "Personal finance platform using Sarvam-2B (Indian multilingual AI) for financial guidance in Hindi/English.",
      "tech": ["Sarvam-2B", "Qwen", "FastAPI", "React"],
      "outcome": "Multilingual Indian fintech AI app",
      "pitch_for": ["fintech", "multilingual AI", "Indian market", "personal finance"],
      "url": "https://bachatt.app"
    }
  ],
  "past_clients": [
    {
      "name": "CodewellImages",
      "type": "photography business",
      "deliverable": "Business website",
      "testimonial": null
    }
  ],
  "availability": "10-15 hours per week (alongside full-time job)",
  "preferred_project_duration": "1 week to 2 months",
  "communication": "Available on email and WhatsApp, respond within 24 hours"
}
```

---

## 10. LANGGRAPH AGENT FLOW

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AgentState(TypedDict):
    run_id: str
    raw_leads: List[dict]
    scored_leads: List[dict]
    top_leads: List[dict]
    proposals: List[dict]
    pricing: List[dict]
    notifications_sent: bool
    errors: List[str]

# Node definitions
async def lead_finder_node(state: AgentState) -> AgentState:
    """Fetch leads from all platforms concurrently"""
    # Parallel fetch using asyncio.gather
    results = await asyncio.gather(
        fetch_remoteok(SEARCH_QUERIES["ai_ml"]),
        fetch_weworkremotely(),
        fetch_upwork_rss(),
        scrape_linkedin_jobs("LangGraph developer"),
        # ... etc
    )
    state["raw_leads"] = deduplicate(flatten(results))
    return state

async def scorer_node(state: AgentState) -> AgentState:
    """Score and filter leads"""
    scored = []
    for lead in state["raw_leads"]:
        score = await score_lead(lead, PORTFOLIO_CONTEXT)
        if not score.auto_rejected:
            scored.append(score)
    state["scored_leads"] = sorted(scored, key=lambda x: x.score_total, reverse=True)
    state["top_leads"] = state["scored_leads"][:10]  # Top 10 only
    return state

async def proposal_writer_node(state: AgentState) -> AgentState:
    """Write personalized proposals for top leads"""
    proposals = []
    for lead in state["top_leads"]:
        proposal = await write_proposal(lead, PORTFOLIO_CONTEXT)
        proposals.append(proposal)
    state["proposals"] = proposals
    return state

async def pricing_node(state: AgentState) -> AgentState:
    """Add pricing suggestions to each proposal"""
    for i, proposal in enumerate(state["proposals"]):
        pricing = await suggest_pricing(state["top_leads"][i])
        state["proposals"][i]["pricing"] = pricing
    return state

async def notification_node(state: AgentState) -> AgentState:
    """Send daily digest notification"""
    await send_whatsapp_digest(state["top_leads"], state["proposals"])
    await send_email_digest(state["top_leads"], state["proposals"])
    state["notifications_sent"] = True
    return state

# Build graph
builder = StateGraph(AgentState)
builder.add_node("lead_finder", lead_finder_node)
builder.add_node("scorer", scorer_node)
builder.add_node("proposal_writer", proposal_writer_node)
builder.add_node("pricing", pricing_node)
builder.add_node("notifier", notification_node)

builder.set_entry_point("lead_finder")
builder.add_edge("lead_finder", "scorer")
builder.add_edge("scorer", "proposal_writer")
builder.add_edge("proposal_writer", "pricing")
builder.add_edge("pricing", "notifier")
builder.add_edge("notifier", END)

graph = builder.compile()
```

---

## 11. DAILY RUN FLOW (END-TO-END)

```
09:00 AM — APScheduler triggers agent run
    ↓
LEAD FINDER runs concurrently across all platforms
  - RemoteOK API → ~50 leads
  - We Work Remotely RSS → ~20 leads
  - Upwork RSS → ~30 leads
  - LinkedIn scraper → ~30 leads
  - Twitter search → ~20 leads
  - Freelancer.com API → ~30 leads
  - Contra scraper → ~20 leads
  = ~200 raw leads found
    ↓
DEDUPLICATION → ~150 unique leads
    ↓
AUTO-REJECT FILTER → drop price wars, irrelevant, too old
  = ~40-50 leads survive
    ↓
SCORER runs on all 40-50 leads
  - Skill match (LLM + portfolio JSON)
  - Budget analysis
  - Client legitimacy check
  - Red flag detection
  - Scoring 0-100
    ↓
TOP 8-10 LEADS SELECTED (score ranked)
    ↓
PROPOSAL WRITER → personalized draft for each
  - Portfolio matching
  - LLM writing with strict rules
  - Self-evaluation scoring
    ↓
PRICING AGENT → suggests rate for each
    ↓
09:30 AM — NOTIFICATION SENT
  WhatsApp → daily digest with top leads
  Email → same digest with full proposal previews
    ↓
MANAN opens Dashboard (20 min review)
  - Reads each lead card
  - Reads proposal draft
  - Edits if needed
  - Clicks "Approve" → marks status as approved
  - MANUALLY COPIES + SENDS on platform (no auto-send ever)
    ↓
CRM TRACKER logs:
  - Which proposals sent
  - Timestamp
  - Platform
  - Schedules follow-up in 3 days
    ↓
THROUGHOUT DAY — CRM agent monitors:
  - New client replies → WhatsApp alert
  - Follow-up due → reminder
  - Negotiation updates → draft response
```

---

## 12. NOTIFICATION SYSTEM DESIGN

### WhatsApp Setup (Twilio)
```python
from twilio.rest import Client

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
WHATSAPP_FROM = "whatsapp:+14155238886"  # Twilio sandbox
WHATSAPP_TO = f"whatsapp:{os.getenv('MANAN_PHONE')}"

async def send_whatsapp(message: str):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_=WHATSAPP_FROM,
        to=WHATSAPP_TO
    )
```

### Email Setup (Gmail SMTP)
```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

async def send_email(subject: str, html_body: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = os.getenv("GMAIL_USER")
    msg["To"] = os.getenv("GMAIL_USER")  # Send to self
    msg.attach(MIMEText(html_body, "html"))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.getenv("GMAIL_USER"), os.getenv("GMAIL_APP_PASSWORD"))
        server.sendmail(os.getenv("GMAIL_USER"), os.getenv("GMAIL_USER"), msg.as_string())
```

---

## 13. HARD CONSTRAINTS & RULES

```
🔴 ABSOLUTE NON-NEGOTIABLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. AUTO-SEND = NEVER
   Agent drafts. Manan sends. Always. No exceptions.
   Reason: Upwork ToS = ban. Spam = reputation damage.

2. GENERIC PROPOSALS = NEVER
   LLM self-evaluates personalization score.
   If personalization_score < 7/10 → regenerate.

3. MASS COLD SPAM = NEVER
   No bulk LinkedIn DM. No email blasts.
   Only targeted, curated outreach.

4. DATA PRIVACY
   Portfolio JSON, resume, client data → stored locally only.
   Never sent to third-party APIs except Groq/Gemini (no PII).

5. QUALITY OVER QUANTITY
   Better 3 excellent proposals than 20 mediocre ones.
   Scorer must be strict — top 10 ONLY.

6. TRANSPARENT PRICING
   Pricing suggestion is recommendation, not final.
   Manan decides final price always.
```

---

## 14. OPEN SOURCE TOOLS TO RESEARCH

Claude Code should research and evaluate these for integration:

### Lead Finding
| Library | Purpose | Link |
|---------|---------|------|
| **python-jobspy** | Scrapes Indeed, LinkedIn, Glassdoor, ZipRecruiter | `pip install python-jobspy` |
| **linkedin-jobs-scraper** | LinkedIn job scraper (Node.js) | github.com/spinlud/linkedin-jobs-scraper |
| **upwork-python** | Unofficial Upwork API wrapper | github.com/upwork/python-upwork |
| **feedparser** | RSS/Atom feed parser | `pip install feedparser` |
| **playwright** | Async browser automation for scraping | `pip install playwright` |

### Agent / LLM
| Library | Purpose | Link |
|---------|---------|------|
| **langgraph** | Agent orchestration | `pip install langgraph` |
| **langchain** | LLM tools, memory, chains | `pip install langchain` |
| **groq** | Groq LLM client | `pip install groq` |
| **sentence-transformers** | Portfolio embedding/matching | `pip install sentence-transformers` |
| **chromadb** | Local vector store | `pip install chromadb` |

### Backend / Infra
| Library | Purpose | Link |
|---------|---------|------|
| **fastapi** | API backend | `pip install fastapi uvicorn` |
| **sqlalchemy** | ORM | `pip install sqlalchemy` |
| **alembic** | DB migrations | `pip install alembic` |
| **apscheduler** | Cron scheduling | `pip install apscheduler` |
| **pydantic** | Data validation | Already in FastAPI |
| **httpx** | Async HTTP client | `pip install httpx` |
| **twilio** | WhatsApp notifications | `pip install twilio` |
| **python-dotenv** | Environment vars | `pip install python-dotenv` |

### Frontend
| Library | Purpose |
|---------|---------|
| **react + vite** | Frontend framework |
| **tailwindcss** | Styling |
| **shadcn/ui** | Components |
| **zustand** | State management |
| **react-query** | Data fetching |
| **recharts** | Analytics charts |
| **@dnd-kit/core** | Kanban drag-and-drop |

---

## 15. RELEVANT MCPs

These MCPs can enhance the agent — Claude Code should check availability:

| MCP | Use Case | Status |
|-----|----------|--------|
| **Gmail MCP** | Read client replies from email, send follow-ups | ✅ Connected |
| **Google Calendar MCP** | Schedule follow-up reminders | ✅ Connected |
| **LinkedIn MCP** | If available — search jobs, send connection requests | 🔍 Research needed |
| **Notion MCP** | Alternative CRM storage in Notion | 🔍 Research needed |
| **Supabase MCP** | Database management in production | 🔍 Research needed |
| **Slack MCP** | Alternative notification channel | 🔍 Research needed |
| **Postman MCP** | Test all API integrations | ✅ Connected |

---

## 16. PHASE-WISE BUILD PLAN

### Phase 0 — Pre-Build Setup (Week 1)
- [ ] ATS-update resume
- [ ] Create portfolio_context.json (master file)
- [ ] Create Upwork account + profile
- [ ] Create Contra account
- [ ] Create Freelancer.com account + API keys
- [ ] Set up Twitter Developer account → API keys
- [ ] Set up Twilio account → WhatsApp sandbox
- [ ] Gmail App Password generate karo
- [ ] Railway account setup

### Phase 1A — Core Agent (Week 2-3)
- [ ] FastAPI backend skeleton
- [ ] SQLite database + all tables
- [ ] LangGraph graph structure
- [ ] RemoteOK + We Work Remotely fetchers (easiest, no auth)
- [ ] Basic scorer with hardcoded weights
- [ ] Basic proposal writer with portfolio JSON
- [ ] Gmail notification (email digest)
- [ ] Test end-to-end with 2 platforms

### Phase 1B — Full Lead Sources (Week 3-4)
- [ ] Upwork RSS fetcher
- [ ] Freelancer.com API integration
- [ ] LinkedIn Playwright scraper
- [ ] Twitter/X API integration
- [ ] Contra Playwright scraper
- [ ] JobSpy integration
- [ ] Deduplication logic
- [ ] APScheduler (daily cron)

### Phase 1C — Intelligence Layer (Week 4-5)
- [ ] LLM-powered scorer (Groq Llama 3.3)
- [ ] Red flag detection
- [ ] Personalization scorer on proposals
- [ ] Portfolio vector embedding + matching
- [ ] Pricing suggestion agent
- [ ] WhatsApp notification (Twilio)

### Phase 1D — Dashboard (Week 5-6)
- [ ] React + Vite frontend
- [ ] Lead review cards
- [ ] Proposal editor
- [ ] Approve/Skip buttons
- [ ] WebSocket real-time updates
- [ ] CRM table view
- [ ] Analytics page (basic)

### Phase 1E — CRM & Follow-ups (Week 6-7)
- [ ] Full lifecycle tracking
- [ ] Follow-up draft generation
- [ ] Follow-up reminder notifications
- [ ] Negotiation response drafts
- [ ] Weekly summary email

### Phase 2 — Future (Post first client)
- [ ] Delivery side: scope → task breakdown
- [ ] Timeline generator
- [ ] Invoice generator
- [ ] Client onboarding flow
- [ ] Fiverr profile optimizer
- [ ] LinkedIn content posting agent (grow presence)

---

## 17. FOLDER STRUCTURE

```
freelancing-agent/
├── backend/
│   ├── main.py                    # FastAPI app entry
│   ├── config.py                  # Settings, env vars
│   ├── database/
│   │   ├── models.py              # SQLAlchemy models
│   │   ├── connection.py          # DB connection
│   │   └── migrations/            # Alembic migrations
│   ├── agents/
│   │   ├── orchestrator.py        # LangGraph StateGraph
│   │   ├── lead_finder/
│   │   │   ├── __init__.py
│   │   │   ├── remoteok.py
│   │   │   ├── weworkremotely.py
│   │   │   ├── upwork.py
│   │   │   ├── freelancer.py
│   │   │   ├── linkedin.py
│   │   │   ├── twitter.py
│   │   │   ├── contra.py
│   │   │   └── jobspy_source.py
│   │   ├── scorer/
│   │   │   ├── __init__.py
│   │   │   ├── scorer.py
│   │   │   └── red_flag_detector.py
│   │   ├── proposal_writer/
│   │   │   ├── __init__.py
│   │   │   ├── writer.py
│   │   │   └── portfolio_matcher.py
│   │   ├── pricing/
│   │   │   ├── __init__.py
│   │   │   └── pricing_agent.py
│   │   ├── crm/
│   │   │   ├── __init__.py
│   │   │   ├── tracker.py
│   │   │   └── followup_generator.py
│   │   └── notifier/
│   │       ├── __init__.py
│   │       ├── whatsapp.py
│   │       └── email_notifier.py
│   ├── api/
│   │   ├── leads.py               # GET /leads, PATCH /leads/:id
│   │   ├── proposals.py           # GET /proposals, PATCH /proposals/:id/approve
│   │   ├── crm.py                 # GET /crm, PATCH /crm/:id
│   │   ├── analytics.py           # GET /analytics
│   │   └── agent.py               # POST /agent/run
│   ├── scheduler/
│   │   └── jobs.py                # APScheduler setup
│   └── utils/
│       ├── deduplication.py
│       └── text_processing.py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx           # Today's leads
│   │   │   ├── Proposals.jsx      # Proposals manager
│   │   │   ├── CRM.jsx            # Pipeline kanban
│   │   │   ├── Analytics.jsx      # Stats
│   │   │   └── Settings.jsx       # Config
│   │   ├── components/
│   │   │   ├── LeadCard.jsx
│   │   │   ├── ProposalEditor.jsx
│   │   │   └── PipelineBoard.jsx
│   │   └── store/
│   │       └── useStore.js        # Zustand store
│   └── package.json
├── data/
│   ├── portfolio_context.json     # Master portfolio file
│   └── freelancing_agent.db      # SQLite database
├── .env                           # All secrets
├── requirements.txt
├── README.md
└── docker-compose.yml             # Optional: containerize
```

---

## 18. ENVIRONMENT VARIABLES

```env
# LLM
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key

# Freelancing Platform APIs
UPWORK_CLIENT_ID=
UPWORK_CLIENT_SECRET=
FREELANCER_CLIENT_ID=
FREELANCER_CLIENT_SECRET=
TWITTER_BEARER_TOKEN=
TWITTER_API_KEY=
TWITTER_API_SECRET=

# Notifications
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
MANAN_PHONE=+91XXXXXXXXXX
GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Database
DATABASE_URL=sqlite:///./data/freelancing_agent.db
SUPABASE_URL=                          # For production
SUPABASE_KEY=                          # For production

# App
SECRET_KEY=random_secret_for_jwt
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
PORTFOLIO_CONTEXT_PATH=./data/portfolio_context.json

# Scheduler
DAILY_RUN_TIME=09:00                   # 24hr format
TIMEZONE=Asia/Kolkata
```

---

## 19. KNOWN RISKS & MITIGATIONS

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LinkedIn blocks scraper | High | Medium | Use rotating user-agents, random delays, Playwright stealth mode |
| Upwork RSS limited data | Medium | Medium | Apply for Upwork API access in parallel |
| Groq rate limits | Low | Low | Gemini fallback configured |
| Twilio WhatsApp sandbox limitations | Medium | Low | Use sandbox for testing, upgrade for prod |
| Platform changes break scrapers | Medium | High | Modular scraper design — each platform isolated |
| Low lead quality initially | Medium | Medium | Tune scoring weights based on real data after 1 week |
| Proposal too generic (LLM hallucination) | Low | High | Self-evaluation score + regeneration loop |
| Railway free tier limit (500 hrs) | Medium | Low | Scale to paid when income justifies |

---

## 20. FUTURE SCOPE (Phase 2+)

These are explicitly OUT OF SCOPE for Phase 1 — build these after first client:

1. **Delivery Side Management**
   - Project scope → auto task breakdown
   - Timeline with milestones
   - Client update email drafts

2. **Fiverr Inbound Optimization**
   - Gig keyword optimizer
   - Fiverr profile A/B tester

3. **LinkedIn Content Agent**
   - Weekly post drafts to grow visibility
   - Connection request personalization at scale

4. **Invoice Generator**
   - Auto-generate invoice PDF on project win
   - Payment follow-up automation

5. **Rate Card Evolution**
   - Track wins/losses to auto-tune pricing
   - ML model on own data: "what price wins most?"

6. **Multi-User / SaaS (far future)**
   - Only if Manan decides to productize

---

## 📎 APPENDIX

### Minimum Viable Agent (If you want to start TODAY)
Build this in 3 days, add more later:
1. RemoteOK + We Work Remotely fetcher only
2. Hardcoded scorer (keyword matching, no LLM)
3. LLM proposal writer with portfolio JSON
4. Gmail email digest

This gives you a working system while you build the full version.

### Key Research Tasks for Claude Code
1. `python-jobspy` — test if it returns usable data for AI jobs
2. Playwright stealth mode for LinkedIn — research anti-detection
3. Upwork RSS query parameters — what search terms work
4. Twilio WhatsApp sandbox join flow — test before build
5. APScheduler in FastAPI — best pattern for background scheduling
6. sentence-transformers — best model for short text matching (portfolio vs job desc)
7. LangGraph 0.2 StateGraph — check latest API changes

---

*PRD Version 1.0 — Built for Claude Code consumption*
*Next Step: Phase 0 setup + Phase 1A build*
