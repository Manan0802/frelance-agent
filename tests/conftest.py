import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_freelancing_agent.db")

import pytest

from backend.database.connection import Base, engine
from backend.database import models  # noqa: F401  (register all tables)


@pytest.fixture(autouse=True)
def _fresh_db():
    """Give every test an isolated schema so shared-SQLite state can't leak.

    Uses a dedicated test DB file (not the dev/live one) — this fixture
    drops and recreates every table before each test, which previously
    wiped real dev data since both shared the same default sqlite file.
    """
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
