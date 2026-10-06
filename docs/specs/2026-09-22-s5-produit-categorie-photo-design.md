# S5 — Back-office CRUD produits, catégories, photos — Design

> Base: `docs/specs/2026-09-14-maison-guillard-mvp-design.md` (product/stack context) and
> the revised doc technique (`Documentation/Maison-Guillard-Doc-Technique.pdf`, Python/FastAPI/SQLAlchemy).
> S4 (auth) is complete on `main` — this spec covers S5 per the plan de route: "Back-office : CRUD
> produits, gestion des catégories et des photographies."

## Scope

One implementation plan covering all three domains together: `Categorie`, `Produit`, `Photo`. No
further decomposition for this iteration.

## Decisions from brainstorming

- **Cloudinary is stubbed for S5.** `photo_service.upload_to_cloudinary` does not call the real
  Cloudinary API. It saves the uploaded file to a local `backend/uploads/` directory (gitignored)
  and returns a locally-served URL. The function signature (`upload_to_cloudinary(fichier) -> url`)
  stays stable so a later swap to the real Cloudinary SDK only touches this one function.
- **Uploaded files are kept**, not discarded — served back via FastAPI `StaticFiles` mounted at
  `/uploads`, so photos are actually viewable during development.
- **Exactly one `principale` photo per produit at a time.** Setting a new principale photo
  atomically un-sets any previous one for the same `produit_id`.
- **No auto-principale on first upload.** The admin always chooses the principale photo
  explicitly — there is no implicit "first photo becomes principale" behavior. This adds one
  endpoint beyond what the original doc technique table lists: `PATCH /photos/:id/principale`.

## Architecture

Same layered pattern already established in S4 (auth): router → Pydantic schema (validation) →
service (business logic, unit-testable in isolation with a mocked DB session) → SQLAlchemy model.
Three new domains added this way: `produit`, `categorie`, `photo`.

- **Admin-protected routes** reuse the existing `require_admin` FastAPI dependency unchanged.
- **Public read routes** (`GET /produits`, `GET /produits/:id`, `GET /categories`) have no auth.

## Data model

New SQLAlchemy models in `app/models/`:

- `Categorie`: `id` PK, `nom`, `slug` (unique)
- `Produit`: `id` PK, `nom`, `description`, `categorie_id` FK → Categorie, `prix` (numeric),
  `dimensions` (string), `disponibilite` (enum: `disponible` / `rupture` / `sur_commande`),
  `created_at`
- `Photo`: `id` PK, `produit_id` FK → Produit (`ondelete=CASCADE`), `url`, `ordre` (int), `principale`
  (bool)

One Alembic migration adds all three tables, their FKs, and the `disponibilite` enum type.

## Components

**Services** (`app/services/`):
- `categorie_service`: `get_all()`, `create(data)`, `update(id, data)`, `delete(id)` — `delete`
  raises a conflict error if any `Produit` references the category (mapped to HTTP 409 in the
  router).
- `produit_service`: `get_all(filtres?)` (filters: `categorie`, `disponibilite`), `get_by_id(id)`,
  `create(data)`, `update(id, data)` (partial fields), `delete(id)`, `set_disponibilite(id, statut)`.
- `photo_service`: `upload_to_cloudinary(fichier)` (stub, see Decisions), `attach_to_produit(produit_id,
  url, ordre)`, `delete(id)`, `set_principale(id)` (un-sets any other principale photo for the same
  produit in the same DB transaction).

**Routers** (`app/routers/`): `produits.py` (also owns the two photo endpoints, since photos are
always accessed through a produit), `categories.py`. Same shape as the existing `auth.py` router.

**Schemas** (`app/schemas/`): `ProduitCreate`, `ProduitUpdate` (all fields optional), `ProduitOut`,
`CategorieCreate`, `CategorieOut`, `PhotoOut`.

## API endpoints

Base URL `/api`. Admin auth = `Authorization: Bearer <token>`, same as S4.

| Méthode | Path | Auth | Input | Output |
|---|---|---|---|---|
| GET | `/produits` | — | `?categorie&disponibilite` | 200 `[Produit]` |
| GET | `/produits/:id` | — | — | 200 `Produit` / 404 |
| POST | `/produits` | admin | `{nom, description, categorie_id, prix, dimensions, disponibilite}` | 201 `Produit` / 422 |
| PUT | `/produits/:id` | admin | champs partiels | 200 `Produit` / 404 |
| DELETE | `/produits/:id` | admin | — | 204 / 404 |
| POST | `/produits/:id/photos` | admin | multipart `{fichier, ordre?}` | 201 `Photo` |
| PATCH | `/photos/:id/principale` | admin | — | 200 `Photo` (new endpoint, not in original doc technique table — added per brainstorming decision) |
| DELETE | `/photos/:id` | admin | — | 204 |
| GET | `/categories` | — | — | 200 `[Categorie]` |
| POST | `/categories` | admin | `{nom, slug}` | 201 `Categorie` |
| DELETE | `/categories/:id` | admin | — | 204 / 409 |

**Error codes:** 401 non authentifié, 403 non autorisé, 404 ressource absente, 409 conflit
(suppression d'une catégorie utilisée par des produits), 422 erreur de validation Pydantic.

## Testing strategy

Same pattern as S4:
- **Unit tests** (pytest): each service, with the DB session mocked — covers business rules
  (category-in-use conflict, single-principale-photo invariant, partial update merging) without
  hitting Postgres.
- **Integration tests** (pytest + FastAPI `TestClient`, real Postgres test DB, migrations applied):
  cover the endpoints end-to-end, including a real multipart file upload exercising the stub
  `upload_to_cloudinary` (assert the file lands under `backend/uploads/` and the returned URL is
  reachable via the `/uploads` static mount).

## Out of scope for S5

Real Cloudinary integration (kept as a stub, swapped in a later week once credentials exist),
public catalog pages (S6), cart/order/quote flows (S7-S8), search/keyword filtering (COULD-priority
user story, not committed to this MVP timeline).
