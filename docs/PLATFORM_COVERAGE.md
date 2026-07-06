# 🌍 Platform Coverage & Expansion Roadmap

**Vision (Manan's words):** volume + quality. Approach ~100 → land ~1 great client.
**National (India) AND International, both.** Personalized per lead — never mass spam;
human always approves + sends.

**SCOPE:** freelance / project-based clients only. Full-time job-hunting is a **separate agent** —
out of scope here. Prioritize freelance marketplaces + gig threads + direct/outbound. The employment
job boards below (RemoteOK/WWR/JobSpy) are kept but **deprioritized** — use only their contract/freelance slices.

**Why this is realistic:** every platform is an isolated, injectable fetcher (~30-50 lines)
that plugs into the engine graph without touching anything else. We proved the pattern with
the sources below; scaling to many platforms = repeat the pattern. The LLM scorer + per-message
self-eval keep quality high even at volume (bad leads auto-rejected, weak messages regenerated).

---

## ✅ Covered now

### Engine A — Inbound (jobs/gigs → proposal)
| Source | Reach | Status |
|---|---|---|
| RemoteOK | International remote | ✅ |
| We Work Remotely | International remote | ✅ |
| **JobSpy** (one lib = 5 platforms) | Indeed + LinkedIn + Glassdoor + Google Jobs + ZipRecruiter — national (country param) + international | ✅ |

### Engine B — Outbound (find businesses → cold pitch)
| Source | Reach | Status |
|---|---|---|
| Google Maps scraper | Local businesses, city/country-targeted (national) | ✅ |

**So ~8 platforms already reachable.** Upwork/Contra/Twitter/Fiverr etc. still to add (below).

---

## 🔜 Planned platforms (each = one small fetcher module)

### Freelance marketplaces
- Upwork (scrape-only — RSS discontinued Aug 2024, no free API), Freelancer.com (API, official Python SDK, access by application review), Contra, Fiverr (inbound/profile), PeoplePerHour, Guru

### Talent / startup boards
- Wellfound (AngelList), YC "Who's Hiring", **India:** Cutshort, Instahyre, Hasjob, Internshala

### Social / direct
- Twitter/X hiring tweets (`#hiring`, "need developer") via API v2 — **free tier removed Feb 2026, now pay-per-read**; deprioritize until Reddit/HN prove out, or budget ~$1-2/mo
- LinkedIn jobs + direct outreach (needs **camoufox** for anti-bot — already in TOOL_REGISTRY)

### Outbound (Engine B) expansion
- Startup/SMB lists for AI-automation pitches, agency directories, more maps categories

---

## National vs International — how it's handled
- **JobSpy**: `country_indeed` param → India-specific or US/global.
- **Google Maps**: queries per city (Delhi, Mumbai, …) = national; any country supported.
- **Scoring**: budget weighted by client geography (US/UK/EU = higher tier, India = negotiate up) —
  per PRD pricing design. Good-rate filter applies regardless of source.

## Volume + quality (100 → 1) — how we keep it clean
- Each source fans in → dedup → LLM score (auto-reject junk) → top-N only → personalized message
  with self-eval regen. Volume scales; **quality does not drop** because filtering + personalization
  are automatic. Human reviews the final short list and sends manually (no auto-spam, ToS-safe).

---

## Add-a-platform checklist (for future sessions)
1. New file `backend/engine_a/<source>.py` with `fetch_<source>(..., http/parse/scrape=...) -> list[dict]`
   returning the common shape `{source, title, description, url, budget}`.
2. Injectable network boundary + a test with a fake fetcher (no live calls).
3. Wire into `engine_a/graph.py` (or a sources aggregator).
4. Append the platform to the "Covered now" table above + a BUILD_LOG phase note.

_Full tool options (nothing discarded): see `docs/research/TOOL_REGISTRY.md`._
