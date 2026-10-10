# S6 — Site public : catalogue, fiches produits, navigation par catégorie — Design

> Base: `docs/specs/2026-09-14-maison-guillard-mvp-design.md` (product/stack context) and the doc
> technique (`Documentation/Maison-Guillard-Doc-Technique.pdf`: wireframes "Catalogue" and "Fiche
> produit", component list `PageCatalogue`, `FiltreCategorie`, `CarteProduit`, `PageFicheProduit`,
> `GaleriePhotos`, `InfosProduit`). S5 (back-office API) is complete on `main`.

## Context and scope

The project is behind the plan de route (on 2026-10-10 the plan expects S8: tests, responsive,
documentation). The remaining work is split into five sub-projects, each with its own spec, plan
and implementation, in this order:

1. **Site public** (this spec) — catalogue, fiche produit, navigation and filters.
2. Achat direct — panier, commande, confirmation (backend + frontend).
3. Demande de devis — formulaire, confirmation (backend + frontend).
4. Back-office UI — login admin, CRUD produits/catégories, upload photo (frontend only, API exists).
5. Back-office commandes et devis — listing and status changes (backend + frontend).

`frontend/` is empty on `main` (the S4 login page scaffold was never committed), so this spec also
creates the frontend project itself.

**Out of scope here:** cart, orders, quotes, admin UI, real Cloudinary integration (still stubbed,
see below), frontend automated tests.

## Decisions from brainstorming

- **Photos embedded in `ProduitOut`.** Add a `photos` relationship on `Produit` and a
  `photos: list[PhotoOut]` field on `ProduitOut`. One request gives the catalogue card its
  principale photo and the fiche its full gallery. Rejected: a separate
  `GET /produits/{id}/photos` endpoint (one extra request per card), and a single
  `photo_principale_url` field (not enough for the gallery).
- **Photo URLs are opaque and absolute.** `upload_to_cloudinary()` already returns an absolute URL
  (`http://localhost:3000/uploads/...` with the stub, `https://res.cloudinary.com/...` once the
  real integration lands). The frontend uses `photo.url` as-is in `<img src>` and never builds an
  image URL itself, so swapping the stub for real Cloudinary requires no frontend change.
- **Vite dev proxy instead of CORS middleware.** Vite proxies `/api` to `http://localhost:3000`, so
  API calls are same-origin in development. Images need no proxy: cross-origin `<img>` loads do not
  require CORS.
- **Business meaning of `disponibilite`**, and what the fiche produit shows:

  | Value | Meaning | Fiche produit actions |
  |---|---|---|
  | `disponible` | Piece already made, in stock, fixed price | "Ajouter au panier" (primary) + "Personnaliser ce modèle" (devis, secondary) |
  | `sur_commande` | Made by the artisan only on request; price varies (wood, dimensions…) | Price shown as "À partir de X €" + "Demander un devis" (primary). Never purchasable directly. |
  | `rupture` | Piece sold, kept in the catalogue as a showcase | Badge "Vendu" + "Demander un modèle similaire" (devis) |

  The header also has a "Projet sur mesure" link (devis with no product attached). In this
  sub-project every cart/devis button and link is rendered **disabled**; sub-projects 2 and 3 wire
  them up. The enum stays unchanged in the database: "Vendu" is a UI label only.
- **Plain CSS** with custom properties in `src/index.css`; no CSS framework (fewer dependencies,
  easier to explain).
- **Filters live in the URL**: category as a path segment (`/categorie/:slug`), availability as a
  query string (`?disponibilite=disponible`). Links are shareable and the back button works.

## Backend changes

### `app/models/produit.py`

```python
photos = relationship(
    "Photo", order_by="Photo.ordre", passive_deletes=True, lazy="selectin"
)
```

- No Alembic migration: a `relationship()` is ORM-only and does not change the schema.
- `passive_deletes=True` is required. `photo.produit_id` is `NOT NULL` with `ON DELETE CASCADE` in
  the database; without it, SQLAlchemy would try to set `produit_id = NULL` on loaded photos when a
  produit is deleted and fail with an `IntegrityError`. With it, SQLAlchemy lets PostgreSQL's
  cascade delete the photos.
- `lazy="selectin"` loads the photos of every produit in a list with one extra query (no N+1).

### `app/schemas/produit.py`

`ProduitOut` gains `photos: list[PhotoOut] = []`. `ProduitCreate`/`ProduitUpdate` are unchanged
(photos are still managed through the photo endpoints).

### Tests (`tests/integration/test_produits_routes.py`)

- `GET /api/produits` returns each produit with its `photos`, sorted by `ordre`.
- `GET /api/produits/{id}` returns `photos` sorted by `ordre`.
- A produit with no photo returns `"photos": []`.
- Deleting a produit that has photos still returns `204` and removes its photos (regression guard
  for `passive_deletes`).

## Frontend

### Setup

- `npm create vite@latest frontend -- --template react` (plain JavaScript), plus `react-router-dom`.
- `vite.config.js`: `server.proxy = { '/api': 'http://localhost:3000' }`.
- README: add the frontend start command (`cd frontend && npm install && npm run dev`).

### Structure

```
frontend/src/
  main.jsx                  # BrowserRouter + routes
  index.css                 # CSS variables, base styles, responsive grid
  api/client.js             # apiGet(path): fetch('/api' + path), throws Error on !res.ok
  api/produits.js           # getProduits({ categorie, disponibilite }), getProduit(id)
  api/categories.js         # getCategories()
  components/Header.jsx     # logo, category nav, "Projet sur mesure" (disabled), cart link (disabled)
  components/FiltreCategorie.jsx
  components/FiltreDisponibilite.jsx
  components/CarteProduit.jsx    # principale photo (or first, or placeholder), nom, prix, badge
  components/GaleriePhotos.jsx   # large photo + thumbnails, click to switch
  components/InfosProduit.jsx    # nom, prix, dimensions, description, badge, actions per disponibilite
  components/EtatChargement.jsx  # shared loading / error (+ retry) / empty display
  pages/PageCatalogue.jsx        # routes "/" and "/categorie/:slug"
  pages/PageFicheProduit.jsx     # route "/produits/:id"
  pages/PageIntrouvable.jsx      # "*" and unknown slug / produit id (404)
  utils/format.js                # formatPrix (fr-FR, EUR), libelleDisponibilite
```

### Data flow

- **PageCatalogue** loads `getCategories()` once (needed by `Header` and `FiltreCategorie`). It
  resolves `:slug` to a `categorie_id`; an unknown slug renders `PageIntrouvable`. It then calls
  `getProduits({ categorie, disponibilite })` and reloads whenever the slug or query string
  changes.
- **PageFicheProduit** calls `getProduit(id)`; a `404` from the API renders `PageIntrouvable`.
- **Photo choice for a card:** the photo with `principale: true`, else the first one by `ordre`,
  else a neutral placeholder.
- **Prices:** the API sends `prix` as a decimal string; `formatPrix` converts it with
  `Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' })`.

### States and errors

Every page handles three states through `EtatChargement`: loading, error (message + "Réessayer"
button that re-runs the request), and empty ("Aucun produit dans cette catégorie" etc.).

### Responsive

Product grid: `grid-template-columns: repeat(auto-fill, minmax(260px, 1fr))` (3 → 2 → 1 columns).
On narrow screens the fiche stacks the gallery above the info, and the header nav wraps.

## Verification

- Backend: `pytest` green, including the new tests.
- Frontend: manual check in the browser against `seed.py` data plus a few photos uploaded via
  Swagger: catalogue, each category, each availability filter, fiche of each `disponibilite`,
  unknown slug and unknown id (404 page), API stopped (error state + retry), narrow window
  (responsive).
- No frontend test framework in this sub-project.
