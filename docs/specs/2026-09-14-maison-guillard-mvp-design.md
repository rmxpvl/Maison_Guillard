# Maison Guillard — MVP Design (condensed from project documentation)

> Source documents (authoritative, out-of-repo): `Documentation/Maison-Guillard-MVP.pdf`,
> `Documentation/Maison-Guillard-Doc-Technique.pdf`, `Documentation/Maison-Guillard-Plan-de-route.pdf`
> (in the parent `Maison_guillard/` folder). This file condenses the parts needed to plan and
> implement Semaine 4 (project init: backend, DB, frontend skeleton, admin auth) and stays valid
> for later weeks (S5-S9).
>
> **Stack amendment (2026-09-14):** the submitted `Maison-Guillard-Doc-Technique.pdf` (Jalon 2,
> milestone dated 10 sept 2026) specifies Node.js/Express/Prisma for the backend. That decision was
> revised **after** that milestone: the backend is now **Python (FastAPI + SQLAlchemy + Alembic)**
> instead. This file is the up-to-date, authoritative version of the stack going forward — the PDF
> itself was not edited (it's a submitted deliverable outside this repo) and now has a factual
> discrepancy with the code. **Action for the project owner:** write a short addendum/errata note
> referencing this decision for whoever grades the coursework, since the PDF can't be edited here.
> Everything else in the original docs (product scope, data model shape, REST endpoint contracts,
> plan de route dates) is unaffected by this change.

## Product summary

Maison Guillard: web app for an artisan furniture maker to present and sell handmade furniture
(tables, chairs, stools, lamps). Two public flows: direct purchase (cart → order) and quote
request (form → artisan follow-up). One admin (the artisan) manages the catalog via a protected
back-office. No customer accounts in the MVP (guest checkout / guest quote requests).

## Stack

- **Frontend:** React + Vite (plain JS, matching the "solo dev, 9-week window" constraint).
- **Backend:** Python + FastAPI, REST API under `/api`. ASGI server: Uvicorn.
- **Database:** PostgreSQL via SQLAlchemy 2.x ORM, migrations via Alembic.
- **Validation:** Pydantic models (FastAPI's native request/response validation — replaces the
  originally-planned Zod schemas).
- **Auth:** JWT (stateless, via `PyJWT`) + bcrypt password hashing (via `passlib[bcrypt]`). Single
  admin account, no roles/permissions system beyond "is admin."
- **Media:** Cloudinary for product photos (backend stores only the returned URL). Out of scope
  for S4 — introduced when product CRUD is built (S5).
- **Local dev DB:** docker-compose running Postgres, so `docker compose up -d` gives a working DB
  without installing Postgres natively.
- **Python env:** a virtualenv per app (`backend/.venv`), dependencies pinned in
  `backend/requirements.txt` (kept deliberately simple over Poetry/PDM for a solo 9-week project).

## Repository layout (monorepo, two independent apps)

```
Maison_Guillard/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI() app factory + route mounting (no uvicorn.run() call)
│   │   ├── database.py         # SQLAlchemy engine + SessionLocal + Base + get_db() dependency
│   │   ├── models/
│   │   │   └── admin.py        # Admin ORM model
│   │   ├── schemas/
│   │   │   └── auth.py         # Pydantic request/response models (LoginRequest, TokenResponse)
│   │   ├── routers/
│   │   │   └── auth.py         # APIRouter: POST /api/auth/login
│   │   ├── services/
│   │   │   └── auth_service.py # hash_password, verify_password, login, verify_token
│   │   └── dependencies/
│   │       └── require_admin.py # FastAPI dependency guarding admin-only routes
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── alembic.ini
│   ├── tests/
│   │   ├── unit/test_auth_service.py
│   │   └── integration/test_auth_routes.py
│   ├── seed.py
│   ├── .env.example
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── context/AuthContext.jsx
│   │   ├── api/auth.js
│   │   └── pages/admin/PageLoginAdmin.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml           # postgres service for local dev
├── docs/{specs,plans}/
└── .gitignore
```

Full catalog/order/quote schema and REST endpoint shapes are specified in
`Maison-Guillard-Doc-Technique.pdf` §04-07 (data model and endpoint list are stack-agnostic and
still apply — only the implementation technology changes); implemented incrementally in later
weeks (S5+). This spec only locks in what S4 needs.

## Database schema — S4 slice

Only the `Admin` table is needed this week. Later weeks add `Categorie`, `Produit`, `Photo`,
`Commande`, `LigneCommande`, `Devis` per the doc technique's ERD (page 7 of that PDF) — same shape,
expressed as SQLAlchemy models instead of a Prisma schema.

```python
# app/models/admin.py
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

## Auth design

- `auth_service.hash_password(plain: str) -> str` → bcrypt hash via `passlib.CryptContext`.
- `auth_service.verify_password(plain: str, hashed: str) -> bool`.
- `auth_service.login(db: Session, email: str, password: str) -> str` → looks up `Admin` by email,
  verifies password, returns a signed JWT (`{"sub": admin.id, "email": admin.email}`, secret from
  `os.environ["JWT_SECRET"]`, expiry `8h`) or raises `InvalidCredentialsError`.
- `auth_service.verify_token(token: str) -> dict` → decoded payload or raises
  `jwt.InvalidTokenError` (or a subclass).
- `require_admin` FastAPI dependency: reads `Authorization: Bearer <token>` header, verifies via
  `auth_service.verify_token`, returns the decoded payload (injectable into route handlers via
  `Depends(require_admin)`) or raises `HTTPException(401)`.
- Endpoint: `POST /api/auth/login` — body `{ "email": str, "motDePasse": str }` → `200 { "token":
  str }` / `401`.
- `seed.py` creates one admin account from `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` env vars
  (never hardcode a password in source).

## Frontend — S4 slice

Unaffected by the backend stack change — still React + Vite, same as before:

- No router library yet needed for a single page — add `react-router-dom` when S6 introduces
  multiple public pages. For S4: a single `PageLoginAdmin` form that posts to `/api/auth/login`,
  stores the token via `AuthContext` (in-memory + `localStorage`), and shows "connecté" on success.
- `AuthContext` exposes `{ token, login(email, password), logout(), isAuthenticated }`.
- `api/auth.js` wraps `fetch` to `VITE_API_URL + '/auth/login'`.

## Testing strategy — S4 slice

- **Unit (pytest):** `auth_service` functions, with the DB session mocked/faked (no real DB hit) —
  hashing, password verification, token verify/expiry, invalid-credentials path.
- **Integration (pytest + FastAPI `TestClient`, i.e. `httpx`):** `POST /api/auth/login` against a
  real test database (separate `DATABASE_URL` for tests, reset between test runs via an Alembic
  migration + truncate fixture) — covers 200 and 401 paths end-to-end.
- No frontend test framework introduced yet for S4 (doc technique doesn't mandate frontend unit
  tests; manual parcours testing is the stated strategy — see doc technique §08).

## Out of scope for this plan (S4)

Product/category/photo/order/quote CRUD, Cloudinary integration, cart, public catalog pages,
`react-router-dom` multi-page routing. These land in S5-S8 per the plan de route and get their own
plans building on this one.

## Global constraints carried into the plan

- Python 3.14.4 as the floor (confirmed locally via `python --version`) — no lower version
  targeted; no compatibility concern since this is a fresh project with no legacy consumers.
- Node.js LTS (v25.8.1 confirmed) still the floor for the frontend (`frontend/`, unaffected by the
  backend stack change).
- Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`) per doc
  technique §08.
- Branch model: `main` / `dev` / `feature/<task>` — for solo work in this session, commit directly
  on a `feature/s4-init` branch and note the merge-to-`dev` step at the end (per doc technique's
  SCM strategy, merges to `main` only from `dev`).
- No secrets committed: `.env` gitignored, `.env.example` documents required vars without values;
  `backend/.venv/` also gitignored (never commit a virtualenv).
