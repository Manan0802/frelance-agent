from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./data/freelancing_agent.db"
    gemini_api_key: str = ""
    groq_api_key: str = ""
    maps_scraper_base_url: str = "http://localhost:8080"
    maps_scraper_api_key: str = ""
    # Manan's call (2026-07-27): he doesn't want an AI-disclosure line on
    # outbound. Kept behind a flag rather than deleted so it's one setting away.
    ai_disclosure_enabled: bool = False
    whatsapp_enabled: bool = True  # set false to exercise the pipeline without messaging Manan
    greenapi_id: str = ""
    greenapi_token: str = ""
    manan_whatsapp: str = ""
    api_key: str = ""  # if set, required on state-changing API calls
    # When set, the dashboard asks for it over HTTP Basic. Empty means no gate,
    # which is right for localhost and wrong for anything with a public URL —
    # the deploy entrypoint refuses to boot without it.
    dashboard_password: str = ""


settings = Settings()
