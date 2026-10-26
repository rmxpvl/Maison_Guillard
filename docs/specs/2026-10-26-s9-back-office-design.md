# S9 — Back-office (essentiel) — Design

> Base: `docs/specs/2026-09-14-maison-guillard-mvp-design.md` and the doc technique (back-office
> wireframes, `PageLoginAdmin`, `DashboardAdmin`, `PageListeProduits`, `FormulaireProduit`,
> `UploadPhoto`, `PageListeCommandes`, `PageListeDevis`, `AuthContext`). S7 (orders) and S8
> (quotes) are merged on `main`.

## Context and scope

Last block before the jury (2026-10-30). The artisan logs in and manages her catalogue, her orders
and her quote requests, and turns the order/quote emails on or off.

**In scope (option A, chosen 2026-10-26):** admin login/logout; dashboard with the email toggle and
three tabs: Produits (list, create, edit, delete, photos), Commandes (list, detail, status), Devis
(list, detail, status).

**Out of scope:** category management (stays in Swagger: 4 categories, rarely changed), search,
status-transition rules, pagination.

## Backend

New admin routes (all behind `require_admin`):

| Method | Path | Input | Output |
|---|---|---|---|
| GET | `/api/commandes` | `?statut` optional | 200 `[CommandeOut]`, newest first / 401 |
| PATCH | `/api/commandes/{id}/statut` | `{statut}` | 200 `CommandeOut` / 401 / 404 / 422 |
| GET | `/api/devis` | `?statut` optional | 200 `[DevisOut]`, newest first / 401 |
| PATCH | `/api/devis/{id}/statut` | `{statut}` | 200 `DevisOut` / 401 / 404 / 422 |

- Any status can follow any other (basic version). Unknown status → 422 (Pydantic enum).
- `LigneCommandeOut` and `DevisOut` gain `nom_produit` (from a `nom_produit` property on the model,
  `None` when there is no product), so the admin sees names rather than ids.
- Services: `commande_service.get_all(db, statut=None)`, `commande_service.update_statut(db, id,
  statut) -> Commande | None`; same two functions in `devis_service`.

## Frontend

### Authentication

- `context/AuthContext.jsx` (`AuthProvider`) + `hooks/useAuth.js`: `{ token, connexion(email,
  motDePasse), deconnexion(), appel(path, options) }`. The token is kept in **sessionStorage**
  (cleared when the browser closes; it also expires after 8 h server-side).
- `appel` sends `Authorization: Bearer <token>` and JSON or multipart bodies; on a 401 it logs out,
  which sends the user back to the login page.
- `/admin/connexion` → `PageConnexionAdmin`. `RouteAdmin` wraps every other `/admin` route:
  without a token → redirect to `/admin/connexion`.
- On `/admin` pages the public header and footer are hidden; `BarreAdmin` shows « Maison Guillard ·
  Administration », the tabs and « Déconnexion ».

### Screens

- `/admin` → `PageAdmin` with the email toggle (`GET`/`PUT /api/parametres`) and tabs kept in the
  URL (`?onglet=produits|commandes|devis`):
  - **Produits**: table (photo, nom, prix, disponibilité), « Nouveau produit », « Modifier »,
    « Supprimer » (confirmation; the 409 message is shown when the product is in an order).
  - **Commandes**: table (n°, date, client, total, statut); a row opens its detail (contact,
    address, lines with product names) with a status `<select>`.
  - **Devis**: table (n°, date, client, produit, statut); detail shows the description and a status
    `<select>`.
- `/admin/produits/nouveau` and `/admin/produits/:id` → `PageProduitAdmin`: form (nom,
  description, catégorie, prix, dimensions, disponibilité); in edit mode a photo section (add a
  file, set as main, delete).
- Pure helpers in `utils/admin.js` (status labels, product form ↔ API payload, date format),
  tested with `node:test`.

## Testing

- Backend: unit tests for the new service functions; integration tests for the four routes
  (401 without token, list order and filter, status change, 404, 422) and `nom_produit`.
- Frontend: `node:test` on `utils/admin.js`; build and lint clean.
- Manual: full back-office walkthrough in the browser.
