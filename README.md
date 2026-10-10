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
   .venv\Scripts\Activate.ps1
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   cp .env.example .env   # then edit JWT_SECRET, SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD
   .\.venv\Scripts\python.exe -m alembic upgrade head
   .\.venv\Scripts\python.exe seed.py             # admin account
   .\.venv\Scripts\python.exe seed_catalogue.py   # demo catalogue (idempotent)
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 3000
   ```
3. Frontend (backend must be running on port 3000):
   ```
   cd frontend
   npm install
   npm run dev      # http://localhost:5173 — /api is proxied to the backend
   npm test         # display rules (node --test)
   ```

## Tests

`cd backend && .\.venv\Scripts\python.exe -m pytest -v`

## S5 — Back-office produits/catégories/photos

New endpoints under `/api/produits`, `/api/categories`, `/api/photos` — see
`docs/specs/2026-09-22-s5-produit-categorie-photo-design.md` for the full design.

Photo uploads are stubbed: files are saved locally under `backend/uploads/` (gitignored) and served
back at `http://localhost:3000/uploads/<filename>` instead of going to a real Cloudinary account.
Swap `photo_service.upload_to_cloudinary` for the real SDK call when Cloudinary credentials exist —
its signature (`upload_to_cloudinary(fichier) -> url`) doesn't need to change.
