# 🕵️ Insider / Hidden-Gig Sources (research)

Non-obvious channels where real gigs + client-acquisition intel flow — the stuff that isn't on
the big marketplaces. These convert well for a cold-start dev because they're **direct** (judge the
work, no platform gate) and **lower-competition** than Upwork. Tagged by how the agent can monitor.

Access: 🟢 free API (agent auto-monitors) · 🟡 scrape/community (careful) · 🔵 manual-assist (agent drafts, human engages).

---

## 💎 The gem: HN "Freelancer? Seeking freelancer?" monthly thread
> **SCOPE:** target the **freelance** thread, NOT the jobs one. Use *"Freelancer? Seeking freelancer?"*
> (project/contract work). Skip *"Ask HN: Who is hiring?"* (full-time employment) — that's the job
> agent's lane, out of scope here.
- **Hacker News monthly thread** — first of every month: *"Ask HN: Freelancer? Seeking freelancer?"*
  - The **SEEKING FREELANCER** entries = businesses/founders wanting project work done = our exact target.
  - **Access: 🟢 free, no-auth [HN Algolia API](https://hn.algolia.com/api)** — query
    `https://hn.algolia.com/api/v1/search?query=freelancer%20seeking%20freelancer&tags=story`,
    then fetch that thread's comments and keep the "SEEKING FREELANCER" ones. Often high-rate
    startup/YC work, AI/dev heavy. **Top-tier freelance source, trivially automatable.**
- **r/forhire monthly + Indie Hackers + WIP** carry similar "seeking dev" posts.

## 🔴 Reddit (monitorable via free API — PRAW)
| Subreddit | Why | Access |
|---|---|---|
| **r/forhire** (~250k) | Biggest freelance hub; `[Hiring]` posts | 🟢 API |
| **r/forhiredevs**, **r/jobbit** | Dev-specific gigs | 🟢 API |
| **r/freelance**, **r/remotejobs**, **r/hiring** | General remote/contract | 🟢 API |
| **r/slavelabour**, **r/DoneDirtCheap** | Small fast gigs (low rate — filter) | 🟢 API |
| **r/startups**, **r/SaaS**, **r/Entrepreneur** | Relationship play — help first, get tagged later | 🟢 API |
| **r/MachineLearning** ("Who's hiring" threads), **r/LLMDevs**, **r/artificial**, **r/LocalLLaMA** | His AI edge; founders needing agents/RAG | 🟢 API |
| Framework subs: **r/nextjs, r/reactjs, r/node** | Occasional gig posts | 🟢 API |

**Agent play:** monitor these for keywords (`AI`, `LangChain`, `agent`, `RAG`, `MERN`, `hiring`,
`need developer`) → feed into Engine A scorer. Reddit's rule = value-first, no spam (matches our constraint).

**2026-07 rate-limit note:** free OAuth tier = 100 req/min, unauthenticated = 10 req/min (tightened
since 2023 API changes) — plenty for polling a handful of subreddits every few minutes at this
project's personal scale, but this is no longer a "true unlimited free" API; keep monitoring frequency
modest.

## 🐦 X / Twitter (monitorable via API v2 recent-search)
- **Search queries** (real-time recent search):
  - `("need" OR "looking for" OR "hiring") ("AI developer" OR "LangChain" OR "RAG" OR "automation" OR "MERN" OR "full stack") -is:retweet lang:en`
  - hashtags: `#hiring #freelance #needdeveloper #buildinpublic #indiehackers`
- **Build-in-public founders** post "need help building X" → warm inbound. Curate an **X List** of
  founders/startups in AI/SaaS; monitor their posts.
- **Access: 🟡 X API v2 — free tier removed Feb 6, 2026**, now pay-per-read (~$0.005/read; legacy paid tiers only for grandfathered accounts). Cheap in absolute terms at this project's low volume, but no longer free — deprioritize until Reddit/HN prove out, or budget ~$1-2/mo explicitly. Scrape remains a 🟡 fallback. Feed hits into Engine B (direct DM draft) / Engine A.

## 🌐 Founder / indie communities (where pre-marketplace gigs appear)
| Community | Why | Access |
|---|---|---|
| **Indie Hackers** | Founders needing MVPs/AI features | 🟡 |
| **YC "Who's Hiring"** (news.ycombinator) | Funded startups, good rates | 🟢 (Algolia) |
| **WIP.co / MegaMaker / Makerlog** | Solo founders, small paid builds | 🔵 |
| **AI/dev Discords & Slacks** (LangChain, LlamaIndex, buildspace, AI collectives) | Gigs posted in #jobs channels | 🔵 |
| **Wellfound / Contra feeds** | (in platform catalog) portfolio-first | 🟡 |

## 🧠 Intel sources (tactics, not gigs — improve conversion)
- Freelance operators on X (share rate/positioning/cold-outreach tactics) — curate a "learn" X List.
- r/freelance + r/Entrepreneur threads on what actually lands clients.
- Newsletters: build-in-public / freelance-ops — mine for tactics + occasional leads.

---

## Integration priority (for the build)
1. **HN Algolia** (🟢 free, no-auth) — monthly "who's hiring / freelancer" threads → **build this first, huge ROI.**
2. **Reddit API (PRAW)** — keyword monitor across the subreddits above → Engine A.
3. **X API v2 recent-search** — hiring-intent queries → Engine A/B (direct).
4. Discord/IndieHackers/WIP — 🔵 manual-assist first (agent drafts, Manan engages).

Each = a small `fetch_<source>()` module (see `PLATFORM_COVERAGE.md` checklist). Rule stays: value-first,
personalized, human approves + sends. No spam, no mass-DM.

## Sources
- [Financial Binder — high-paying freelance gigs on Reddit](https://financialbinder.com/high-paying-freelance-gigs-reddit/)
- [The Hive Index — freelancing subreddits](https://thehiveindex.com/topics/freelancing/platform/reddit/)
- [Libertylancer — best subreddits for freelancers](https://libertylancer.com/best-subreddits-for-freelancers/)
- [Freelancer FAQs — use Twitter/X to find clients](https://www.freelancerfaqs.com/use-twitter-find-clients/)
- [Harlow — freelancers to follow on Twitter](https://meetharlow.com/blog/freelancers-to-follow-on-twitter/)
- [HN Algolia API docs](https://hn.algolia.com/api)
