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
