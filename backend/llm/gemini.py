from google import genai

from backend.config import settings

DEFAULT_MODEL = "gemini-2.0-flash-lite"


def generate(prompt: str, model: str = DEFAULT_MODEL) -> str:
    client = genai.Client(api_key=settings.gemini_api_key)
    return client.models.generate_content(model=model, contents=prompt).text
