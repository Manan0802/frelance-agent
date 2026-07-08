import httpx
from google import genai

from backend.config import settings

DEFAULT_MODEL = "gemini-2.0-flash-lite"
GROQ_FALLBACK_MODEL = "llama-3.3-70b-versatile"


def _generate_gemini(prompt: str, model: str) -> str:
    client = genai.Client(api_key=settings.gemini_api_key)
    return client.models.generate_content(model=model, contents=prompt).text


def _generate_groq(prompt: str, model: str = GROQ_FALLBACK_MODEL) -> str:
    resp = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.groq_api_key}"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}]},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def generate(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Gemini primary, Groq fallback — a Gemini error (rate limit, outage, bad
    key) shouldn't take down message/proposal generation."""
    try:
        return _generate_gemini(prompt, model)
    except Exception:
        return _generate_groq(prompt)
