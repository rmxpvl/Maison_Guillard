# S4 — Project Init & Admin Auth Implementation Plan (Python/FastAPI)

> **Revision note (2026-09-14):** this plan originally targeted Node.js/Express/Prisma. The stack
> was changed to Python/FastAPI/SQLAlchemy/Alembic after Task 1-2 were already implemented and
> reviewed under the old stack — those tasks were reverted (see spec's "Stack amendment" note) and
> redone here. Task numbering restarts clean for the new stack; nothing from the Node
> implementation carries forward.

**Goal:** Stand up the Maison Guillard monorepo (backend + frontend + local Postgres) and ship a
working admin authentication flow (`POST /api/auth/login` + a login page), matching the plan de
route's Semaine 4 objective: "Initialiser le projet (backend, base de données, squelette
frontend) ; authentification et autorisation administrateur."

**Architecture:** Two independent apps in one repo (`backend/`, `frontend/`), no shared tooling.
Backend is FastAPI + SQLAlchemy/PostgreSQL exposing a REST API under `/api`; frontend is a Vite +
React SPA that calls it over `fetch`. Postgres runs locally via docker-compose. Auth is stateless
JWT + bcrypt, single admin account, no roles beyond "is admin."

**Tech Stack:** Python 3.14.4, FastAPI, Uvicorn, SQLAlchemy 2.x, Alembic, Pydantic, PyJWT,
passlib[bcrypt], pytest + httpx (via FastAPI `TestClient`), PostgreSQL 16 (docker-compose),
Node.js v25.8.1 + React 18 + Vite (frontend only).

**Spec:** `docs/specs/2026-09-14-maison-guillard-mvp-design.md`

## Global Constraints

- Python 3.14.4 as the floor (confirmed locally).
- Conventional Commits format for every commit (`feat:`, `fix:`, `docs:`, `chore:`, `test:`,
  `refactor:`).
- Work happens on branch `feature/s4-init` (already checked out — do not create it again).
- No secrets committed: `.env` files gitignored; `.env.example` documents required vars with
  placeholder values only. `backend/.venv/` is also gitignored — never commit a virtualenv.
- `backend/app/main.py` must build and export the FastAPI `app` instance WITHOUT calling
  `uvicorn.run()` — that call lives only in a separate `backend/run.py` (or is invoked via the
  `uvicorn` CLI directly), so tests can import `app` and use `TestClient` without binding a port.
- Docker-compose Postgres (from the earlier Node-stack work, still valid/unaffected by the pivot):
  user `maison`, password `maison_dev_password`, db `maison_guillard`, port 5432. Do not recreate
  `docker-compose.yml` — it already exists at the repo root with these values.

---

### Task 1: Backend Python project skeleton, venv, FastAPI health check

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/pytest.ini`
- Create: `backend/.gitignore` (venv-specific; root `.gitignore` already covers `.env`)
- Test: `backend/tests/__init__.py`, `backend/tests/integration/__init__.py`,
  `backend/tests/integration/test_health.py`

**Interfaces:**
- Consumes: nothing (first backend code).
- Produces: `app/main.py` exposes `app` (a `FastAPI()` instance, no server-start call) — every
  later backend test and the eventual `uvicorn app.main:app` invocation import this exact name.

- [ ] **Step 1: Create and activate a virtualenv, from `backend/`**

```bash
cd backend
python -m venv .venv
```

Activate it (Windows Git Bash): `source .venv/Scripts/activate` — your prompt should now show
`(.venv)`. Run every following `pip`/`pytest`/`uvicorn` command from this activated shell.

- [ ] **Step 2: Create `backend/requirements.txt`**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
alembic==1.14.0
psycopg2-binary==2.9.10
pydantic==2.10.4
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.1
pytest==8.3.4
httpx==0.28.1
```

- [ ] **Step 3: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: all packages install without error.

- [ ] **Step 4: Create `backend/pytest.ini`**

```ini
[pytest]
testpaths = tests
pythonpath = .
```

- [ ] **Step 5: Create empty `__init__.py` markers**

```bash
mkdir -p app tests/unit tests/integration
touch app/__init__.py tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py
```

- [ ] **Step 6: Write the failing test**

```python
# backend/tests/integration/test_health.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 7: Run test to verify it fails**

Run: `pytest tests/integration/test_health.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 8: Create `backend/app/main.py`**

```python
from fastapi import FastAPI

app = FastAPI(title="Maison Guillard API")


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 9: Run test to verify it passes**

Run: `pytest tests/integration/test_health.py -v`
Expected: PASS (1 test)

- [ ] **Step 10: Create `backend/.gitignore`**

```gitignore
.venv/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 11: Commit**

```bash
git add backend/requirements.txt backend/app backend/tests backend/pytest.ini backend/.gitignore
git commit -m "feat: add FastAPI app skeleton with health check endpoint"
```

---

### Task 2: SQLAlchemy engine/session, Admin model, Alembic migration

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/admin.py`
- Create: `backend/.env.example`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/` (populated by `alembic revision` in Step 6)

**Interfaces:**
- Consumes: `DATABASE_URL` env var (from `.env`, pointing at the docker-compose Postgres).
- Produces: `app/database.py` exports `engine`, `SessionLocal`, `Base`, and a `get_db()` generator
  (FastAPI dependency, yields a `Session` and closes it after the request) — every later router and
  service imports these exact names. `app/models/admin.py` exports the `Admin` ORM class
  (`__tablename__ = "admin"`, columns `id`, `email`, `password_hash`, `created_at`) — queryable via
  `db.query(Admin)` once a `Session` is obtained.

- [ ] **Step 1: Create `backend/.env.example`**

```
DATABASE_URL=postgresql+psycopg2://maison:maison_dev_password@localhost:5432/maison_guillard
JWT_SECRET=replace-with-a-long-random-string
SEED_ADMIN_EMAIL=admin@maisonguillard.fr
SEED_ADMIN_PASSWORD=replace-with-a-strong-password
```

- [ ] **Step 2: Create local `.env` (not committed)**

```bash
cp .env.example .env
```

Edit `backend/.env` and set `JWT_SECRET` to a real random value — run
`python -c "import secrets; print(secrets.token_hex(32))"` and paste the output — and set
`SEED_ADMIN_PASSWORD` to a real password you'll use to log in locally.

- [ ] **Step 3: Create `backend/app/database.py`**

```python
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: Create `backend/app/models/__init__.py`**

```python
from app.models.admin import Admin

__all__ = ["Admin"]
```

- [ ] **Step 5: Create `backend/app/models/admin.py`**

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Admin(Base):
    __tablename__ = "admin"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 6: Initialize Alembic**

Run: `alembic init alembic`
Expected: creates `backend/alembic/` (with `env.py`, `script.py.mako`, `versions/`) and
`backend/alembic.ini`.

- [ ] **Step 7: Point Alembic at `DATABASE_URL` and the models' metadata**

Edit `backend/alembic.ini` — find the line starting `sqlalchemy.url =` and delete/comment it out
(we set the URL from the environment instead, in `env.py`, so the real password never sits in a
committed ini file):

```ini
# sqlalchemy.url = driver://user:pass@localhost/dbname
```

Edit `backend/alembic/env.py` — near the top, after the existing imports, add:

```python
import os
import sys
sys.path.insert(0, os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from app.database import Base
from app.models import Admin  # noqa: F401 — import so Base.metadata sees the table

config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
target_metadata = Base.metadata
```

(This replaces the template's `target_metadata = None` line — search for it and replace it with
the block above, keeping the rest of the generated `env.py` as-is.)

- [ ] **Step 8: Generate and apply the first migration**

Run: `alembic revision --autogenerate -m "create admin table"`
Expected: writes a new file under `backend/alembic/versions/` containing `op.create_table("admin",
...)`.

Run: `alembic upgrade head`
Expected: "Running upgrade -> <revision>, create admin table" with no errors.

- [ ] **Step 9: Verify the table exists**

Run: `docker compose exec postgres psql -U maison -d maison_guillard -c '\d admin'`
Expected: shows the `admin` table with columns `id, email, password_hash, created_at`.

- [ ] **Step 10: Commit**

```bash
git add backend/app/database.py backend/app/models backend/.env.example backend/alembic.ini backend/alembic
git commit -m "feat: add SQLAlchemy engine, Admin model, and initial Alembic migration"
```

---

### Task 3: `auth_service` (unit tests, DB session faked)

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/auth_service.py`
- Test: `backend/tests/unit/test_auth_service.py`
- Modify: `backend/requirements.txt` (already has needed deps from Task 1 — no change expected,
  listed here only in case a version conflict surfaces during install)

**Interfaces:**
- Consumes: `Admin` model (Task 2).
- Produces: `auth_service.hash_password(plain: str) -> str`,
  `auth_service.verify_password(plain: str, hashed: str) -> bool`,
  `auth_service.login(db: Session, email: str, password: str) -> str` (returns a JWT string, raises
  `auth_service.InvalidCredentialsError` on bad email/password),
  `auth_service.verify_token(token: str) -> dict` (raises `jwt.InvalidTokenError` — from
  `jose.exceptions` — on invalid/expired token). Task 4's route and dependency call these exact
  names.

- [ ] **Step 1: Create `backend/app/services/__init__.py`** (empty file)

- [ ] **Step 2: Write the failing tests**

```python
# backend/tests/unit/test_auth_service.py
import os
from unittest.mock import MagicMock
import pytest

os.environ.setdefault("JWT_SECRET", "test-secret")

from app.services import auth_service


def test_hash_and_verify_password_roundtrip():
    hashed = auth_service.hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert auth_service.verify_password("correct horse battery staple", hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = auth_service.hash_password("right-password")
    assert auth_service.verify_password("wrong-password", hashed) is False


def _fake_admin(id_=1, email="admin@test.com", password="good-password"):
    admin = MagicMock()
    admin.id = id_
    admin.email = email
    admin.password_hash = auth_service.hash_password(password)
    return admin


def test_login_returns_token_for_valid_credentials():
    admin = _fake_admin()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = admin

    token = auth_service.login(db, "admin@test.com", "good-password")

    assert isinstance(token, str)
    assert len(token) > 0


def test_login_raises_for_unknown_email():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(auth_service.InvalidCredentialsError):
        auth_service.login(db, "nobody@test.com", "whatever")


def test_login_raises_for_wrong_password():
    admin = _fake_admin(password="good-password")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = admin

    with pytest.raises(auth_service.InvalidCredentialsError):
        auth_service.login(db, "admin@test.com", "bad-password")


def test_verify_token_decodes_a_token_from_login():
    admin = _fake_admin(id_=42, email="admin@test.com")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = admin

    token = auth_service.login(db, "admin@test.com", "good-password")
    decoded = auth_service.verify_token(token)

    assert decoded["sub"] == 42
    assert decoded["email"] == "admin@test.com"


def test_verify_token_raises_on_garbage_token():
    with pytest.raises(Exception):
        auth_service.verify_token("not-a-real-token")
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/unit/test_auth_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.auth_service'`

- [ ] **Step 4: Create `backend/app/services/auth_service.py`**

```python
import os
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.admin import Admin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TOKEN_EXPIRY_HOURS = 8
JWT_ALGORITHM = "HS256"


class InvalidCredentialsError(Exception):
    """Raised when login is attempted with an unknown email or wrong password."""


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def login(db: Session, email: str, password: str) -> str:
    admin = db.query(Admin).filter(Admin.email == email).first()
    if admin is None:
        raise InvalidCredentialsError()

    if not verify_password(password, admin.password_hash):
        raise InvalidCredentialsError()

    payload = {
        "sub": admin.id,
        "email": admin.email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS),
    }
    secret = os.environ["JWT_SECRET"]
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    secret = os.environ["JWT_SECRET"]
    try:
        return jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise JWTError("Invalid or expired token") from exc
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/test_auth_service.py -v`
Expected: PASS (all 7 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/app/services backend/tests/unit
git commit -m "feat: add auth_service with bcrypt hashing and JWT issuing"
```

---

### Task 4: `require_admin` dependency + `POST /api/auth/login` route (integration tests, real test DB)

**Files:**
- Create: `backend/app/dependencies/__init__.py`
- Create: `backend/app/dependencies/require_admin.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/auth.py`
- Modify: `backend/app/main.py` (mount the auth router; add a protected test route)
- Test: `backend/tests/integration/test_auth_routes.py`
- Modify: `backend/.env.example`, `backend/.env` (add `TEST_DATABASE_URL`)
- Modify: `backend/tests/integration/test_health.py` may need no change — confirm it still passes.

**Interfaces:**
- Consumes: `auth_service.login`, `auth_service.verify_token`,
  `auth_service.InvalidCredentialsError` (Task 3); `get_db` (Task 2).
- Produces: `require_admin` FastAPI dependency (raises `HTTPException(401)` on missing/invalid
  token, otherwise returns the decoded payload dict) — later tasks (product/order/quote admin
  routes in S5+) depend on this via `Depends(require_admin)`. Route `POST /api/auth/login` mounted
  at `/api/auth/login`.

- [ ] **Step 1: Add a separate test database URL**

Edit `backend/.env.example`, add:

```
TEST_DATABASE_URL=postgresql+psycopg2://maison:maison_dev_password@localhost:5432/maison_guillard_test
```

Edit `backend/.env` and add the same line (matching your local Postgres).

- [ ] **Step 2: Create the test database and apply migrations to it**

```bash
docker compose exec postgres psql -U maison -d maison_guillard -c "CREATE DATABASE maison_guillard_test;"
DATABASE_URL="$TEST_DATABASE_URL" alembic upgrade head
```

(Read `TEST_DATABASE_URL` from `.env` if your shell doesn't export it automatically — e.g.
`export $(grep TEST_DATABASE_URL .env)` first, or just paste the literal URL from Step 1 inline.)

- [ ] **Step 3: Create `backend/app/schemas/__init__.py`** (empty file)

- [ ] **Step 4: Create `backend/app/schemas/auth.py`**

```python
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    motDePasse: str


class TokenResponse(BaseModel):
    token: str
```

- [ ] **Step 5: Create `backend/app/dependencies/__init__.py`** (empty file)

- [ ] **Step 6: Create `backend/app/dependencies/require_admin.py`**

```python
from fastapi import Header, HTTPException

from app.services import auth_service


def require_admin(authorization: str = Header(default="")) -> dict:
    scheme, _, token = authorization.partition(" ")
    if scheme != "Bearer" or not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        return auth_service.verify_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")
```

- [ ] **Step 7: Create `backend/app/routers/__init__.py`** (empty file)

- [ ] **Step 8: Create `backend/app/routers/auth.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        token = auth_service.login(db, payload.email, payload.motDePasse)
    except auth_service.InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    return TokenResponse(token=token)
```

- [ ] **Step 9: Mount the router and a protected test route in `backend/app/main.py`**

```python
from fastapi import Depends, FastAPI

from app.dependencies.require_admin import require_admin
from app.routers import auth

app = FastAPI(title="Maison Guillard API")

app.include_router(auth.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


# Exercises require_admin end-to-end; also useful during S5+ manual testing.
@app.get("/api/health/protected-check")
def protected_health_check(admin: dict = Depends(require_admin)):
    return {"status": "ok", "admin": admin["email"]}
```

- [ ] **Step 10: Write the failing tests**

```python
# backend/tests/integration/test_auth_routes.py
import os

os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.services import auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def seed_admin():
    db = SessionLocal()
    db.query(Admin).delete()
    db.commit()
    admin = Admin(
        email="admin@test.com",
        password_hash=auth_service.hash_password("test-password-123"),
    )
    db.add(admin)
    db.commit()
    yield
    db.query(Admin).delete()
    db.commit()
    db.close()


def test_login_returns_200_and_token_for_valid_credentials():
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@test.com", "motDePasse": "test-password-123"},
    )
    assert res.status_code == 200
    assert "token" in res.json()


def test_login_returns_401_for_wrong_password():
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@test.com", "motDePasse": "wrong-password"},
    )
    assert res.status_code == 401


def test_login_returns_401_for_unknown_email():
    res = client.post(
        "/api/auth/login",
        json={"email": "nobody@test.com", "motDePasse": "whatever"},
    )
    assert res.status_code == 401


def test_login_returns_422_when_motdepasse_missing():
    res = client.post("/api/auth/login", json={"email": "admin@test.com"})
    assert res.status_code == 422


def test_protected_route_rejects_missing_authorization_header():
    res = client.get("/api/health/protected-check")
    assert res.status_code == 401


def test_protected_route_accepts_valid_token():
    login_res = client.post(
        "/api/auth/login",
        json={"email": "admin@test.com", "motDePasse": "test-password-123"},
    )
    token = login_res.json()["token"]

    res = client.get(
        "/api/health/protected-check",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
```

> Note: FastAPI/Pydantic rejects a request missing a required field with `422` (not `400` — this
> differs from a hand-rolled Express validator, which is why the missing-field test above expects
> `422`, matching Pydantic's actual behavior rather than the REST convention table in the doc
> technique written for the Node stack).

- [ ] **Step 11: Run tests to verify they fail**

Run: `pytest tests/integration/test_auth_routes.py -v`
Expected: FAIL — collection error or 404s, since the router/dependency files don't fully wire
together yet before this step (if Steps 1-9 above were already done in order, this may partially
pass — run it anyway to confirm the full suite, including this file, is green only after Step 9 is
truly complete).

- [ ] **Step 12: Run the full test suite to verify everything passes**

Run: `pytest -v`
Expected: PASS (all tests across `test_health.py`, `test_auth_service.py`, `test_auth_routes.py`)

- [ ] **Step 13: Commit**

```bash
git add backend/app backend/tests backend/.env.example
git commit -m "feat: add POST /api/auth/login route and require_admin dependency"
```

---

### Task 5: Admin seed script

**Files:**
- Create: `backend/seed.py`

**Interfaces:**
- Consumes: `auth_service.hash_password` (Task 3), `SessionLocal`, `Admin` (Task 2),
  `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` env vars (Task 2's `.env.example`).
- Produces: one `Admin` row in the dev database, usable to log in from the frontend in Task 6.

- [ ] **Step 1: Create `backend/seed.py`**

```python
import os

from dotenv import load_dotenv

load_dotenv()

from app.database import SessionLocal
from app.models.admin import Admin
from app.services import auth_service


def main():
    email = os.environ["SEED_ADMIN_EMAIL"]
    password = os.environ["SEED_ADMIN_PASSWORD"]

    db = SessionLocal()
    try:
        existing = db.query(Admin).filter(Admin.email == email).first()
        if existing:
            print(f"Admin {email} already exists, skipping.")
            return

        admin = Admin(email=email, password_hash=auth_service.hash_password(password))
        db.add(admin)
        db.commit()
        print(f"Created admin account for {email}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the seed script against the dev database**

Run: `python seed.py`
Expected: `Created admin account for <SEED_ADMIN_EMAIL>.`

- [ ] **Step 3: Verify manually**

Start the API in another terminal: `uvicorn app.main:app --reload --port 3000` (from `backend/`,
venv activated).

Run: `curl -X POST http://localhost:3000/api/auth/login -H "Content-Type: application/json" -d "{\"email\":\"<SEED_ADMIN_EMAIL>\",\"motDePasse\":\"<SEED_ADMIN_PASSWORD>\"}"`
Expected: JSON response with a `token` field.

- [ ] **Step 4: Commit**

```bash
git add backend/seed.py
git commit -m "feat: add admin account seed script"
```

---

### Task 6: Frontend Vite/React skeleton with admin login page

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/.env.example`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/context/AuthContext.jsx`
- Create: `frontend/src/api/auth.js`
- Create: `frontend/src/pages/admin/PageLoginAdmin.jsx`

**Interfaces:**
- Consumes: backend `POST /api/auth/login` (Task 4), read from `import.meta.env.VITE_API_URL`.
- Produces: `AuthContext` exposing `{ token, isAuthenticated, login(email, password), logout() }`
  — S5's `DashboardAdmin` and protected admin routes will wrap themselves in this context and read
  `isAuthenticated` / call `logout()`.

Entirely unaffected by the backend stack change — identical to the original Node-stack plan for
this task, since the frontend only talks to the backend over HTTP.

- [ ] **Step 1: Scaffold the Vite React app**

```bash
cd frontend
npm create vite@latest . -- --template react
npm install
```

- [ ] **Step 2: Create `frontend/.env.example`**

```
VITE_API_URL=http://localhost:3000/api
```

Copy it: `cp .env.example .env`

- [ ] **Step 3: Create `frontend/src/api/auth.js`**

```javascript
const API_URL = import.meta.env.VITE_API_URL;

export async function loginRequest(email, motDePasse) {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, motDePasse }),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || 'Échec de la connexion');
  }

  return data.token;
}
```

> Note: FastAPI's default error body shape is `{"detail": "..."}`, not `{"error": "..."}` — this
> is why `data.detail` is read here instead of `data.error`.

- [ ] **Step 4: Create `frontend/src/context/AuthContext.jsx`**

```jsx
import { createContext, useContext, useState, useCallback } from 'react';
import { loginRequest } from '../api/auth';

const AuthContext = createContext(null);
const STORAGE_KEY = 'maison_guillard_admin_token';

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY));

  const login = useCallback(async (email, password) => {
    const newToken = await loginRequest(email, password);
    localStorage.setItem(STORAGE_KEY, newToken);
    setToken(newToken);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
  }, []);

  const value = {
    token,
    isAuthenticated: Boolean(token),
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
```

- [ ] **Step 5: Create `frontend/src/pages/admin/PageLoginAdmin.jsx`**

```jsx
import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';

export function PageLoginAdmin() {
  const { login, isAuthenticated, logout } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isAuthenticated) {
    return (
      <div>
        <p>Connecté en tant qu'administrateur.</p>
        <button onClick={logout}>Se déconnecter</button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <h1>Connexion administrateur</h1>
      <label>
        Email
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </label>
      <label>
        Mot de passe
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </label>
      {error && <p role="alert">{error}</p>}
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Connexion...' : 'Se connecter'}
      </button>
    </form>
  );
}
```

- [ ] **Step 6: Wire it up in `frontend/src/App.jsx`**

```jsx
import { AuthProvider } from './context/AuthContext';
import { PageLoginAdmin } from './pages/admin/PageLoginAdmin';

export default function App() {
  return (
    <AuthProvider>
      <PageLoginAdmin />
    </AuthProvider>
  );
}
```

- [ ] **Step 7: Manual verification**

With the backend running (`uvicorn app.main:app --reload --port 3000` in `backend/`, venv
activated, Postgres up, admin seeded from Task 5), run (from `frontend/`): `npm run dev`, open the
printed local URL, submit the login form with the seeded admin's email/password.
Expected: form replaced by "Connecté en tant qu'administrateur." with a working "Se déconnecter"
button. Submitting wrong credentials shows the error message inline instead.

- [ ] **Step 8: Commit**

```bash
git add frontend
git commit -m "feat: add vite react skeleton with admin login page and auth context"
```

---

### Task 7: Wire remaining docs and merge to `dev`

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: nothing new.
- Produces: nothing consumed by later tasks — this is the wrap-up task for S4.

- [ ] **Step 1: Update root `README.md` with the actual commands verified in Tasks 1-6**

```markdown
# Maison Guillard

Web app for presenting and selling handmade furniture. See
`docs/specs/2026-09-14-maison-guillard-mvp-design.md` for the design and
`docs/plans/` for implementation plans.

## Local dev setup

1. `docker compose up -d` — starts Postgres on `localhost:5432`.
2. Backend:
   ```
   cd backend
   python -m venv .venv
   source .venv/Scripts/activate   # Windows Git Bash; use .venv/bin/activate on macOS/Linux
   pip install -r requirements.txt
   cp .env.example .env            # then edit JWT_SECRET, SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD
   alembic upgrade head
   python seed.py
   uvicorn app.main:app --reload --port 3000
   ```
3. Frontend:
   ```
   cd frontend
   cp .env.example .env
   npm install
   npm run dev              # opens on http://localhost:5173 (or similar)
   ```

## Tests

`cd backend && pytest -v` — unit tests (faked DB session) + integration tests (real Postgres test
database, see `TEST_DATABASE_URL` in `backend/.env`).
```

- [ ] **Step 2: Run the full backend test suite one last time**

Run (from `backend/`, venv activated): `pytest -v`
Expected: PASS, all tests.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: finalize S4 local dev setup instructions"
```

- [ ] **Step 4: Merge into `dev`**

```bash
git checkout -b dev 2>/dev/null || git checkout dev
git merge --no-ff feature/s4-init -m "merge: S4 project init and admin auth"
git checkout main
```

Leave the merge to `main` for the weekly checkpoint per the doc technique's SCM strategy (`dev` →
`main` only at week's end / milestones, never a direct commit) — do not merge `dev` into `main` as
part of this task. This is also a merge to a shared/long-lived branch — confirm with the project
owner before running it, per the "ask before a merge" norm.
