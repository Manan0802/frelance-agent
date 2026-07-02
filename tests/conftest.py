import pytest

from backend.database.connection import Base, engine
from backend.database import models  # noqa: F401  (register all tables)


@pytest.fixture(autouse=True)
def _fresh_db():
    """Give every test an isolated schema so shared-SQLite state can't leak."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
