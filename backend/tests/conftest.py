import os

import pytest
from dotenv import load_dotenv

load_dotenv()

# Must run before any `app.*` import: app.database builds its engine from
# DATABASE_URL at import time, so redirecting it later is too late.
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]


@pytest.fixture(autouse=True)
def limiteur_vierge():
    """The rate limiter keeps its counters in memory: every test starts with empty ones."""
    from app.services import limiteur

    limiteur.reinitialiser()
    yield
    limiteur.reinitialiser()
