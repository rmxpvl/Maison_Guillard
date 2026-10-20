# S7 — Achat direct : panier, commande, confirmation — Design

> Base: `docs/specs/2026-09-14-maison-guillard-mvp-design.md` (product/stack context) and the doc
> technique (`Documentation/Maison-Guillard-Doc-Technique.pdf`: tables `commande` and
> `ligne_commande`, endpoint `POST /commandes`, `commande_service`, components `PagePanier`,
> `LigneArticlePanier`, `PageFormulaireCommande`, `PageConfirmationCommande`, `PanierContext`).
> S6 (site public) is complete on `main`.

## Context and scope

Second of the five remaining sub-projects (site public → **achat direct** → devis → back-office UI
→ back-office commandes et devis). A visitor adds available pieces to a cart, fills in contact
details, and sends the order. The order is stored with status `en_attente`, the visitor sees a
confirmation page, and the artisan follows up by email or phone for payment and delivery.

Optionally (admin setting, **off by default**), an email is sent to the artisan and a recap to the
customer when an order is created.

**Out of scope here:** online payment, stock management, `GET /commandes` and
`PATCH /commandes/{id}/statut` (back-office commandes block), the admin UI toggle for the email
setting (back-office UI block), quotes.

## Decisions from brainstorming

- **No stock management.** A `disponible` product can be ordered in any quantity from 1 to 10 per
  line. When the artisan runs out, she switches the product to `rupture` by hand. No `stock`
  column, the data model stays as in the doc technique.
- **Payment and delivery are handled offline.** The confirmation page says: « Commande n°X reçue.
  Maison Guillard vous contacte sous 48 h pour le paiement et la livraison. » `adresse` is
  required, `telephone` is optional (as in the doc technique).
- **Only `disponible` products can be ordered.** `rupture` and `sur_commande` are rejected by the
  backend, even if a client sends them (the frontend never offers them in the first place).
- **The price always comes from the database.** The request only carries `produit_id` and
  `quantite`. The service reads `produit.prix` and copies it into `prix_unitaire_snapshot`, so a
  client cannot set its own price and the order keeps the price of the day if the artisan changes
  it later.
- **Email notification is an admin setting, off by default.** When on, two emails are sent: one to
  the artisan (new order, customer, lines, total) and a recap to the customer. Sending runs in a
  FastAPI `BackgroundTasks` after the response: an SMTP failure is logged and never fails the
  order. The setting is stored in the database (not in `.env`) so the artisan can change it
  herself once the back-office UI exists.
- **SMTP via `smtplib` (standard library), configured only through `.env`.** For now: Gmail SMTP
  with the developer's own address as both sender and artisan address, so real emails can be
  checked during manual tests. See "À adapter au déploiement".

## Backend

### Models (one Alembic migration)

- `commande`: `id` PK, `nom_client` str, `email` str, `telephone` str nullable, `adresse` str,
  `statut` enum `statut_commande_enum` (`en_attente` / `confirmee` / `expediee` / `livree` /
  `annulee`, default `en_attente`), `created_at`. Relationship `lignes` (selectin, cascade
  delete-orphan).
- `ligne_commande`: `id` PK, `commande_id` FK → `commande.id` `ondelete=CASCADE`, `produit_id` FK →
  `produit.id`, `quantite` int, `prix_unitaire_snapshot` Numeric(10, 2).
- `parametre`: single row, `id` PK, `email_commande_actif` bool, default `false`. The service
  creates the row on first read if it is missing.

### Schemas (`app/schemas/commande.py`, `app/schemas/parametre.py`)

- `LigneCommandeIn`: `produit_id` int, `quantite` int (1 ≤ q ≤ 10).
- `CommandeIn`: `nom_client` (non-empty), `email` (`EmailStr`), `telephone` optional, `adresse`
  (non-empty), `lignes` (at least 1, no duplicate `produit_id`). Invalid body → 422 (Pydantic).
  `EmailStr` needs the `email-validator` package: add it to `requirements.txt` (only new
  dependency of this block).
- `LigneCommandeOut`, `CommandeOut`: all columns, plus `total` computed from the lines.
- `ParametreOut` / `ParametreIn`: `email_commande_actif` bool.

### Services

- `commande_service.create(db, data) -> Commande`: for each line, load the product; missing →
  `ProduitIntrouvableError`, not `disponible` → `ProduitIndisponibleError` (both carry the
  `produit_id`). Builds the lines with the DB price, commits, returns the order.
- `parametre_service.get(db)` / `parametre_service.update(db, data)`.
- `email_service.notifier_nouvelle_commande(commande)`: builds both messages (artisan and
  customer) and sends them over SMTP with the `.env` settings. Catches and logs SMTP errors.

### Routes (Swagger tags « Commandes » and « Paramètres »)

| Method | Path | Auth | Input | Output |
|---|---|---|---|---|
| POST | `/api/commandes` | — | `CommandeIn` | 201 `CommandeOut` / 422 |
| GET | `/api/parametres` | admin | — | 200 `ParametreOut` / 401 |
| PUT | `/api/parametres` | admin | `ParametreIn` | 200 `ParametreOut` / 401 / 422 |

The router maps `ProduitIntrouvableError` and `ProduitIndisponibleError` to **422** with a French
`detail` naming the product (« Produit n°X introuvable », « Le produit « Nom » n'est plus
disponible »). After creating the order, if `email_commande_actif` is true, the router adds
`email_service.notifier_nouvelle_commande` to `BackgroundTasks`.

### Configuration (`backend/.env`, documented in `.env.example` without secrets)

`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_EXPEDITEUR`, `EMAIL_ARTISAN`.
Dev values: `smtp.gmail.com`, `587` (STARTTLS), the developer's Gmail address and a Gmail
**app password** (requires 2-step verification). `.env` is never committed.

## Frontend

### Cart state

- `utils/panier.js`: pure functions on a list of lines `{produit_id, nom, prix, photo, quantite}`:
  add (merges with an existing line, caps at 10), change quantity (clamped 1–10), remove, count,
  total. Tested with Vitest (`utils/panier.test.js`).
- `context/PanierContext.jsx`: holds the lines, exposes `ajouter(produit)`,
  `changerQuantite(id, q)`, `retirer(id)`, `vider()`, `nombreArticles`, `total`. Persisted in
  `localStorage`; reads and writes are wrapped in try/catch and fall back to an empty cart. `nom`,
  `prix` and `photo` are display-only, the backend recomputes the price.

### Changes to existing components

- `Header`: the disabled « Panier » button becomes a link to `/panier` with an item-count badge.
- `InfosProduit`: « Ajouter au panier » is enabled for `disponible` products; after a click, a
  short message « Ajouté au panier » with a link to the cart. The quote button stays disabled
  until the devis block.

### New pages and API

- `/panier` → `PagePanier` + `LigneArticlePanier` (photo, name, price, quantity 1–10, remove),
  total, « Passer commande » button. Empty cart → link to `/boutique`.
- `/commande` → `PageFormulaireCommande`: nom, email, téléphone (optional), adresse, cart summary.
  Basic client-side checks (required fields, email format). On submit, `POST /api/commandes`:
  - success → empty the cart, navigate to the confirmation with the order number in router state;
  - 422 → show the `detail` message, keep the cart so the visitor can fix it;
  - network error → message inviting to retry.
- `/commande/confirmation` → `PageConfirmationCommande`: order number and the 48 h message. Opened
  without router state → redirect to `/`.
- `api/client.js` gains `apiPost(path, body)`, which exposes the response `detail` on errors;
  `api/commandes.js` wraps `POST /commandes`.

## Testing

- **Unit (pytest):** `commande_service.create` uses the DB price (not anything from the client),
  rejects `rupture` and `sur_commande`, rejects an unknown product, computes the total.
- **Integration (pytest + TestClient):** `POST /api/commandes` → 201 with lines and total; 422 on
  empty lines, quantity 0 or 11, duplicate product, invalid email, unavailable product; parametres
  routes reject missing and forged tokens (same pattern as the existing admin-route tests); with
  `smtplib.SMTP` mocked, an order triggers an email only when `email_commande_actif` is true.
- **Frontend (Vitest):** `utils/panier.js`.
- **Manual:** full flow in the browser (add, change quantity, order, confirmation, cart emptied),
  unavailable-product error, then with the setting turned on in Swagger, check both emails arrive.

## Implementation order

Branch `Branche-S7`. Each step is tested before the next.

1. Models + migration (`commande`, `ligne_commande`, `parametre`).
2. `commande_service` + unit tests.
3. `POST /api/commandes` + integration tests.
4. `parametre_service` + admin routes + tests.
5. `email_service` + `BackgroundTasks` call + tests with mocked SMTP.
6. Front: `utils/panier.js` + Vitest, then `PanierContext`.
7. Front: `Header`, `InfosProduit`, `PagePanier`.
8. Front: `apiPost`, `PageFormulaireCommande`, `PageConfirmationCommande`.
9. Manual test of the full flow with a real email, then `docs/2026-10-XX-s7-resume.md`.

## À adapter au déploiement

The site will not be hosted on the development machine. Before going live, change only the
server's `.env` (no code change):

- **SMTP provider:** personal Gmail is for development only; use the host's SMTP or a
  transactional service (e.g. Brevo).
- **`EMAIL_ARTISAN`:** the artisan's real address (currently the developer's).
- **`EMAIL_EXPEDITEUR`:** preferably an address in the Maison Guillard name.
- **Email toggle:** moves into the admin UI with the back-office UI block; until then it is
  changed through Swagger (`PUT /api/parametres`).
