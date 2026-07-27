"""LLM JSON responses arrive fenced, and both parsers were silently failing.

Gemini wraps JSON in ```json ... ``` fences. `json.loads()` raises on that, and
both callers swallowed it into a fallback:

- research_target() dumped the whole raw string into research_summary and left
  pain_points EMPTY. pain_points is what the matcher matches on, so researched
  leads were matching on the business name instead — which is why portfolio
  matches kept coming back empty for has-website leads.
- score_job() fell back to score 0, which is below REJECT_THRESHOLD (40), so a
  fenced response auto-rejected the job outright.
"""

import json

from backend.llm.parse import parse_json
from backend.engine_b.research import research_target
from backend.engine_a.scorer import score_job
from backend.portfolio.context import PortfolioContext


class T:
    name = "Acme"
    category = "shop"
    location = "Delhi"
    website = "https://example.com"


FENCED = '```json\n{"research_summary": "s", "pain_points": "no online ordering"}\n```'


def test_parses_plain_json():
    assert parse_json('{"a": 1}', {}) == {"a": 1}


def test_parses_json_fence():
    assert parse_json('```json\n{"a": 1}\n```', {}) == {"a": 1}


def test_parses_bare_fence():
    assert parse_json('```\n{"a": 1}\n```', {}) == {"a": 1}


def test_parses_json_embedded_in_prose():
    assert parse_json('Sure! Here you go:\n{"a": 1}\nHope that helps.', {}) == {"a": 1}


def test_returns_default_on_unparseable_text():
    assert parse_json("no json at all", {"a": 0}) == {"a": 0}


def test_parses_json_with_raw_newlines_inside_string_values():
    """Gemini formats long values as multi-line lists, putting literal newlines
    inside JSON strings. That is invalid JSON and json.loads() rejects it — seen
    live, emptying pain_points even after the fenced-JSON fix."""
    raw = '```json\n{\n  "research_summary": "s",\n  "pain_points": "issues:\n    1. manual support\n    2. no booking"\n}\n```'
    out = parse_json(raw, {})
    assert "manual support" in out["pain_points"]
    assert out["research_summary"] == "s"


def test_research_recovers_pain_points_from_fenced_json():
    out = research_target(T(), fetch=lambda url: "<html>site</html>", llm=lambda p: FENCED)
    assert out["pain_points"] == "no online ordering"
    assert out["research_summary"] == "s"
    assert "```" not in out["research_summary"]


def test_scorer_recovers_score_from_fenced_json():
    pf = PortfolioContext(personal={"name": "M"}, skills={"ai": ["LangGraph"]})
    fenced = '```json\n{"score": 85, "skill_matched": ["LangGraph"]}\n```'
    out = score_job({"title": "t", "description": "d"}, pf, llm=lambda p: fenced)
    assert out["score"] == 85.0
    assert out["auto_rejected"] is False, "a fenced response must not auto-reject the job"
