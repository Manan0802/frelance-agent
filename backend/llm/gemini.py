import google.generativeai as genai

from backend.config import settings


def generate(prompt: str) -> str:
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    return model.generate_content(prompt).text
