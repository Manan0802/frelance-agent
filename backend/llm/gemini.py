import time

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


# A 25-target run makes ~125 calls in a burst. Measured: that 429'd Gemini, fell
# through to Groq, and 429'd that too. Both free tiers are per-MINUTE limited, so
# the only cure is to wait — routing to the other provider isn't enough when the
# burst is what caused it.
LLM_ATTEMPTS = 3
BACKOFF_SECONDS = 20


def generate(prompt: str, model: str = DEFAULT_MODEL, sleep=time.sleep) -> str:
    """Gemini primary, Groq fallback, then wait and try again.

    Raises the last provider error rather than a generic one — the caller needs
    to tell a rate limit apart from a bad key.
    """
    last: Exception | None = None
    for attempt in range(LLM_ATTEMPTS):
        for call in (lambda: _generate_gemini(prompt, model), lambda: _generate_groq(prompt)):
            try:
                return call()
            except Exception as exc:
                last = exc
        if attempt < LLM_ATTEMPTS - 1:
            sleep(BACKOFF_SECONDS * (attempt + 1))
    raise last
