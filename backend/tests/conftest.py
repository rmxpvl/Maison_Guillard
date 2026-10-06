import os

from dotenv import load_dotenv

load_dotenv()

# Must run before any `app.*` import: app.database builds its engine from
# DATABASE_URL at import time, so redirecting it later is too late.
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]