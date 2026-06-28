# Phase 1 — Engine B (Outbound) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A runnable outbound pipeline that turns a list of local businesses into personalized, portfolio-grounded outreach messages, delivers them as a WhatsApp digest for review, and logs approved sends to a CRM — landing Manan's first good-rate client.

**Architecture:** A LangGraph linear StateGraph (`ingest → research → match → write → notify`) over a FastAPI app with a SQLite store. Lead targets come from the omkarcloud Google Maps scraper (ingested as dicts, decoupled from live scraping). Research and message-writing use Gemini; portfolio matching uses local sentence-transformers embeddings. Notifications go out via green-api WhatsApp. Nothing is auto-sent — the human approves and sends manually.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.x (SQLite), Pydantic v2, LangGraph, google-generativeai (Gemini), sentence-transformers, httpx, pytest, python-dotenv.

## Global Constraints

- **Never auto-send.** The system drafts and notifies; Manan approves and sends manually. No code path sends an outreach message to a client.
- **No mass spam.** Outbound is curated and per-target personalized; no bulk blasts.
- **Data local-only** except LLM calls (Gemini). No PII leaves the machine beyond the LLM prompt.
- **LLM:** Gemini `gemini-1.5-flash` primary. Groq fallback is out of scope for Phase 1 (add in 1.5).
- **Personalization gate:** message writer self-evaluates; if `personalization_score < 7/10`, regenerate once.
- **WhatsApp = green-api** REST; notifications are self-only.
- All LLM/HTTP boundaries must be mockable so tests never hit the network.

---

## File Structure

```
backend/
├── main.py                       # FastAPI app + routes (Task 1, 10)
├── config.py                     # Settings from .env (Task 1)
├── database/
│   ├── connection.py             # engine + SessionLocal + get_db (Task 1)
│   └── models.py                 # OutboundTarget, OutreachMessage, CrmRecord (Task 2)
├── portfolio/
│   └── context.py                # Pydantic models + loader (Task 3)
├── engine_b/
│   ├── ingest.py                 # raw business dicts → OutboundTarget (Task 4)
│   ├── research.py               # site fetch + Gemini research (Task 5)
│   ├── matcher.py                # portfolio embedding match (Task 6)
│   ├── writer.py                 # message writer + self-eval (Task 7)
│   └── graph.py                  # LangGraph orchestrator (Task 9)
├── notify/
│   └── whatsapp.py               # green-api digest sender (Task 8)
└── llm/
    └── gemini.py                 # thin Gemini wrapper (Task 5)
data/
└── portfolio_context.json        # Manan's portfolio brain (Task 3)
tests/                            # mirrors backend/ (all tasks)
.env.example                      # secrets template (Task 1)
requirements.txt                  # deps (Task 1)
```

---

### Task 1: Project scaffold, config, DB connection

**Files:**
- Create: `requirements.txt`, `.env.example`, `backend/config.py`, `backend/database/connection.py`, `backend/main.py`
- Test: `tests/test_health.py`

**Interfaces:**
- Produces: `backend.config.settings` (object with `database_url: str`, `gemini_api_key: str`, `greenapi_id: str`, `greenapi_token: str`, `manan_whatsapp: str`); `backend.database.connection.engine`, `SessionLocal`, `get_db()` generator; FastAPI `app` in `backend/main.py` with `GET /health` returning `{"status": "ok"}`.

- [ ] **Step 1: Write requirements.txt**

```
fastapi==0.115.*
uvicorn[standard]==0.32.*
sqlalchemy==2.0.*
pydantic==2.*
pydantic-settings==2.*
python-dotenv==1.*
httpx==0.27.*
langgraph==0.2.*
google-generativeai==0.8.*
sentence-transformers==3.*
pytest==8.*
```

- [ ] **Step 2: Write .env.example**

```
DATABASE_URL=sqlite:///./data/freelancing_agent.db
GEMINI_API_KEY=
GREENAPI_ID=
GREENAPI_TOKEN=
MANAN_WHATSAPP=91XXXXXXXXXX
```

- [ ] **Step 3: Write the failing test**

```python
# tests/test_health.py
from fastapi.testclient import TestClient
from backend.main import app

def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
```

- [ ] **Step 4: Run test to verify it fails**

Run: `pytest tests/test_health.py -v`
Expected: FAIL — `ModuleNotFoundError: backend.main`

- [ ] **Step 5: Write config.py**

```python
# backend/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./data/freelancing_agent.db"
    gemini_api_key: str = ""
    greenapi_id: str = ""
    greenapi_token: str = ""
    manan_whatsapp: str = ""

settings = Settings()
```

- [ ] **Step 6: Write database/connection.py**

```python
# backend/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.config import settings

class Base(DeclarativeBase):
    pass

engine = create_engine(
    settings.database_url, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 7: Write main.py**

```python
# backend/main.py
from fastapi import FastAPI

app = FastAPI(title="Freelancing Agent")

@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest tests/test_health.py -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add requirements.txt .env.example backend/ tests/test_health.py
git commit -m "feat: project scaffold, config, db connection, health route"
```

---

### Task 2: Database models

**Files:**
- Create: `backend/database/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: `backend.database.connection.Base`, `engine`, `SessionLocal`.
- Produces: ORM models `OutboundTarget`, `OutreachMessage`, `CrmRecord`; `create_all(engine)` callable that builds tables.
  - `OutboundTarget(id:str pk, name:str, website:str|None, email:str|None, phone:str|None, category:str|None, location:str|None, dedup_hash:str unique, raw:str, created_at:datetime)`
  - `OutreachMessage(id:str pk, target_id:str fk, research_summary:str, pain_points:str, portfolio_used:str, draft_text:str, personalization_score:float, status:str default 'draft', created_at:datetime)`
  - `CrmRecord(id:str pk, message_id:str fk, target_name:str, status:str default 'approved', sent_at:datetime|None, notes:str|None, created_at:datetime)`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
from backend.database.connection import Base, engine, SessionLocal
from backend.database.models import OutboundTarget, create_all

def test_insert_target():
    create_all(engine)
    db = SessionLocal()
    t = OutboundTarget(id="t1", name="Acme Dental", dedup_hash="h1", raw="{}")
    db.add(t); db.commit()
    got = db.query(OutboundTarget).filter_by(id="t1").one()
    assert got.name == "Acme Dental"
    db.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL — `ImportError: cannot import name 'OutboundTarget'`

- [ ] **Step 3: Write models.py**

```python
# backend/database/models.py
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.database.connection import Base, engine

class OutboundTarget(Base):
    __tablename__ = "outbound_targets"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    website: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    dedup_hash: Mapped[str] = mapped_column(String, unique=True)
    raw: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class OutreachMessage(Base):
    __tablename__ = "outreach_messages"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    target_id: Mapped[str] = mapped_column(ForeignKey("outbound_targets.id"))
    research_summary: Mapped[str] = mapped_column(Text, default="")
    pain_points: Mapped[str] = mapped_column(Text, default="")
    portfolio_used: Mapped[str] = mapped_column(Text, default="")
    draft_text: Mapped[str] = mapped_column(Text, default="")
    personalization_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class CrmRecord(Base):
    __tablename__ = "crm_records"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    message_id: Mapped[str] = mapped_column(ForeignKey("outreach_messages.id"))
    target_name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="approved")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

def create_all(bind=engine):
    Base.metadata.create_all(bind)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/database/models.py tests/test_models.py
git commit -m "feat: outbound target, message, crm models"
```

---

### Task 3: Portfolio context loader

**Files:**
- Create: `backend/portfolio/context.py`, `data/portfolio_context.json`
- Test: `tests/test_portfolio.py`

**Interfaces:**
- Produces: Pydantic `PortfolioProject(name:str, type:str, description:str, tech:list[str], pitch_for:list[str], url:str|None)`, `PortfolioContext(personal:dict, skills:dict, projects:list[PortfolioProject], ...)`; `load_portfolio(path:str) -> PortfolioContext`.

- [ ] **Step 1: Seed data/portfolio_context.json**

Use the master portfolio from the PRD §9 (name, skills, the 5 projects with `pitch_for` arrays). Copy it verbatim into `data/portfolio_context.json`.

- [ ] **Step 2: Write the failing test**

```python
# tests/test_portfolio.py
from backend.portfolio.context import load_portfolio

def test_load_portfolio():
    ctx = load_portfolio("data/portfolio_context.json")
    assert ctx.personal["name"] == "Manan"
    assert any(p.name == "SARA" for p in ctx.projects)
    sara = next(p for p in ctx.projects if p.name == "SARA")
    assert "AI agent" in sara.pitch_for
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_portfolio.py -v`
Expected: FAIL — `ModuleNotFoundError: backend.portfolio.context`

- [ ] **Step 4: Write context.py**

```python
# backend/portfolio/context.py
import json
from pydantic import BaseModel

class PortfolioProject(BaseModel):
    name: str
    type: str
    description: str
    tech: list[str] = []
    pitch_for: list[str] = []
    url: str | None = None

class PortfolioContext(BaseModel):
    personal: dict
    skills: dict = {}
    projects: list[PortfolioProject] = []
    availability: str | None = None

def load_portfolio(path: str) -> PortfolioContext:
    with open(path, encoding="utf-8") as f:
        return PortfolioContext(**json.load(f))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_portfolio.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/portfolio/ data/portfolio_context.json tests/test_portfolio.py
git commit -m "feat: portfolio context loader"
```

---

### Task 4: Target ingest (Maps dicts → OutboundTarget)

**Files:**
- Create: `backend/engine_b/ingest.py`
- Test: `tests/test_ingest.py`

**Interfaces:**
- Consumes: `OutboundTarget`, `SessionLocal`, `create_all`.
- Produces: `ingest_targets(rows: list[dict], db) -> list[OutboundTarget]` — maps omkarcloud Maps fields (`name`, `website`, `email`, `phone`, `category`, `address`) to `OutboundTarget`, computes `dedup_hash = sha256(name+location)`, skips rows whose hash already exists.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ingest.py
from backend.database.connection import engine, SessionLocal
from backend.database.models import create_all, OutboundTarget
from backend.engine_b.ingest import ingest_targets

def test_ingest_dedupes():
    create_all(engine)
    db = SessionLocal()
    rows = [
        {"name": "Acme Dental", "website": "http://acme.in", "address": "Delhi"},
        {"name": "Acme Dental", "website": "http://acme.in", "address": "Delhi"},
    ]
    out = ingest_targets(rows, db)
    assert len(out) == 1
    assert db.query(OutboundTarget).count() == 1
    db.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ingest.py -v`
Expected: FAIL — `ModuleNotFoundError: backend.engine_b.ingest`

- [ ] **Step 3: Write ingest.py**

```python
# backend/engine_b/ingest.py
import hashlib, json, uuid
from backend.database.models import OutboundTarget

def _hash(name: str, location: str) -> str:
    return hashlib.sha256(f"{name}|{location}".encode()).hexdigest()

def ingest_targets(rows: list[dict], db) -> list[OutboundTarget]:
    created = []
    for row in rows:
        name = row.get("name", "").strip()
        location = row.get("address") or row.get("location") or ""
        h = _hash(name, location)
        if db.query(OutboundTarget).filter_by(dedup_hash=h).first():
            continue
        t = OutboundTarget(
            id=str(uuid.uuid4()), name=name,
            website=row.get("website"), email=row.get("email"),
            phone=row.get("phone"), category=row.get("category"),
            location=location, dedup_hash=h, raw=json.dumps(row),
        )
        db.add(t); created.append(t)
    db.commit()
    return created
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ingest.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/engine_b/ingest.py tests/test_ingest.py
git commit -m "feat: maps target ingest with dedup"
```

---

### Task 5: Website research (fetch + Gemini)

**Files:**
- Create: `backend/llm/gemini.py`, `backend/engine_b/research.py`
- Test: `tests/test_research.py`

**Interfaces:**
- Produces:
  - `backend.llm.gemini.generate(prompt:str) -> str` — thin Gemini wrapper (real impl uses `gemini-1.5-flash`); injectable.
  - `research_target(target, fetch=..., llm=...) -> dict` returning `{"research_summary": str, "pain_points": str}`. `fetch(url)->str` and `llm(prompt)->str` are injected so tests don't hit network.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_research.py
from backend.engine_b.research import research_target

class T:
    name = "Acme Dental"; website = "http://acme.in"; category = "dentist"; location = "Delhi"

def test_research_uses_site_and_llm():
    fake_fetch = lambda url: "Acme Dental. Old site, no online booking."
    fake_llm = lambda prompt: '{"research_summary": "Dental clinic, outdated site", "pain_points": "no online booking"}'
    out = research_target(T(), fetch=fake_fetch, llm=fake_llm)
    assert "Dental" in out["research_summary"]
    assert "booking" in out["pain_points"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_research.py -v`
Expected: FAIL — `ModuleNotFoundError: backend.engine_b.research`

- [ ] **Step 3: Write gemini.py**

```python
# backend/llm/gemini.py
import google.generativeai as genai
from backend.config import settings

def generate(prompt: str) -> str:
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    return model.generate_content(prompt).text
```

- [ ] **Step 4: Write research.py**

```python
# backend/engine_b/research.py
import json
import httpx
from backend.llm.gemini import generate

def _default_fetch(url: str) -> str:
    try:
        r = httpx.get(url, timeout=15, follow_redirects=True,
                      headers={"User-Agent": "FreelancingAgent/1.0"})
        return r.text[:6000]
    except Exception:
        return ""

RESEARCH_PROMPT = """You are researching a local business for a freelance pitch.
Business: {name} ({category}) in {location}.
Website content (truncated):
{site}

Return ONLY JSON: {{"research_summary": "...", "pain_points": "concrete problems a web/AI dev could fix"}}"""

def research_target(target, fetch=_default_fetch, llm=generate) -> dict:
    site = fetch(target.website) if target.website else ""
    prompt = RESEARCH_PROMPT.format(
        name=target.name, category=target.category or "business",
        location=target.location or "", site=site or "(no website found)")
    raw = llm(prompt)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"research_summary": raw.strip(), "pain_points": ""}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_research.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/llm/gemini.py backend/engine_b/research.py tests/test_research.py
git commit -m "feat: website research via fetch + gemini"
```

---

### Task 6: Portfolio matcher (embeddings)

**Files:**
- Create: `backend/engine_b/matcher.py`
- Test: `tests/test_matcher.py`

**Interfaces:**
- Consumes: `PortfolioContext`, `PortfolioProject`.
- Produces: `match_projects(need_text:str, projects:list[PortfolioProject], top_k:int=2, embed=...) -> list[PortfolioProject]`. `embed(list[str])->list[list[float]]` injected (defaults to sentence-transformers `all-MiniLM-L6-v2`). Ranks projects by cosine similarity of `description + ' ' + ' '.join(pitch_for)` against `need_text`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_matcher.py
from backend.portfolio.context import PortfolioProject
from backend.engine_b.matcher import match_projects

def test_match_picks_relevant():
    projects = [
        PortfolioProject(name="SARA", type="ai", description="LangGraph multi-agent system", pitch_for=["AI agent", "automation"]),
        PortfolioProject(name="Site", type="web", description="business website", pitch_for=["website", "landing page"]),
    ]
    fake_embed = lambda texts: [[1.0, 0.0] if "website" in t.lower() else [0.0, 1.0] for t in texts]
    out = match_projects("need a business website", projects, top_k=1, embed=fake_embed)
    assert out[0].name == "Site"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_matcher.py -v`
Expected: FAIL — `ModuleNotFoundError: backend.engine_b.matcher`

- [ ] **Step 3: Write matcher.py**

```python
# backend/engine_b/matcher.py
from backend.portfolio.context import PortfolioProject

_model = None
def _default_embed(texts: list[str]) -> list[list[float]]:
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model.encode(texts).tolist()

def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0

def match_projects(need_text, projects, top_k=2, embed=_default_embed):
    proj_texts = [f"{p.description} {' '.join(p.pitch_for)}" for p in projects]
    vectors = embed([need_text] + proj_texts)
    need_vec, proj_vecs = vectors[0], vectors[1:]
    scored = sorted(zip(projects, proj_vecs),
                    key=lambda pv: _cosine(need_vec, pv[1]), reverse=True)
    return [p for p, _ in scored[:top_k]]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_matcher.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/engine_b/matcher.py tests/test_matcher.py
git commit -m "feat: portfolio embedding matcher"
```

---

### Task 7: Message writer + self-eval regen

**Files:**
- Create: `backend/engine_b/writer.py`
- Test: `tests/test_writer.py`

**Interfaces:**
- Consumes: `match_projects`, Gemini `generate`, `PortfolioContext`.
- Produces: `write_message(target, research:dict, projects:list[PortfolioProject], llm=...) -> dict` returning `{"draft_text": str, "personalization_score": float, "portfolio_used": list[str]}`. Calls LLM to write, then to self-score; if score < 7, regenerates once with a stricter instruction. Enforces the PRD proposal rules in the system prompt.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_writer.py
from backend.portfolio.context import PortfolioProject
from backend.engine_b.writer import write_message

class T:
    name = "Acme Dental"; category = "dentist"; location = "Delhi"

def test_writer_regens_when_low_score():
    projects = [PortfolioProject(name="Site", type="web", description="business website", pitch_for=["website"])]
    research = {"research_summary": "Outdated site", "pain_points": "no online booking"}
    calls = []
    def fake_llm(prompt):
        calls.append(prompt)
        if "Write a" in prompt:
            return "Hi, I noticed Acme Dental has no online booking..."
        # scoring call: first time low, then high
        return "9" if "stricter" in prompt else "4"
    out = write_message(T(), research, projects, llm=fake_llm)
    assert out["personalization_score"] == 9.0
    assert "Site" in out["portfolio_used"]
    assert len([c for c in calls if "Write a" in c]) == 2  # regenerated once
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_writer.py -v`
Expected: FAIL — `ModuleNotFoundError: backend.engine_b.writer`

- [ ] **Step 3: Write writer.py**

```python
# backend/engine_b/writer.py
from backend.llm.gemini import generate

RULES = """Rules: start with the client's problem (never "Hi I am Manan"); reference one
specific detail; mention one relevant past project; name the tech you'd use; under 120 words;
end with one question; do NOT commit a price; confident peer tone, not sycophantic."""

WRITE_PROMPT = """Write a cold outreach message to {name}, a {category} in {location}.
Their situation: {summary}
Their likely pain: {pain}
Relevant past work you can cite: {projects}
{rules}{stricter}"""

SCORE_PROMPT = """Rate this outreach message's personalization 0-10 (how specific to THIS
business vs generic). Reply with ONLY a number.\n\nMessage:\n{msg}"""

def _draft(target, research, projects, llm, stricter=""):
    proj_str = "; ".join(f"{p.name}: {p.description}" for p in projects)
    return llm(WRITE_PROMPT.format(
        name=target.name, category=target.category or "business",
        location=target.location or "", summary=research.get("research_summary", ""),
        pain=research.get("pain_points", ""), projects=proj_str,
        rules=RULES, stricter=stricter))

def _score(msg, llm) -> float:
    raw = llm(SCORE_PROMPT.format(msg=msg))
    try:
        return float("".join(c for c in raw if c.isdigit() or c == ".")[:4])
    except ValueError:
        return 0.0

def write_message(target, research, projects, llm=generate) -> dict:
    draft = _draft(target, research, projects, llm)
    score = _score(draft, llm)
    if score < 7:
        draft = _draft(target, research, projects, llm,
                       stricter="\nBe stricter: cite a concrete detail unique to this business.")
        score = _score(draft, llm)
    return {"draft_text": draft, "personalization_score": score,
            "portfolio_used": [p.name for p in projects]}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_writer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/engine_b/writer.py tests/test_writer.py
git commit -m "feat: message writer with self-eval regen"
```

---

### Task 8: WhatsApp digest (green-api)

**Files:**
- Create: `backend/notify/whatsapp.py`
- Test: `tests/test_whatsapp.py`

**Interfaces:**
- Produces:
  - `format_digest(messages:list[dict]) -> str` — builds the digest text from `[{name, score, draft_text}]`.
  - `send_whatsapp(text:str, poster=...) -> bool` — POSTs to green-api `sendMessage`; `poster(url, json)->resp` injected. Returns True on 2xx. Never raises on network error (logs, returns False).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_whatsapp.py
from backend.notify.whatsapp import format_digest, send_whatsapp

def test_format_digest():
    text = format_digest([{"name": "Acme Dental", "score": 9.0, "draft_text": "Hi..."}])
    assert "Acme Dental" in text and "9" in text

def test_send_posts_to_greenapi():
    captured = {}
    class Resp:
        status_code = 200
    def fake_poster(url, json):
        captured["url"] = url; captured["json"] = json
        return Resp()
    ok = send_whatsapp("hello", poster=fake_poster)
    assert ok is True
    assert "sendMessage" in captured["url"]
    assert captured["json"]["message"] == "hello"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_whatsapp.py -v`
Expected: FAIL — `ModuleNotFoundError: backend.notify.whatsapp`

- [ ] **Step 3: Write whatsapp.py**

```python
# backend/notify/whatsapp.py
import httpx
from backend.config import settings

def format_digest(messages: list[dict]) -> str:
    lines = ["🚀 OUTBOUND DIGEST", ""]
    for i, m in enumerate(messages, 1):
        lines.append(f"{i}. [{m['score']:.0f}/10] {m['name']}")
        lines.append(m["draft_text"])
        lines.append("")
    lines.append("→ Review + approve in dashboard, then send manually.")
    return "\n".join(lines)

def _default_poster(url, json):
    return httpx.post(url, json=json, timeout=20)

def send_whatsapp(text: str, poster=_default_poster) -> bool:
    url = (f"https://api.green-api.com/waInstance{settings.greenapi_id}"
           f"/sendMessage/{settings.greenapi_token}")
    payload = {"chatId": f"{settings.manan_whatsapp}@c.us", "message": text}
    try:
        resp = poster(url, payload)
        return 200 <= resp.status_code < 300
    except Exception:
        return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_whatsapp.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/notify/whatsapp.py tests/test_whatsapp.py
git commit -m "feat: green-api whatsapp digest"
```

---

### Task 9: LangGraph orchestrator

**Files:**
- Create: `backend/engine_b/graph.py`
- Test: `tests/test_graph.py`

**Interfaces:**
- Consumes: `research_target`, `match_projects`, `write_message`, `format_digest`, `send_whatsapp`, `load_portfolio`, models.
- Produces: `run_engine_b(targets:list[OutboundTarget], db, portfolio, deps:dict|None=None) -> list[OutreachMessage]`. `deps` lets tests inject `research`, `match`, `write`, `notify`. For each target: research → match (using pain text) → write → persist `OutreachMessage` → collect; then send one digest.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_graph.py
from backend.database.connection import engine, SessionLocal
from backend.database.models import create_all, OutboundTarget, OutreachMessage
from backend.portfolio.context import PortfolioContext, PortfolioProject
from backend.engine_b.graph import run_engine_b

def test_run_engine_b_persists_and_notifies():
    create_all(engine)
    db = SessionLocal()
    t = OutboundTarget(id="g1", name="Acme", dedup_hash="gh1", raw="{}")
    db.add(t); db.commit()
    pf = PortfolioContext(personal={"name": "Manan"},
                          projects=[PortfolioProject(name="Site", type="web", description="website")])
    sent = {}
    deps = {
        "research": lambda target: {"research_summary": "x", "pain_points": "no site"},
        "match": lambda need, projects: projects[:1],
        "write": lambda target, research, projects: {
            "draft_text": "Hi Acme", "personalization_score": 8.0, "portfolio_used": ["Site"]},
        "notify": lambda text: sent.update({"text": text}) or True,
    }
    out = run_engine_b([t], db, pf, deps=deps)
    assert len(out) == 1
    assert db.query(OutreachMessage).count() == 1
    assert "Acme" in sent["text"]
    db.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_graph.py -v`
Expected: FAIL — `ModuleNotFoundError: backend.engine_b.graph`

- [ ] **Step 3: Write graph.py**

```python
# backend/engine_b/graph.py
import uuid
from backend.database.models import OutreachMessage
from backend.engine_b.research import research_target
from backend.engine_b.matcher import match_projects
from backend.engine_b.writer import write_message
from backend.notify.whatsapp import format_digest, send_whatsapp

def run_engine_b(targets, db, portfolio, deps=None):
    deps = deps or {}
    research = deps.get("research", lambda t: research_target(t))
    match = deps.get("match", lambda need, projects: match_projects(need, projects))
    write = deps.get("write", lambda t, r, p: write_message(t, r, p))
    notify = deps.get("notify", lambda text: send_whatsapp(text))

    messages, digest_rows = [], []
    for target in targets:
        r = research(target)
        projects = match(r.get("pain_points") or target.name, portfolio.projects)
        w = write(target, r, projects)
        msg = OutreachMessage(
            id=str(uuid.uuid4()), target_id=target.id,
            research_summary=r.get("research_summary", ""),
            pain_points=r.get("pain_points", ""),
            portfolio_used=",".join(w["portfolio_used"]),
            draft_text=w["draft_text"],
            personalization_score=w["personalization_score"])
        db.add(msg); messages.append(msg)
        digest_rows.append({"name": target.name, "score": w["personalization_score"],
                            "draft_text": w["draft_text"]})
    db.commit()
    if digest_rows:
        notify(format_digest(digest_rows))
    return messages
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_graph.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/engine_b/graph.py tests/test_graph.py
git commit -m "feat: engine B orchestrator"
```

---

### Task 10: API routes — run, list, approve (CRM log)

**Files:**
- Modify: `backend/main.py`
- Create: `backend/api/routes.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `ingest_targets`, `run_engine_b`, `load_portfolio`, `get_db`, models.
- Produces routes:
  - `POST /run` body `{"targets": [ {maps dict} ]}` → ingests + runs engine (with injected no-network deps in test via app state) → `{"messages": [{id, name, draft_text, score}]}`.
  - `GET /messages` → list drafts.
  - `PATCH /messages/{id}/approve` → sets status `approved`, creates `CrmRecord`, returns it.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from backend.database.connection import engine
from backend.database.models import create_all
from backend.main import app, set_run_deps

def test_run_and_approve():
    create_all(engine)
    set_run_deps({
        "research": lambda t: {"research_summary": "x", "pain_points": "no site"},
        "match": lambda need, projects: projects[:1],
        "write": lambda t, r, p: {"draft_text": "Hi Acme", "personalization_score": 8.0, "portfolio_used": ["Site"]},
        "notify": lambda text: True,
    })
    client = TestClient(app)
    r = client.post("/run", json={"targets": [{"name": "Acme", "address": "Delhi"}]})
    assert r.status_code == 200
    mid = r.json()["messages"][0]["id"]
    a = client.patch(f"/messages/{mid}/approve")
    assert a.status_code == 200
    assert a.json()["status"] == "approved"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py -v`
Expected: FAIL — `ImportError: cannot import name 'set_run_deps'`

- [ ] **Step 3: Write api/routes.py**

```python
# backend/api/routes.py
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from backend.database.connection import get_db
from backend.database.models import OutreachMessage, CrmRecord
from backend.engine_b.ingest import ingest_targets
from backend.engine_b.graph import run_engine_b
from backend.portfolio.context import load_portfolio

router = APIRouter()
_RUN_DEPS = {}
def set_run_deps(deps): _RUN_DEPS.clear(); _RUN_DEPS.update(deps)

@router.post("/run")
def run(body: dict, db=Depends(get_db)):
    targets = ingest_targets(body.get("targets", []), db)
    pf = load_portfolio("data/portfolio_context.json")
    msgs = run_engine_b(targets, db, pf, deps=_RUN_DEPS or None)
    return {"messages": [{"id": m.id, "name": next((t.name for t in targets if t.id == m.target_id), ""),
                          "draft_text": m.draft_text, "score": m.personalization_score} for m in msgs]}

@router.get("/messages")
def list_messages(db=Depends(get_db)):
    return [{"id": m.id, "draft_text": m.draft_text, "status": m.status}
            for m in db.query(OutreachMessage).all()]

@router.patch("/messages/{message_id}/approve")
def approve(message_id: str, db=Depends(get_db)):
    m = db.query(OutreachMessage).filter_by(id=message_id).first()
    if not m:
        raise HTTPException(404, "message not found")
    m.status = "approved"
    rec = CrmRecord(id=str(uuid.uuid4()), message_id=m.id,
                    target_name="", status="approved", created_at=datetime.utcnow())
    db.add(rec); db.commit()
    return {"id": m.id, "status": m.status, "crm_id": rec.id}
```

- [ ] **Step 4: Wire routes into main.py**

```python
# backend/main.py
from fastapi import FastAPI
from backend.api.routes import router, set_run_deps  # noqa: F401

app = FastAPI(title="Freelancing Agent")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(router)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_api.py -v`
Expected: PASS

- [ ] **Step 6: Run the full suite**

Run: `pytest -v`
Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add backend/api/ backend/main.py tests/test_api.py
git commit -m "feat: run/list/approve API with crm logging"
```

---

## Self-Review

**Spec coverage (Phase 1, §7 of design):**
- Maps target source → Task 4 (ingest; live scrape is a manual feed, decoupled by design). ✅
- Research → Task 5. ✅
- Portfolio match (RAG) → Task 6. ✅
- Personalized message + self-eval regen → Task 7 (enforces §13 personalization gate). ✅
- WhatsApp digest (green-api) → Task 8. ✅
- Orchestrator → Task 9. ✅
- Review + approve + CRM log → Task 10. ✅
- Portfolio context JSON → Task 3. ✅
- Never auto-send constraint → honored: pipeline drafts + notifies only; approve route logs, never sends. ✅

**Deferred to Phase 1.5 (intentional, not gaps):** React dashboard (review is API + WhatsApp for now), APScheduler daily cron (run via `POST /run` manually), Groq fallback, live Maps-scraper subprocess wrapper, enrichment (Bricks), email second channel.

**Placeholder scan:** none — every step has runnable code/commands.

**Type consistency:** `research_target`→dict{research_summary,pain_points} consumed identically in Tasks 7/9; `write_message`→dict{draft_text,personalization_score,portfolio_used} consumed in Task 9; `OutreachMessage` fields match across Tasks 2/9/10. ✅
