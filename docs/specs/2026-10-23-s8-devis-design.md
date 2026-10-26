# S8 — Demande de devis (version de base) — Design

> Base: `docs/specs/2026-09-14-maison-guillard-mvp-design.md` and the doc technique
> (`Documentation/Maison-Guillard-Doc-Technique.pdf`: table `devis`, endpoint `POST /devis`,
> `devis_service`). S7 (achat direct) is on `Branche-S7`, PR #6, not merged yet: this branch starts
> from it.

## Context and scope

Third of the remaining blocks (site public → achat direct → **devis** → back-office UI →
back-office commandes et devis). A visitor describes a project (custom piece, catalogue model to
adapt, sold piece to make again). The request is stored with status `nouveau`; the artisan follows
up later from the back-office.

**Deliberately basic, built to be extended later** (budget, delays, photos, dimensions…): new
fields are a column, a schema field and a form input, with no change of structure.

**Out of scope here:** `GET /api/devis` and `PATCH /api/devis/{id}/statut` (back-office devis
block), file uploads, a separate quote page.

## Decisions

- **Same data model as the doc technique.** `devis`: `id`, `nom_client`, `email`, `telephone`
  (nullable), `produit_id` (nullable FK → `produit.id`), `description_projet`, `statut` enum
  `statut_devis_enum` (`nouveau` / `en_discussion` / `accepte` / `refuse`, default `nouveau`),
  `created_at`.
- **Any disponibilité is accepted** for `produit_id`: quoting a `sur_commande`, `rupture` or
  `disponible` piece is the point of a quote. An unknown `produit_id` → 422.
- **Deleting a product referenced by a quote** keeps the quote: `produit_id` uses
  `ondelete="SET NULL"` (the description still says what the client wanted). Unlike order lines,
  a quote does not need the product to exist.
- **Emails reuse the existing setting** `parametre.email_commande_actif` (no new setting): when on,
  the artisan gets « Nouvelle demande de devis n°X » and the client an acknowledgement. Same
  `email_service` helpers, same background task, same rule: an SMTP failure never fails the
  request.
- **The form lives on the Contact page.** The three disabled buttons of the product page
  (« Demander un devis », « Personnaliser ce modèle », « Demander un modèle similaire ») become
  links to `/contact?produit=<id>`; the form then shows « À propos de : <nom> » and sends the
  `produit_id`.

## Backend

- Model `app/models/devis.py` (`Devis`, `StatutDevis`) + Alembic migration (dev and test
  databases; `downgrade` also drops `statut_devis_enum`).
- Schemas `app/schemas/devis.py`:
  - `DevisIn`: `nom_client` (1–100), `email` (`EmailStr`), `telephone` (optional, ≤ 30),
    `produit_id` (optional int), `description_projet` (10–2000); whitespace stripped.
  - `DevisOut`: all columns.
- Service `app/services/devis_service.py`: `create(db, data) -> Devis`; unknown `produit_id` →
  `ProduitIntrouvableError` (reuses the one in `commande_service`).
- Route `POST /api/devis` (tag « Devis »): 201 `DevisOut` / 422. If the email setting is on,
  `email_service.messages_nouveau_devis(devis)` is sent in a background task.

## Frontend

- `api/devis.js`: `creerDevis(demande)` via `apiPost`.
- `components/FormulaireDevis.jsx` on `PageContact`: nom, e-mail, téléphone (facultatif),
  description; reads `?produit=` from the URL, loads the product name to show « À propos de »;
  on success shows « Demande n°X envoyée. Maison Guillard vous répond sous 48 h. » and clears the
  form; errors as in the order form (API `detail`, generic 422 message, network message).
- `utils/produit.js`: the three quote actions get `code: 'devis'`; `InfosProduit` renders them as
  links to `/contact?produit=<id>`.

## Testing

- Unit: schema (valid without phone/product; refuses short description, invalid email, blank
  name), service (stores the request, unknown product refused, any disponibilité accepted).
- Integration: `POST /api/devis` 201 with and without product, 422 unknown product / invalid body,
  quote kept with `produit_id = NULL` after its product is deleted, emails sent only when the
  setting is on, SMTP failure still 201.
- Manual: send a quote from a product page and from the Contact page, check the emails.
