# S6 — Site public (catalogue, fiche produit, navigation) Implementation Plan

**Goal:** Ship the public catalogue: list produits with photos, filter by catégorie and
disponibilité, show a detailed fiche produit, on a new React + Vite frontend talking to the
existing FastAPI API.

**Architecture:** Backend gains one ORM relationship (`Produit.photos`) and one schema field
(`ProduitOut.photos`) so a single request returns produits with their photos; a seed script fills
the catalogue for the demo. Frontend is a new Vite + React app (plain JS) with `react-router-dom`;
Vite proxies `/api` to the backend on port 3000. Pages own data loading through one small
`useApi` hook; pure display rules (price, labels, photo choice, actions per disponibilité) live in
`utils/produit.js` and are unit-tested with Node's built-in test runner.

**Tech Stack:** Python 3.14.4, FastAPI, SQLAlchemy 2.0.36, pytest, PostgreSQL 16 (docker-compose);
Node 25.8.1, npm 11, Vite, React, react-router-dom, `node:test`.

**Spec:** `docs/specs/2026-10-10-s6-site-public-design.md`

**Who types what:** Tasks 1–2 (backend) are typed by Remy; Tasks 3–6 (frontend) are written for
him and explained afterwards.

## Global Constraints

- Branch: `Branche-S6` (already created from `main`, holds the spec).
- Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`), no trailers.
- Backend runs on port **3000** (`uvicorn ... --port 3000`, as in the README).
- No Alembic migration in this plan: the relationship is ORM-only.
- Frontend uses `photo.url` exactly as returned by the API; it never builds an image URL.
- Frontend calls the API only through relative `/api/...` paths (Vite proxy).
- UI text in French. `rupture` is displayed as "Vendu"; `sur_commande` prices as "À partir de X €".
- `sur_commande` produits are never purchasable directly: no "Ajouter au panier" for them.
- Every cart/devis button is rendered `disabled` with `title="Bientôt disponible"` in this plan.
- No frontend test framework dependency: pure helpers are tested with `node --test` only.

## Review Focus

- `?disponibilite=foo` (hand-edited URL) → filter ignored, full list shown, no API 422 error
  screen. Pinned by `disponibiliteValide` tests (Task 3) and its use in Tasks 4–5.
- `/produits/abc` or `/produits/0` → "Page introuvable", not an error screen or a 422. Pinned by
  `parseIdProduit` tests (Task 3), used in Task 5.
- Produit with photos but none marked `principale` → card shows the lowest `ordre` photo, not a
  placeholder. Pinned by `photoPrincipale` tests (Task 3).
- `sur_commande` produit → never offers "Ajouter au panier". Pinned by `actionsFiche` tests
  (Task 3).
- Deleting a produit that has loaded photos → still `204`, photos removed (no `IntegrityError`).
  Pinned by `test_delete_produit_with_photos_removes_its_photos` (Task 1).

## File Map

```
backend/app/models/produit.py               modify  photos relationship
backend/app/schemas/produit.py              modify  ProduitOut.photos
backend/tests/integration/test_produits_routes.py  modify  4 new tests
backend/seed_catalogue.py                   create  idempotent demo catalogue
backend/tests/integration/test_seed_catalogue.py   create
frontend/                                   create  Vite React app
  vite.config.js                            proxy /api -> :3000
  index.html                                lang fr, title
  package.json                              + react-router-dom, "test" script
  src/main.jsx                              router
  src/Layout.jsx                            Header + <Outlet>, loads categories once
  src/index.css                             all styles
  src/api/client.js, produits.js, categories.js
  src/hooks/useApi.js                       loading / error / retry state
  src/utils/produit.js (+ produit.test.js)  pure display rules
  src/components/Header.jsx, EtatChargement.jsx, BadgeDisponibilite.jsx,
                 FiltreCategorie.jsx, FiltreDisponibilite.jsx, CarteProduit.jsx,
                 GaleriePhotos.jsx, InfosProduit.jsx
  src/pages/PageCatalogue.jsx, PageFicheProduit.jsx, PageIntrouvable.jsx
README.md                                   modify  frontend + seed instructions
```

Compared with the spec's structure: `utils/format.js` becomes `utils/produit.js` (it also holds
photo choice and actions, not only formatting), and `Layout.jsx`, `hooks/useApi.js`,
`BadgeDisponibilite.jsx` are added to avoid repeating the same code in several pages.

---

### Task 1: Produits returned with their photos (backend — Remy types)

**Files:**
- Modify: `backend/app/models/produit.py`
- Modify: `backend/app/schemas/produit.py`
- Test: `backend/tests/integration/test_produits_routes.py`

**Interfaces:**
- Produces: `GET /api/produits` and `GET /api/produits/{id}` responses gain
  `"photos": [{"id", "produit_id", "url", "ordre", "principale"}, ...]` sorted by `ordre`
  ascending; `[]` when none.

Prerequisite: Postgres running (`docker compose up -d` at repo root).

- [ ] **Step 1: Add imports and a helper to the test file**

In `backend/tests/integration/test_produits_routes.py`, replace the line
`from app.models.produit import Produit` with:

```python
from app.models.photo import Photo
from app.models.produit import Disponibilite, Produit
```

Below `_make_categorie`, add:

```python
def _make_produit_avec_photos(db, categorie, ordres):
    produit = Produit(
        nom="Table basse",
        description="En chêne",
        categorie_id=categorie.id,
        prix=199.99,
        dimensions="120x60x40cm",
        disponibilite=Disponibilite.disponible,
    )
    db.add(produit)
    db.commit()
    db.refresh(produit)
    for ordre in ordres:
        db.add(
            Photo(
                produit_id=produit.id,
                url=f"https://example.com/photo-{ordre}.jpg",
                ordre=ordre,
                principale=False,
            )
        )
    db.commit()
    return produit
```

- [ ] **Step 2: Write the four failing tests**

Append to the same file:

```python
def test_get_produit_includes_photos_sorted_by_ordre(clean_db):
    categorie = _make_categorie(clean_db)
    produit = _make_produit_avec_photos(clean_db, categorie, ordres=[2, 0, 1])

    res = client.get(f"/api/produits/{produit.id}")

    assert res.status_code == 200
    assert [p["ordre"] for p in res.json()["photos"]] == [0, 1, 2]


def test_list_produits_includes_photos_sorted_by_ordre(clean_db):
    categorie = _make_categorie(clean_db)
    _make_produit_avec_photos(clean_db, categorie, ordres=[2, 0, 1])

    res = client.get("/api/produits")

    assert res.status_code == 200
    assert [p["ordre"] for p in res.json()[0]["photos"]] == [0, 1, 2]


def test_produit_without_photo_returns_empty_photos_list(clean_db):
    categorie = _make_categorie(clean_db)
    produit = _make_produit_avec_photos(clean_db, categorie, ordres=[])

    res = client.get(f"/api/produits/{produit.id}")

    assert res.status_code == 200
    assert res.json()["photos"] == []


def test_delete_produit_with_photos_removes_its_photos(clean_db):
    token = _admin_token(clean_db)
    categorie = _make_categorie(clean_db)
    produit = _make_produit_avec_photos(clean_db, categorie, ordres=[0, 1])
    produit_id = produit.id

    res = client.delete(
        f"/api/produits/{produit_id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert res.status_code == 204
    assert clean_db.query(Photo).filter(Photo.produit_id == produit_id).count() == 0
```

- [ ] **Step 3: Run the tests, check which fail**

Run (from `backend/`): `.\.venv\Scripts\python.exe -m pytest tests/integration/test_produits_routes.py -v`

Expected: the three `photos` tests FAIL with `KeyError: 'photos'`;
`test_delete_produit_with_photos_removes_its_photos` PASSES (no relationship yet, so PostgreSQL's
`ON DELETE CASCADE` does the work). All older tests PASS.

- [ ] **Step 4: Add the relationship WITHOUT cascade (on purpose)**

In `backend/app/models/produit.py`, add `from sqlalchemy.orm import relationship` under the
existing `sqlalchemy` imports, and at the end of the `Produit` class:

```python
    photos = relationship("Photo", order_by="Photo.ordre", lazy="selectin")
```

In `backend/app/schemas/produit.py`, add `from app.schemas.photo import PhotoOut` to the imports,
and in `ProduitOut`, after `disponibilite: Disponibilite`:

```python
    photos: list[PhotoOut] = []
```

- [ ] **Step 5: Run the tests, watch the delete test break**

Run: `.\.venv\Scripts\python.exe -m pytest tests/integration/test_produits_routes.py -v`

Expected: the three `photos` tests now PASS; `test_delete_produit_with_photos_removes_its_photos`
FAILS with `sqlalchemy.exc.IntegrityError` … `null value in column "produit_id"` (SQLAlchemy sent
`UPDATE photo SET produit_id=NULL` — `orm/dependency.py:562` → `orm/sync.py:94`).

- [ ] **Step 6: Add the delete cascade**

Replace the relationship line with:

```python
    photos = relationship(
        "Photo",
        order_by="Photo.ordre",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
```

- [ ] **Step 7: Run the whole backend suite**

Run: `.\.venv\Scripts\python.exe -m pytest -v`
Expected: all tests PASS (including `test_photo_routes.py`, which deletes produits with photos).

- [ ] **Step 8: Commit**

```bash
git add backend/app/models/produit.py backend/app/schemas/produit.py backend/tests/integration/test_produits_routes.py
git commit -m "feat: return photos with produits"
```

---

### Task 2: Demo catalogue seed (backend — Remy types)

**Files:**
- Create: `backend/seed_catalogue.py`
- Test: `backend/tests/integration/test_seed_catalogue.py`
- Modify: `README.md`

**Interfaces:**
- Produces: `seed_catalogue(db: Session) -> None` — creates the 4 catégories (`tables`,
  `chaises`, `tabourets`, `lampes`) and 12 produits (3 per catégorie, every `disponibilite`
  represented) if they don't already exist (matched on `slug` / `nom`). Runnable with
  `python seed_catalogue.py`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/integration/test_seed_catalogue.py`:

```python
import pytest

from app.database import SessionLocal
from app.models.categorie import Categorie
from app.models.produit import Disponibilite, Produit
from seed_catalogue import seed_catalogue


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    db.query(Produit).delete()
    db.query(Categorie).delete()
    db.commit()
    yield db
    db.query(Produit).delete()
    db.query(Categorie).delete()
    db.commit()
    db.close()


def test_seed_catalogue_creates_categories_and_produits(clean_db):
    seed_catalogue(clean_db)

    assert clean_db.query(Categorie).count() == 4
    assert clean_db.query(Produit).count() == 12


def test_seed_catalogue_is_idempotent(clean_db):
    seed_catalogue(clean_db)
    seed_catalogue(clean_db)

    assert clean_db.query(Categorie).count() == 4
    assert clean_db.query(Produit).count() == 12


def test_seed_catalogue_covers_every_disponibilite(clean_db):
    seed_catalogue(clean_db)

    disponibilites = {p.disponibilite for p in clean_db.query(Produit)}
    assert disponibilites == set(Disponibilite)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/integration/test_seed_catalogue.py -v`
Expected: collection ERROR `ModuleNotFoundError: No module named 'seed_catalogue'`.

- [ ] **Step 3: Write the seed script**

Create `backend/seed_catalogue.py`:

```python
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv()

from app.database import SessionLocal
from app.models.categorie import Categorie
from app.models.produit import Disponibilite, Produit

CATEGORIES = [
    ("Tables", "tables"),
    ("Chaises", "chaises"),
    ("Tabourets", "tabourets"),
    ("Lampes", "lampes"),
]

# (slug catégorie, nom, description, prix, dimensions, disponibilité)
PRODUITS = [
    ("tables", "Table de ferme en chêne",
     "Plateau massif en chêne brut, pieds tournés à la main, finition huile naturelle.",
     "890.00", "200x90x76cm", Disponibilite.disponible),
    ("tables", "Table basse en noyer",
     "Pièce unique en noyer massif, assemblages à tenons et mortaises.",
     "420.00", "110x60x40cm", Disponibilite.rupture),
    ("tables", "Table en frêne sur mesure",
     "Fabriquée à la demande : essence, dimensions et finition à définir ensemble.",
     "1200.00", "Dimensions au choix", Disponibilite.sur_commande),
    ("chaises", "Chaise paillée",
     "Structure en hêtre, assise paillée à la main.",
     "180.00", "45x48x88cm", Disponibilite.disponible),
    ("chaises", "Chaise en hêtre cintré",
     "Dossier cintré à la vapeur, fabriquée à la demande.",
     "240.00", "44x50x85cm", Disponibilite.sur_commande),
    ("chaises", "Fauteuil en chêne et lin",
     "Assise garnie de lin naturel, accoudoirs en chêne.",
     "560.00", "62x70x80cm", Disponibilite.rupture),
    ("tabourets", "Tabouret de bar en orme",
     "Assise creusée dans un plateau d'orme, repose-pieds en chêne.",
     "150.00", "35x35x75cm", Disponibilite.disponible),
    ("tabourets", "Tabouret tripode",
     "Trois pieds en frêne, assise ronde en chêne.",
     "95.00", "30x30x45cm", Disponibilite.disponible),
    ("tabourets", "Banc-tabouret en chêne",
     "Banc d'appoint en chêne massif, longueur à la demande.",
     "210.00", "90x30x45cm", Disponibilite.sur_commande),
    ("lampes", "Lampe de chevet en bois flotté",
     "Pied en bois flotté du Léman, abat-jour en lin.",
     "85.00", "20x20x40cm", Disponibilite.disponible),
    ("lampes", "Lampadaire en noyer",
     "Fût en noyer tourné, fabriqué à la demande.",
     "320.00", "40x40x160cm", Disponibilite.sur_commande),
    ("lampes", "Suspension en hêtre tourné",
     "Abat-jour tourné dans un bloc de hêtre.",
     "140.00", "35x35x30cm", Disponibilite.rupture),
]


def seed_catalogue(db: Session) -> None:
    categories = {}
    for nom, slug in CATEGORIES:
        categorie = db.query(Categorie).filter(Categorie.slug == slug).first()
        if categorie is None:
            categorie = Categorie(nom=nom, slug=slug)
            db.add(categorie)
            db.flush()  # assigns categorie.id before the produits need it
        categories[slug] = categorie

    for slug, nom, description, prix, dimensions, disponibilite in PRODUITS:
        if db.query(Produit).filter(Produit.nom == nom).first() is None:
            db.add(
                Produit(
                    nom=nom,
                    description=description,
                    categorie_id=categories[slug].id,
                    prix=Decimal(prix),
                    dimensions=dimensions,
                    disponibilite=disponibilite,
                )
            )
    db.commit()


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_catalogue(db)
        print("Catalogue de démonstration en place.")
    finally:
        db.close()
```

- [ ] **Step 4: Run the tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/integration/test_seed_catalogue.py -v`
Expected: 3 PASS. Then the full suite: `.\.venv\Scripts\python.exe -m pytest -v` → all PASS.

- [ ] **Step 5: Seed the dev database**

Run (from `backend/`): `.\.venv\Scripts\python.exe seed_catalogue.py`
Expected: `Catalogue de démonstration en place.` Run it a second time: same message, nothing
duplicated (check `GET http://localhost:3000/api/produits` returns 12 items).

- [ ] **Step 6: Document it in the README**

In `README.md`, step 2 of "Local dev setup", after the `alembic upgrade head` line, add:

```
   .\.venv\Scripts\python.exe seed.py             # admin account
   .\.venv\Scripts\python.exe seed_catalogue.py   # demo catalogue (idempotent)
```

- [ ] **Step 7: Commit**

```bash
git add backend/seed_catalogue.py backend/tests/integration/test_seed_catalogue.py README.md
git commit -m "feat: add idempotent demo catalogue seed"
```

---

### Task 3: Frontend scaffold, API client, display rules (frontend)

**Files:**
- Create: `frontend/` via create-vite, then
- Modify: `frontend/vite.config.js`, `frontend/index.html`, `frontend/package.json`
- Create: `frontend/src/api/client.js`, `frontend/src/api/produits.js`,
  `frontend/src/api/categories.js`, `frontend/src/hooks/useApi.js`,
  `frontend/src/utils/produit.js`, `frontend/src/utils/produit.test.js`
- Replace: `frontend/src/index.css`
- Delete: `frontend/src/App.jsx`, `frontend/src/App.css`, `frontend/src/assets/`,
  `frontend/public/vite.svg`
- Modify: `README.md`

**Interfaces:**
- Produces:
  - `class ApiError extends Error { status: number }`; `apiGet(path: string) -> Promise<any>`
    (fetches `/api` + path, throws `ApiError` when `!res.ok`).
  - `getProduits({ categorie?: number|null, disponibilite?: string|null }) -> Promise<Produit[]>`,
    `getProduit(id: number) -> Promise<Produit>`, `getCategories() -> Promise<Categorie[]>`.
  - `useApi(load: () => Promise<T>, deps: Array<string|number|null>) ->
    { statut: 'chargement'|'erreur'|'ok', data: T|null, erreur: Error|null, reessayer: () => void }`.
  - `utils/produit.js`: `DISPONIBILITES`, `libelleDisponibilite(d)`, `disponibiliteValide(v)`,
    `formatPrix(prix)`, `prixAffiche(produit)`, `photoPrincipale(photos)`,
    `parseIdProduit(v)`, `actionsFiche(disponibilite) -> {libelle, principale}[]`.
  - CSS classes used by Tasks 4–5 (all defined in `index.css` below).

- [ ] **Step 1: Scaffold**

From the repo root: `npm create vite@latest frontend -- --template react --no-interactive`
(if the flag is unknown, answer "No" to "Install with npm and start now?"), then
`cd frontend && npm install && npm install react-router-dom`.
Expected: `frontend/package.json` lists `react`, `react-dom`, `react-router-dom`.

- [ ] **Step 2: Clean the template and configure Vite**

Delete `src/App.jsx`, `src/App.css`, `src/assets/`, `public/vite.svg`.

`frontend/vite.config.js`:

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// /api is forwarded to FastAPI so the browser only ever talks to one origin in dev.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:3000',
    },
  },
})
```

`frontend/index.html`: set `<html lang="fr">`, `<title>Maison Guillard</title>`, and remove the
`<link rel="icon" ...vite.svg>` line.

In `frontend/package.json` `"scripts"`, add: `"test": "node --test src/utils/produit.test.js"`.

- [ ] **Step 3: Write the failing tests for the display rules**

Create `frontend/src/utils/produit.test.js`:

```js
import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  actionsFiche,
  disponibiliteValide,
  formatPrix,
  libelleDisponibilite,
  parseIdProduit,
  photoPrincipale,
  prixAffiche,
} from './produit.js'

// Intl inserts non-breaking spaces; normalise them to compare.
const espaces = (s) => s.replace(/\s/g, ' ')

test('formatPrix formats a decimal string in euros, French style', () => {
  assert.equal(espaces(formatPrix('199.99')), '199,99 €')
  assert.equal(espaces(formatPrix('1200.00')), '1 200,00 €')
})

test('prixAffiche prefixes sur_commande prices with "À partir de"', () => {
  assert.equal(espaces(prixAffiche({ prix: '240.00', disponibilite: 'sur_commande' })), 'À partir de 240,00 €')
  assert.equal(espaces(prixAffiche({ prix: '240.00', disponibilite: 'disponible' })), '240,00 €')
})

test('libelleDisponibilite shows rupture as "Vendu"', () => {
  assert.equal(libelleDisponibilite('disponible'), 'Disponible')
  assert.equal(libelleDisponibilite('sur_commande'), 'Sur commande')
  assert.equal(libelleDisponibilite('rupture'), 'Vendu')
})

test('disponibiliteValide keeps known values and drops anything else', () => {
  assert.equal(disponibiliteValide('rupture'), 'rupture')
  assert.equal(disponibiliteValide('foo'), null)
  assert.equal(disponibiliteValide(null), null)
})

test('photoPrincipale prefers principale, then lowest ordre, else null', () => {
  const a = { id: 1, ordre: 2, principale: false }
  const b = { id: 2, ordre: 0, principale: false }
  const c = { id: 3, ordre: 1, principale: true }
  assert.equal(photoPrincipale([a, b, c]), c)
  assert.equal(photoPrincipale([a, b]), b)
  assert.equal(photoPrincipale([]), null)
})

test('parseIdProduit accepts positive integers only', () => {
  assert.equal(parseIdProduit('12'), 12)
  assert.equal(parseIdProduit('abc'), null)
  assert.equal(parseIdProduit('0'), null)
  assert.equal(parseIdProduit('-3'), null)
  assert.equal(parseIdProduit('1.5'), null)
})

test('actionsFiche never offers the cart for sur_commande or rupture', () => {
  const libelles = (d) => actionsFiche(d).map((a) => a.libelle)
  assert.deepEqual(libelles('disponible'), ['Ajouter au panier', 'Personnaliser ce modèle'])
  assert.deepEqual(libelles('sur_commande'), ['Demander un devis'])
  assert.deepEqual(libelles('rupture'), ['Demander un modèle similaire'])
})
```

Run: `npm test` (in `frontend/`). Expected: FAIL, `Cannot find module ... produit.js`.

- [ ] **Step 4: Implement the display rules**

Create `frontend/src/utils/produit.js`:

```js
export const DISPONIBILITES = ['disponible', 'sur_commande', 'rupture']

const LIBELLES = {
  disponible: 'Disponible',
  sur_commande: 'Sur commande',
  rupture: 'Vendu',
}

export function libelleDisponibilite(disponibilite) {
  return LIBELLES[disponibilite] ?? disponibilite
}

// Anything typed by hand in the URL that the API wouldn't accept is ignored.
export function disponibiliteValide(valeur) {
  return DISPONIBILITES.includes(valeur) ? valeur : null
}

const formateurPrix = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' })

// The API sends prix as a decimal string ("199.99").
export function formatPrix(prix) {
  return formateurPrix.format(Number(prix))
}

export function prixAffiche(produit) {
  const prix = formatPrix(produit.prix)
  return produit.disponibilite === 'sur_commande' ? `À partir de ${prix}` : prix
}

export function photoPrincipale(photos) {
  if (!photos || photos.length === 0) return null
  return photos.find((p) => p.principale) ?? [...photos].sort((a, b) => a.ordre - b.ordre)[0]
}

export function parseIdProduit(valeur) {
  return /^[1-9]\d*$/.test(valeur ?? '') ? Number(valeur) : null
}

const ACTIONS = {
  disponible: [
    { libelle: 'Ajouter au panier', principale: true },
    { libelle: 'Personnaliser ce modèle', principale: false },
  ],
  sur_commande: [{ libelle: 'Demander un devis', principale: true }],
  rupture: [{ libelle: 'Demander un modèle similaire', principale: false }],
}

export function actionsFiche(disponibilite) {
  return ACTIONS[disponibilite] ?? []
}
```

Run: `npm test`. Expected: 7 tests PASS.

- [ ] **Step 5: API client and hook**

`frontend/src/api/client.js`:

```js
export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

export async function apiGet(path) {
  const res = await fetch(`/api${path}`)
  if (!res.ok) {
    throw new ApiError(res.status, `Erreur API ${res.status}`)
  }
  return res.json()
}
```

`frontend/src/api/produits.js`:

```js
import { apiGet } from './client.js'

export function getProduits({ categorie = null, disponibilite = null } = {}) {
  const params = new URLSearchParams()
  if (categorie !== null) params.set('categorie', categorie)
  if (disponibilite !== null) params.set('disponibilite', disponibilite)
  const query = params.toString()
  return apiGet(`/produits${query ? `?${query}` : ''}`)
}

export function getProduit(id) {
  return apiGet(`/produits/${id}`)
}
```

`frontend/src/api/categories.js`:

```js
import { apiGet } from './client.js'

export function getCategories() {
  return apiGet('/categories')
}
```

`frontend/src/hooks/useApi.js`:

```js
import { useCallback, useEffect, useState } from 'react'

// Runs `load` whenever `deps` change and exposes { statut, data, erreur, reessayer }.
// `cle` identifies the current request: a result stored for an older key means
// the current one is still loading, and late answers from old requests are dropped.
export function useApi(load, deps) {
  const [essai, setEssai] = useState(0)
  const cle = JSON.stringify([...deps, essai])
  const [resultat, setResultat] = useState({ cle: null, data: null, erreur: null })

  useEffect(() => {
    let annule = false
    load().then(
      (data) => { if (!annule) setResultat({ cle, data, erreur: null }) },
      (erreur) => { if (!annule) setResultat({ cle, data: null, erreur }) },
    )
    return () => { annule = true }
    // `load` is a new function on every render; `cle` already captures what it depends on.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cle])

  const reessayer = useCallback(() => setEssai((n) => n + 1), [])

  if (resultat.cle !== cle) return { statut: 'chargement', data: null, erreur: null, reessayer }
  if (resultat.erreur) return { statut: 'erreur', data: null, erreur: resultat.erreur, reessayer }
  return { statut: 'ok', data: resultat.data, erreur: null, reessayer }
}
```

- [ ] **Step 6: Styles**

Replace `frontend/src/index.css` with:

```css
:root {
  --couleur-fond: #faf7f2;
  --couleur-surface: #ffffff;
  --couleur-texte: #2b2620;
  --couleur-texte-doux: #6b6258;
  --couleur-accent: #8a5a2b;
  --couleur-bordure: #e4ddd2;
  --couleur-disponible: #2f6b3a;
  --couleur-sur-commande: #8a5a2b;
  --couleur-rupture: #8b8178;
  --couleur-erreur: #a33;
  --rayon: 8px;
  --police-titre: Georgia, 'Times New Roman', serif;
  --police-texte: system-ui, -apple-system, 'Segoe UI', sans-serif;
  color-scheme: light;
}

* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--couleur-fond);
  color: var(--couleur-texte);
  font-family: var(--police-texte);
  line-height: 1.5;
}
h1, h2 { font-family: var(--police-titre); font-weight: normal; }
a { color: inherit; }
img { display: block; max-width: 100%; }
button { font: inherit; }
button:disabled { opacity: .5; cursor: not-allowed; }

/* En-tête */
.entete {
  display: flex; flex-wrap: wrap; align-items: center; gap: 1rem 2rem;
  padding: 1rem 1.5rem;
  background: var(--couleur-surface);
  border-bottom: 1px solid var(--couleur-bordure);
}
.entete__logo { font-family: var(--police-titre); font-size: 1.5rem; text-decoration: none; }
.entete__nav { display: flex; flex-wrap: wrap; gap: 1rem; flex: 1; }
.entete__nav a { text-decoration: none; color: var(--couleur-texte-doux); }
.entete__nav a.active { color: var(--couleur-accent); font-weight: 600; }
.entete__actions { display: flex; gap: .5rem; }

.contenu { max-width: 1200px; margin: 0 auto; padding: 1.5rem 1rem 3rem; }

/* Boutons */
.bouton {
  padding: .6rem 1.2rem;
  border: 1px solid var(--couleur-accent); border-radius: var(--rayon);
  background: var(--couleur-surface); color: var(--couleur-accent);
  cursor: pointer;
}
.bouton--principal { background: var(--couleur-accent); color: #fff; }

/* Filtres */
.barre-filtres {
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;
  gap: 1rem; margin-bottom: 1.5rem;
}
.filtre { display: flex; flex-wrap: wrap; gap: .5rem; }
.puce {
  padding: .35rem .9rem;
  border: 1px solid var(--couleur-bordure); border-radius: 999px;
  background: var(--couleur-surface); text-decoration: none;
}
.puce.active { background: var(--couleur-accent); border-color: var(--couleur-accent); color: #fff; }
.filtre-dispo { display: flex; align-items: center; gap: .5rem; color: var(--couleur-texte-doux); }
.filtre-dispo select {
  padding: .35rem .5rem;
  border: 1px solid var(--couleur-bordure); border-radius: var(--rayon);
  background: var(--couleur-surface); font: inherit;
}

/* Grille et cartes : 3 → 2 → 1 colonnes selon la largeur */
.grille { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1.5rem; }
.carte {
  background: var(--couleur-surface);
  border: 1px solid var(--couleur-bordure); border-radius: var(--rayon);
  overflow: hidden; transition: box-shadow .15s;
}
.carte:hover { box-shadow: 0 4px 16px rgb(0 0 0 / .08); }
.carte__lien { display: block; text-decoration: none; }
.carte__photo { width: 100%; aspect-ratio: 4 / 3; object-fit: cover; }
.photo-vide {
  display: grid; place-items: center; aspect-ratio: 4 / 3;
  background: var(--couleur-bordure); color: var(--couleur-texte-doux);
}
.carte__infos { display: grid; gap: .25rem; padding: 1rem; }
.carte__nom { margin: 0; font-size: 1.15rem; }
.carte__prix { margin: 0; font-weight: 600; }

.badge { justify-self: start; padding: .1rem .6rem; border-radius: 999px; font-size: .8rem; color: #fff; }
.badge--disponible { background: var(--couleur-disponible); }
.badge--sur_commande { background: var(--couleur-sur-commande); }
.badge--rupture { background: var(--couleur-rupture); }

/* Fiche produit */
.retour { display: inline-block; margin-bottom: 1rem; color: var(--couleur-texte-doux); }
.fiche { display: grid; grid-template-columns: 3fr 2fr; gap: 2rem; align-items: start; }
.galerie__grande { width: 100%; aspect-ratio: 4 / 3; object-fit: cover; border-radius: var(--rayon); }
.galerie .photo-vide { border-radius: var(--rayon); }
.galerie__vignettes { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .75rem; }
.galerie__vignette {
  width: 80px; padding: 0;
  border: 2px solid transparent; border-radius: var(--rayon);
  background: none; overflow: hidden; cursor: pointer;
}
.galerie__vignette img { width: 100%; aspect-ratio: 1; object-fit: cover; }
.galerie__vignette--active { border-color: var(--couleur-accent); }
.infos { display: grid; gap: .75rem; }
.infos h1 { margin: 0; }
.infos__prix { margin: 0; font-size: 1.4rem; font-weight: 600; }
.infos__note { margin: 0; color: var(--couleur-texte-doux); font-style: italic; }
.infos__details { display: grid; grid-template-columns: auto 1fr; gap: .25rem 1rem; margin: 0; }
.infos__details dt { color: var(--couleur-texte-doux); }
.infos__details dd { margin: 0; }
.infos__actions { display: flex; flex-wrap: wrap; gap: .75rem; margin-top: .5rem; }

/* États chargement / erreur / vide / 404 */
.etat { padding: 3rem 1rem; text-align: center; color: var(--couleur-texte-doux); }
.etat--erreur p { color: var(--couleur-erreur); }

@media (max-width: 768px) {
  .entete { padding: 1rem; }
  .fiche { grid-template-columns: 1fr; }
}
```

- [ ] **Step 7: README**

In `README.md`, replace `3. Frontend: (not started yet — S4 in progress)` with:

````
3. Frontend (backend must be running on port 3000):
   ```
   cd frontend
   npm install
   npm run dev      # http://localhost:5173 — /api is proxied to the backend
   npm test         # display rules (node --test)
   ```
````

- [ ] **Step 8: Verify and commit**

Run in `frontend/`: `npm test` (7 PASS). `src/main.jsx` still imports the deleted `App.jsx`, so
the build is checked at the end of Task 4.

```bash
git add frontend README.md
git commit -m "feat: scaffold frontend with API client and display rules"
```

---

### Task 4: Catalogue page with filters (frontend)

**Files:**
- Create: `frontend/src/Layout.jsx`, `frontend/src/components/Header.jsx`,
  `frontend/src/components/EtatChargement.jsx`, `frontend/src/components/BadgeDisponibilite.jsx`,
  `frontend/src/components/FiltreCategorie.jsx`, `frontend/src/components/FiltreDisponibilite.jsx`,
  `frontend/src/components/CarteProduit.jsx`, `frontend/src/pages/PageCatalogue.jsx`,
  `frontend/src/pages/PageIntrouvable.jsx`
- Replace: `frontend/src/main.jsx`

**Interfaces:**
- Consumes: everything produced by Task 3.
- Produces: routes `/`, `/categorie/:slug`, `*`; `<Outlet context={{ categories }}>` where
  `categories` is a `useApi` result; components `EtatChargement`, `BadgeDisponibilite`,
  `PageIntrouvable` reused by Task 5.

- [ ] **Step 1: Shared components**

`frontend/src/components/EtatChargement.jsx`:

```jsx
export default function EtatChargement({ statut, reessayer, vide = false, messageVide = '', children }) {
  if (statut === 'chargement') {
    return <p className="etat">Chargement…</p>
  }
  if (statut === 'erreur') {
    return (
      <div className="etat etat--erreur">
        <p>Impossible de charger les données.</p>
        <button type="button" className="bouton" onClick={reessayer}>Réessayer</button>
      </div>
    )
  }
  if (vide) {
    return <p className="etat">{messageVide}</p>
  }
  return children
}
```

`frontend/src/components/BadgeDisponibilite.jsx`:

```jsx
import { libelleDisponibilite } from '../utils/produit.js'

export default function BadgeDisponibilite({ disponibilite }) {
  return <span className={`badge badge--${disponibilite}`}>{libelleDisponibilite(disponibilite)}</span>
}
```

`frontend/src/pages/PageIntrouvable.jsx`:

```jsx
import { Link } from 'react-router-dom'

export default function PageIntrouvable() {
  return (
    <section className="etat">
      <h1>Page introuvable</h1>
      <p>Ce que vous cherchez n'existe pas ou plus.</p>
      <Link to="/">Retour au catalogue</Link>
    </section>
  )
}
```

- [ ] **Step 2: Header and layout**

`frontend/src/components/Header.jsx`:

```jsx
import { Link, NavLink } from 'react-router-dom'

export default function Header({ categories }) {
  return (
    <header className="entete">
      <Link to="/" className="entete__logo">Maison Guillard</Link>
      <nav className="entete__nav" aria-label="Catégories">
        <NavLink to="/" end>Catalogue</NavLink>
        {categories.map((c) => (
          <NavLink key={c.id} to={`/categorie/${c.slug}`}>{c.nom}</NavLink>
        ))}
      </nav>
      <div className="entete__actions">
        <button type="button" className="bouton" disabled title="Bientôt disponible">Projet sur mesure</button>
        <button type="button" className="bouton" disabled title="Bientôt disponible">Panier</button>
      </div>
    </header>
  )
}
```

`frontend/src/Layout.jsx`:

```jsx
import { Outlet } from 'react-router-dom'
import Header from './components/Header.jsx'
import { getCategories } from './api/categories.js'
import { useApi } from './hooks/useApi.js'

// Categories are loaded once here: the header and the catalogue filters both need them.
export default function Layout() {
  const categories = useApi(getCategories, [])
  return (
    <>
      <Header categories={categories.data ?? []} />
      <main className="contenu">
        <Outlet context={{ categories }} />
      </main>
    </>
  )
}
```

- [ ] **Step 3: Filters and card**

`frontend/src/components/FiltreCategorie.jsx`:

```jsx
import { NavLink, useLocation } from 'react-router-dom'

// Keeps the current ?disponibilite= when switching category.
export default function FiltreCategorie({ categories }) {
  const { search } = useLocation()
  return (
    <nav className="filtre" aria-label="Filtrer par catégorie">
      <NavLink to={{ pathname: '/', search }} end className="puce">Toutes</NavLink>
      {categories.map((c) => (
        <NavLink key={c.id} to={{ pathname: `/categorie/${c.slug}`, search }} className="puce">
          {c.nom}
        </NavLink>
      ))}
    </nav>
  )
}
```

`frontend/src/components/FiltreDisponibilite.jsx`:

```jsx
import { useSearchParams } from 'react-router-dom'
import { DISPONIBILITES, disponibiliteValide, libelleDisponibilite } from '../utils/produit.js'

export default function FiltreDisponibilite() {
  const [params, setParams] = useSearchParams()
  const valeur = disponibiliteValide(params.get('disponibilite')) ?? ''

  function changer(event) {
    const suivants = new URLSearchParams(params)
    if (event.target.value) suivants.set('disponibilite', event.target.value)
    else suivants.delete('disponibilite')
    setParams(suivants)
  }

  return (
    <label className="filtre-dispo">
      Disponibilité
      <select value={valeur} onChange={changer}>
        <option value="">Toutes</option>
        {DISPONIBILITES.map((d) => (
          <option key={d} value={d}>{libelleDisponibilite(d)}</option>
        ))}
      </select>
    </label>
  )
}
```

`frontend/src/components/CarteProduit.jsx`:

```jsx
import { Link } from 'react-router-dom'
import BadgeDisponibilite from './BadgeDisponibilite.jsx'
import { photoPrincipale, prixAffiche } from '../utils/produit.js'

export default function CarteProduit({ produit }) {
  const photo = photoPrincipale(produit.photos)
  return (
    <article className="carte">
      <Link to={`/produits/${produit.id}`} className="carte__lien">
        {photo
          ? <img src={photo.url} alt={produit.nom} className="carte__photo" loading="lazy" />
          : <div className="photo-vide">Photo à venir</div>}
        <div className="carte__infos">
          <h2 className="carte__nom">{produit.nom}</h2>
          <p className="carte__prix">{prixAffiche(produit)}</p>
          <BadgeDisponibilite disponibilite={produit.disponibilite} />
        </div>
      </Link>
    </article>
  )
}
```

- [ ] **Step 4: Catalogue page**

`frontend/src/pages/PageCatalogue.jsx`:

```jsx
import { useOutletContext, useParams, useSearchParams } from 'react-router-dom'
import CarteProduit from '../components/CarteProduit.jsx'
import EtatChargement from '../components/EtatChargement.jsx'
import FiltreCategorie from '../components/FiltreCategorie.jsx'
import FiltreDisponibilite from '../components/FiltreDisponibilite.jsx'
import PageIntrouvable from './PageIntrouvable.jsx'
import { getProduits } from '../api/produits.js'
import { useApi } from '../hooks/useApi.js'
import { disponibiliteValide } from '../utils/produit.js'

export default function PageCatalogue() {
  const { slug } = useParams()
  const [params] = useSearchParams()
  const { categories } = useOutletContext()

  const disponibilite = disponibiliteValide(params.get('disponibilite'))
  const categorie = slug ? categories.data?.find((c) => c.slug === slug) : null
  const categorieId = categorie?.id ?? null

  const produits = useApi(
    () => getProduits({ categorie: categorieId, disponibilite }),
    [categorieId, disponibilite],
  )

  if (slug && categories.statut === 'ok' && !categorie) {
    return <PageIntrouvable />
  }

  // With a slug, the category list must be loaded before the product list means anything.
  const enCours = slug && categories.statut !== 'ok' ? categories : produits

  return (
    <section>
      <h1>{categorie ? categorie.nom : 'Catalogue'}</h1>
      <div className="barre-filtres">
        <FiltreCategorie categories={categories.data ?? []} />
        <FiltreDisponibilite />
      </div>
      <EtatChargement
        statut={enCours.statut}
        reessayer={enCours.reessayer}
        vide={produits.data?.length === 0}
        messageVide="Aucun produit ne correspond à ces critères."
      >
        <div className="grille">
          {produits.data?.map((p) => <CarteProduit key={p.id} produit={p} />)}
        </div>
      </EtatChargement>
    </section>
  )
}
```

- [ ] **Step 5: Router**

Replace `frontend/src/main.jsx` with:

```jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './index.css'
import Layout from './Layout.jsx'
import PageCatalogue from './pages/PageCatalogue.jsx'
import PageIntrouvable from './pages/PageIntrouvable.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<PageCatalogue />} />
          <Route path="categorie/:slug" element={<PageCatalogue />} />
          <Route path="*" element={<PageIntrouvable />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
```

- [ ] **Step 6: Verify**

In `frontend/`: `npm run lint` → no errors; `npm run build` → succeeds; `npm test` → 7 PASS.
With the backend on port 3000 and the catalogue seeded, `npm run dev`, then in the browser:
- `/` shows 12 cards with placeholders "Photo à venir", prices like "À partir de 240,00 €" on
  `sur_commande` items and "Vendu" badges on `rupture` items.
- Header and filter links switch category; `/categorie/lampes` shows 3 produits.
- Disponibilité select adds `?disponibilite=...`; switching category keeps it.
- `/?disponibilite=foo` shows all 12 produits; `/categorie/inconnue` shows "Page introuvable".
- Stop the backend, reload: "Impossible de charger les données" + "Réessayer"; restart backend,
  click "Réessayer": the list comes back.

- [ ] **Step 7: Commit**

```bash
git add frontend
git commit -m "feat: add public catalogue with category and availability filters"
```

---

### Task 5: Fiche produit page (frontend)

**Files:**
- Create: `frontend/src/components/GaleriePhotos.jsx`, `frontend/src/components/InfosProduit.jsx`,
  `frontend/src/pages/PageFicheProduit.jsx`
- Modify: `frontend/src/main.jsx` (add one route)

**Interfaces:**
- Consumes: `getProduit`, `ApiError.status`, `useApi`, `parseIdProduit`, `photoPrincipale`,
  `prixAffiche`, `actionsFiche` (Task 3); `EtatChargement`, `BadgeDisponibilite`,
  `PageIntrouvable` (Task 4).
- Produces: route `/produits/:id`.

- [ ] **Step 1: Gallery**

`frontend/src/components/GaleriePhotos.jsx`:

```jsx
import { useState } from 'react'
import { photoPrincipale } from '../utils/produit.js'

export default function GaleriePhotos({ photos, nom }) {
  const [selectionId, setSelectionId] = useState(null)

  if (photos.length === 0) {
    return <div className="galerie"><div className="photo-vide">Photo à venir</div></div>
  }

  const affichee = photos.find((p) => p.id === selectionId) ?? photoPrincipale(photos)

  return (
    <div className="galerie">
      <img src={affichee.url} alt={nom} className="galerie__grande" />
      {photos.length > 1 && (
        <div className="galerie__vignettes">
          {photos.map((p, index) => (
            <button
              key={p.id}
              type="button"
              className={`galerie__vignette${p.id === affichee.id ? ' galerie__vignette--active' : ''}`}
              onClick={() => setSelectionId(p.id)}
              aria-label={`Voir la photo ${index + 1}`}
            >
              <img src={p.url} alt="" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Product info**

`frontend/src/components/InfosProduit.jsx`:

```jsx
import BadgeDisponibilite from './BadgeDisponibilite.jsx'
import { actionsFiche, prixAffiche } from '../utils/produit.js'

export default function InfosProduit({ produit }) {
  return (
    <div className="infos">
      <h1>{produit.nom}</h1>
      <p className="infos__prix">{prixAffiche(produit)}</p>
      <BadgeDisponibilite disponibilite={produit.disponibilite} />
      {produit.disponibilite === 'sur_commande' && (
        <p className="infos__note">
          Fabriqué à la demande : prix et délai confirmés par l'artisan sur devis.
        </p>
      )}
      <dl className="infos__details">
        <dt>Dimensions</dt>
        <dd>{produit.dimensions}</dd>
      </dl>
      <p>{produit.description}</p>
      <div className="infos__actions">
        {actionsFiche(produit.disponibilite).map((action) => (
          <button
            key={action.libelle}
            type="button"
            className={action.principale ? 'bouton bouton--principal' : 'bouton'}
            disabled
            title="Bientôt disponible"
          >
            {action.libelle}
          </button>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Page**

`frontend/src/pages/PageFicheProduit.jsx`:

```jsx
import { Link, useParams } from 'react-router-dom'
import EtatChargement from '../components/EtatChargement.jsx'
import GaleriePhotos from '../components/GaleriePhotos.jsx'
import InfosProduit from '../components/InfosProduit.jsx'
import PageIntrouvable from './PageIntrouvable.jsx'
import { getProduit } from '../api/produits.js'
import { useApi } from '../hooks/useApi.js'
import { parseIdProduit } from '../utils/produit.js'

export default function PageFicheProduit() {
  const { id } = useParams()
  const produitId = parseIdProduit(id)
  const produit = useApi(
    () => (produitId === null ? Promise.resolve(null) : getProduit(produitId)),
    [produitId],
  )

  if (produitId === null || produit.erreur?.status === 404) {
    return <PageIntrouvable />
  }

  return (
    <section>
      <Link to="/" className="retour">← Retour au catalogue</Link>
      <EtatChargement statut={produit.statut} reessayer={produit.reessayer}>
        {produit.data && (
          <article className="fiche">
            <GaleriePhotos key={produit.data.id} photos={produit.data.photos} nom={produit.data.nom} />
            <InfosProduit produit={produit.data} />
          </article>
        )}
      </EtatChargement>
    </section>
  )
}
```

(`key={produit.data.id}` resets the selected thumbnail when navigating to another produit.)

- [ ] **Step 4: Route**

In `frontend/src/main.jsx`, add `import PageFicheProduit from './pages/PageFicheProduit.jsx'` and,
just above the `path="*"` route:

```jsx
          <Route path="produits/:id" element={<PageFicheProduit />} />
```

- [ ] **Step 5: Verify**

`npm run lint`, `npm run build`, `npm test` all clean. In the browser (backend running):
- Upload 3 photos to one `disponible` produit via Swagger (`http://localhost:3000/docs`,
  `POST /api/produits/{id}/photos` with `ordre` 0, 1, 2), mark the second as principale.
- Its card shows the principale photo; its fiche shows the large photo + 3 thumbnails, clicking a
  thumbnail switches the large photo.
- Fiche of a `disponible` produit: "Ajouter au panier" (filled) + "Personnaliser ce modèle", both
  disabled. `sur_commande`: "À partir de …", note "Fabriqué à la demande…", "Demander un devis"
  only. `rupture`: "Vendu" badge, "Demander un modèle similaire" only.
- `/produits/999999`, `/produits/abc`, `/produits/0` → "Page introuvable".
- Window narrower than 768px: gallery above infos, grid in 1–2 columns, header wraps.

- [ ] **Step 6: Commit**

```bash
git add frontend
git commit -m "feat: add fiche produit page with photo gallery"
```

---

### Task 6: Wrap-up

**Files:** none new.

- [ ] **Step 1: Full verification**

Backend: `.\.venv\Scripts\python.exe -m pytest -v` → all PASS.
Frontend: `npm run lint && npm test && npm run build` → clean.

- [ ] **Step 2: No-trace check**

Grep the branch's commit messages (`git log main..HEAD --format=%B`) and tracked files
(`git grep -i`) for the names of the tools used during development; both must return nothing.

- [ ] **Step 3: Push**

`git push -u origin Branche-S6` (PR and merge decided with Remy at that point).
