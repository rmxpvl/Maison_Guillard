# S9 — Back-office (essentiel) Implementation Plan

**Goal:** The artisan logs in, manages products and photos, follows orders and quote requests
(list, detail, status), and turns the emails on or off.

**Architecture:** Four admin routes are added to the API (list and status change for orders and
quotes); everything else the back-office needs already exists. The frontend gains an auth context
(token in sessionStorage), a guarded `/admin` area with its own bar, a tabbed dashboard and a
product form.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest; React, react-router-dom, `node:test`.

**Spec:** `docs/specs/2026-10-26-s9-back-office-design.md`

**Who types what:** Remy types the backend app code; tests and the frontend are written for him
and explained.

## Global Constraints

- Branch `Branche-S9` (from `main`). Conventional Commits, no trailers.
- Every new route is admin-only (`require_admin`) and is added to `ROUTES_ADMIN` in
  `tests/integration/test_securite_et_erreurs.py`.
- Lists are sorted newest first.
- No database migration: `nom_produit` is a Python property, not a column.

## Review Focus

- Expired token while using the back-office → logged out and sent to the login page, not stuck
  on errors (Task 3).
- Deleting a product that is in an order → the 409 message is shown, the product stays (Task 4).
- Status change on an order that was deleted meanwhile → 404 shown, list refreshed (Task 5).
- Typing `/admin/produits/abc` → « produit introuvable », not a crash (Task 4).
- Public pages still show their header/footer; admin pages never do (Task 3).

---

### Task 1: Orders — list and status (backend)

**Files:** modify `app/models/commande.py`, `app/schemas/commande.py`,
`app/services/commande_service.py`, `app/routers/commandes.py`; tests
`tests/unit/test_commande_service.py`, `tests/integration/test_commandes_admin.py`,
`tests/integration/test_securite_et_erreurs.py`.

- [ ] **Step 1: Tests**, run → fail (404 / `AttributeError`).
- [ ] **Step 2: `LigneCommande` (model) — add the property**

```python
    @property
    def nom_produit(self) -> str | None:
        return self.produit.nom if self.produit else None
```

- [ ] **Step 3: Schemas** — in `LigneCommandeOut` add `nom_produit: str | None = None`; add

```python
class StatutCommandeIn(BaseModel):
    statut: StatutCommande
```

- [ ] **Step 4: Service** — add to `commande_service.py`

```python
def get_all(db: Session, statut: StatutCommande | None = None) -> list[Commande]:
    query = db.query(Commande)
    if statut is not None:
        query = query.filter(Commande.statut == statut)
    return query.order_by(Commande.created_at.desc(), Commande.id.desc()).all()


def update_statut(db: Session, commande_id: int, statut: StatutCommande) -> Commande | None:
    commande = db.query(Commande).filter(Commande.id == commande_id).first()
    if commande is None:
        return None
    commande.statut = statut
    db.commit()
    db.refresh(commande)
    return commande
```
(import `StatutCommande` from `app.models.commande`).

- [ ] **Step 5: Routes** — add to `routers/commandes.py`

```python
@router.get(
    "",
    response_model=list[CommandeOut],
    summary="Lister les commandes (les plus récentes d'abord)",
    responses=NON_AUTORISE,
)
def list_commandes(
    statut: StatutCommande | None = None,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    return commande_service.get_all(db, statut)


@router.patch(
    "/{commande_id}/statut",
    response_model=CommandeOut,
    summary="Changer le statut d'une commande",
    responses={**NON_AUTORISE, 404: {"description": "Commande introuvable"}},
)
def update_statut_commande(
    commande_id: int,
    payload: StatutCommandeIn,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    commande = commande_service.update_statut(db, commande_id, payload.statut)
    if commande is None:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    return commande
```
(imports: `require_admin`, `NON_AUTORISE`, `StatutCommande`, `StatutCommandeIn`).

- [ ] **Step 6: Run** → all pass. **Commit** `feat: add admin order list and status change`.

---

### Task 2: Quotes — list and status (backend)

Same as Task 1 for quotes: `Devis.nom_produit` property, `DevisOut.nom_produit`,
`StatutDevisIn`, `devis_service.get_all` / `update_statut`, `GET /api/devis` and
`PATCH /api/devis/{devis_id}/statut` (404 « Devis introuvable »). Tests in
`tests/unit/test_devis_service.py` and `tests/integration/test_devis_admin.py`; two entries added
to `ROUTES_ADMIN`. **Commit** `feat: add admin quote list and status change`.

---

### Task 3: Frontend — authentication and admin shell

- [ ] `api/client.js`: `apiRequete(path, { method, body, token, formulaire })` (JSON or
  `FormData`, `Authorization` header, `ApiError` with `detail`, 204 → `null`).
- [ ] `context/authContexte.js`, `context/AuthContext.jsx` (`AuthProvider`), `hooks/useAuth.js`:
  token in sessionStorage (try/catch), `connexion`, `deconnexion`, `appel` (logs out on 401).
- [ ] `PageConnexionAdmin` (`/admin/connexion`), `RouteAdmin` (redirects without token),
  `BarreAdmin`; `Header`/`Footer` return `null` on `/admin` paths.
- [ ] `PageAdmin` (`/admin`): email toggle + tabs in `?onglet=`; tab contents filled by Tasks 4–5.
- [ ] `utils/admin.js` + tests: status labels for orders and quotes, `formatDate`.
- [ ] lint/build/tests clean. **Commit** `feat: add admin login and dashboard shell`.

### Task 4: Frontend — products

- [ ] `OngletProduits`: table, « Nouveau produit », « Modifier », « Supprimer » (confirm; 409
  message shown).
- [ ] `PageProduitAdmin` (`/admin/produits/nouveau`, `/admin/produits/:id`): form, then photo
  section in edit mode (upload, set main, delete). Unknown id → « Produit introuvable ».
- [ ] `utils/admin.js`: `formulaireDepuisProduit`, `produitPourApi` (+ tests).
- [ ] **Commit** `feat: add product management to the back-office`.

### Task 5: Frontend — orders and quotes

- [ ] `OngletCommandes`, `OngletDevis`: tables, detail panel, status `<select>` (PATCH, then
  refresh; error message on failure).
- [ ] **Commit** `feat: add order and quote follow-up to the back-office`.

### Task 6: Manual check, docs, PR

- [ ] Full walkthrough: login, wrong password, create/edit/delete a product, photo upload, order and
  quote status changes, email toggle, logout, expired/forged token.
- [ ] `docs/tests-api.md` section 19, `docs/outils.html` (sessionStorage), S9 summary.
- [ ] Push, PR to `main`.
