from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./data/freelancing_agent.db"
    gemini_api_key: str = ""
    groq_api_key: str = ""
    maps_scraper_base_url: str = "http://localhost:8080"
    maps_scraper_api_key: str = ""
    greenapi_id: str = ""
    greenapi_token: str = ""
    manan_whatsapp: str = ""
    api_key: str = ""  # if set, required on state-changing API calls


settings = Settings()
