# Maison Guillard v2 — Lot 1 : catalogue — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the shop into three fixed univers (Meubles, Céramique, Papeterie) with admin-managed categories and finishes (teintes), replace `disponibilite` by `visible`, fix bugs B22–B24 and B28.

**Architecture:** Same layers as today (router → schema → service → model). `univers` is a PostgreSQL enum column on `categorie`; `teinte` + `produit_teinte` are new tables; public product routes only return visible products, two new admin routes return everything. Frontend: `/boutique` becomes a three-tile landing page, `/boutique/:univers[/:categorie]` the listing; two new back-office tabs. The cart keeps working (every visible product can be added) until lot 2 turns it into « Ma demande ».

**Tech Stack:** FastAPI 0.115, SQLAlchemy 2, Alembic, Pydantic 2, pytest + TestClient; React 19, React Router 7, Vite, `node --test`.

**Spec:** `docs/specs/2026-11-08-v2-boutique-sur-commande-design.md` (§4.1, §4.2, §5.2–5.4, §5.9, §6.1 `categorie`/`produit`/`teinte`/`produit_teinte`). Mockups: `docs/specs/maquettes-v2/boutique-univers.html` (option C), `fiche-produit-teintes.html` (left half only in this lot).

**Branch:** `Branche-v2-lot1-catalogue` from `main`; one PR to `main` at the end.

## Global Constraints

- Commits: Conventional Commits, English, **no Co-Authored-By / Claude trailers**.
- Domain names in French (`univers`, `teinte`, `visible`), code comments in English, user-facing text in French.
- Univers codes, exactly: `meubles`, `ceramique`, `papeterie`; labels: « Meubles », « Céramique », « Papeterie ». Fixed, not editable from the back-office.
- Category slug pattern: `^[a-z0-9-]+$`, unique site-wide.
- Product price: `prix > 0`; product name: non-blank after stripping spaces.
- Price display everywhere on the public site: « À partir de X € ».
- Fiche produit copy, exactly: « Le prix final peut varier selon la finition et vos souhaits ; il est confirmé dans votre devis. » and « Fabriqué à la commande · Fabrication et livraison garanties sous 15 jours après paiement ».
- Every new migration has a working `downgrade()` that also drops the enum types it created.
- Backend tests: `cd backend; .\.venv\Scripts\python.exe -m pytest -q` (Docker must be up). Frontend: `cd frontend; npm test`, `npm run lint`, `npm run build`.
- Apply each migration to dev **and** test DBs: `alembic upgrade head` then `$env:DATABASE_URL=$env:TEST_DATABASE_URL; alembic upgrade head` (read `TEST_DATABASE_URL` from `backend/.env`).

## Review Focus

1. A hidden product reached by its URL (`/produits/<id>`) or still in a visitor's cart: public detail → 404, `POST /api/commandes` → 422 « « X » n'est plus disponible ». Tests in Task 4.
2. Moving a category to another univers or renaming its slug while products use it: products follow, old URL `/boutique/<univers>/<ancien-slug>` shows the 404 page, nothing crashes. Test in Task 3 (`PUT` keeps products attached).
3. Deleting a teinte that a product offers → 409 with « Teinte proposée par des produits : désactivez-la » ; an inactive teinte stays on the admin product form but never shows on the public fiche. Tests in Task 5 and Task 7.
4. A product created with `teinte_ids` containing an unknown id → 422 « Teinte introuvable », nothing half-saved. Test in Task 5.
5. Univers with no visible product (true for Céramique/Papeterie on a fresh DB without seed) → page shows « Bientôt disponible », not an empty grid or an error. Test in Task 7 (`messageUniversVide`).

---

### Task 1: B28 — show/hide password on admin login

**Files:**
- Modify: `frontend/src/pages/admin/PageConnexionAdmin.jsx`
- Modify: `frontend/src/index.css` (append)

**Interfaces:** Produces nothing other tasks use.

- [ ] **Step 1:** In `PageConnexionAdmin.jsx` add `const [visible, setVisible] = useState(false)`; the password `<input>` gets `type={visible ? 'text' : 'password'}`; right after it a `<button type="button" className="champ-mdp__bouton" aria-pressed={visible} onClick={() => setVisible((v) => !v)}>{visible ? 'Masquer' : 'Afficher'}</button>`; wrap input + button in `<span className="champ-mdp">`.
- [ ] **Step 2:** Append to `index.css`: `input::-ms-reveal, input::-ms-clear { display: none; }`, plus `.champ-mdp` (relative, flex, input grows) and `.champ-mdp__bouton` (small uppercase text button in the site's black/white style).
- [ ] **Step 3:** Run `npm run lint` and `npm run build` → both succeed.
- [ ] **Step 4: Manual check** in Edge at `http://localhost:5173/admin/connexion`: type, click outside, click back in: the « Afficher » button is still there and toggles; Edge's own eye icon never appears.
- [ ] **Step 5: Commit** `fix: add a show/hide password button on admin login (B28)`

---

### Task 2: Validation of produit and categorie input (B22, B23, B24)

**Files:**
- Modify: `backend/app/schemas/produit.py`, `backend/app/schemas/categorie.py`
- Test: `backend/tests/unit/test_produit_schema.py` (create), `backend/tests/unit/test_categorie_schema.py` (create)

**Interfaces:**
- Produces: `ProduitCreate`/`ProduitUpdate` with `model_config = ConfigDict(str_strip_whitespace=True)`, `nom: str = Field(min_length=1, max_length=120)`, `prix: Decimal = Field(gt=0, max_digits=10, decimal_places=2)` (Optional in Update); `CategorieCreate` with `nom: str = Field(min_length=1, max_length=60)`, `slug: str = Field(pattern=r"^[a-z0-9-]+$", max_length=60)`. Also replace the deprecated `class Config` by `model_config = ConfigDict(from_attributes=True)` in both `Out` schemas.

- [ ] **Step 1: Write the failing tests**

```python
# test_produit_schema.py
VALIDE = {"nom": "Table", "description": "Chêne", "categorie_id": 1, "prix": "120.00", "dimensions": "80x80", "disponibilite": "disponible"}

@pytest.mark.parametrize("champ, valeur", [("prix", "0"), ("prix", "-5"), ("nom", ""), ("nom", "   ")])
def test_produit_create_refuse(champ, valeur):
    with pytest.raises(ValidationError):
        ProduitCreate(**{**VALIDE, champ: valeur})

def test_produit_update_refuse_un_prix_negatif():
    with pytest.raises(ValidationError):
        ProduitUpdate(prix="-1")

def test_produit_create_retire_les_espaces_du_nom():
    assert ProduitCreate(**{**VALIDE, "nom": "  Table  "}).nom == "Table"

# test_categorie_schema.py
@pytest.mark.parametrize("slug", ["Test", "test qa", "té", ""])
def test_categorie_create_refuse_un_slug_invalide(slug):
    with pytest.raises(ValidationError):
        CategorieCreate(nom="Test", slug=slug)

def test_categorie_create_accepte_un_slug_valide():
    assert CategorieCreate(nom="Bols", slug="bols-2").slug == "bols-2"
```

(`disponibilite` disappears from `VALIDE` in Task 4.)

- [ ] **Step 2:** Run `pytest tests/unit/test_produit_schema.py tests/unit/test_categorie_schema.py -v` → FAIL (no validation yet).
- [ ] **Step 3:** Add the `Field` constraints listed in Interfaces.
- [ ] **Step 4:** Run the two files → PASS; run the full backend suite → all pass.
- [ ] **Step 5: Commit** `fix: validate produit price and name and categorie slug (B22-B24)`

---

### Task 3: Univers on categories, category update route, filter products by univers

**Files:**
- Modify: `backend/app/models/categorie.py`, `backend/app/models/__init__.py`, `backend/app/schemas/categorie.py`, `backend/app/services/categorie_service.py`, `backend/app/services/produit_service.py`, `backend/app/routers/categories.py`, `backend/app/routers/produits.py`, `backend/app/main.py` (tag description), every test that builds a `Categorie(...)` (add `univers=Univers.meubles`)
- Create: migration `backend/alembic/versions/<rev>_add_univers_to_categorie.py`
- Test: `backend/tests/unit/test_categorie_service.py`, `backend/tests/integration/test_categories_routes.py`, `backend/tests/integration/test_produits_routes.py`, `backend/tests/integration/test_securite_et_erreurs.py`

**Interfaces:**
- Produces: `class Univers(str, enum.Enum)` in `app/models/categorie.py` with `meubles`, `ceramique`, `papeterie`, exported from `app.models`; column `Categorie.univers = Column(SqlEnum(Univers, name="univers_enum"), nullable=False)`.
- `CategorieCreate(nom, slug, univers: Univers)`, `CategorieUpdate(nom: str | None, slug: str | None, univers: Univers | None)` (same constraints as Create), `CategorieOut(id, nom, slug, univers)`.
- `categorie_service.update(db, categorie_id: int, data: dict) -> Categorie | None` (sets non-None fields; `SlugDejaUtiliseError` on duplicate slug).
- `PUT /api/categories/{categorie_id}` 🔒 → 200 `CategorieOut` / 404 « Catégorie introuvable » / 409 « Slug déjà utilisé » / 422.
- `produit_service.get_all(db, categorie_id=None, univers: Univers | None = None, …)`: `univers` filters through a join on `Categorie`. `GET /api/produits?univers=` (422 for an unknown value).

- [ ] **Step 1: Write the failing tests**
  - unit `test_update_change_les_champs_envoyes` (mock db, only `nom` sent → `univers` unchanged) and `test_update_leve_slug_deja_utilise_et_annule` (commit raises `IntegrityError` → `SlugDejaUtiliseError`, `rollback` called).
  - integration: `test_create_categorie_enregistre_son_univers` (POST `{"nom":"Bols","slug":"bols","univers":"ceramique"}` → 201, body `univers == "ceramique"`); `test_create_categorie_refuse_un_univers_inconnu` (→ 422); `test_update_categorie_change_d_univers_et_garde_ses_produits` (category with one produit, PUT `{"univers":"papeterie","slug":"carnets"}` → 200, produit still has `categorie_id` of that category); `test_update_categorie_404`; `test_update_categorie_409_slug_pris`; `test_list_produits_filtre_par_univers` (one produit in a `meubles` category, one in `ceramique`; `?univers=ceramique` returns only the second); `test_list_produits_422_pour_un_univers_inconnu`.
  - add `("put", "/api/categories/1")` to `ROUTES_ADMIN`.
- [ ] **Step 2:** Run them → FAIL.
- [ ] **Step 3:** Model + enum. Migration (hand-checked after `alembic revision --autogenerate -m "add univers to categorie"`): create `univers_enum`, add column with `server_default='meubles'` so existing rows are valid, then `alter_column(..., server_default=None)`; `downgrade` drops the column and the type.
- [ ] **Step 4:** Schemas, `categorie_service.update`, the `PUT` route (same error style as `create_categorie`), `univers` filter in `produit_service.get_all` and `list_produits`. Add `univers=Univers.meubles` to every `Categorie(...)` built in tests and in `seed_catalogue.py` (all four current categories → `meubles`), `"univers": "meubles"` to every `POST /api/categories` JSON body in tests, and `univers="meubles"` to the `CategorieCreate(...)` calls of `test_categorie_schema.py` (Task 2).
- [ ] **Step 5:** Apply the migration to dev and test DBs; check `alembic downgrade -1` then `upgrade head` on the dev DB; run the full suite → PASS.
- [ ] **Step 6: Commit** `feat: add univers to categories, category update route and univers filter`

---

### Task 4: `visible` replaces `disponibilite`

**Files:**
- Modify: `backend/app/models/produit.py`, `backend/app/models/__init__.py`, `backend/app/schemas/produit.py`, `backend/app/services/produit_service.py`, `backend/app/services/commande_service.py`, `backend/app/services/devis_service.py` (comment), `backend/app/routers/produits.py`, `backend/app/routers/commandes.py` (Swagger text), `backend/seed_catalogue.py`, every test listed by `grep -rln disponibilite backend/tests`
- Create: migration `<rev>_replace_disponibilite_with_visible.py`
- Test: `backend/tests/integration/test_produits_routes.py`, `backend/tests/unit/test_commande_service.py`, `backend/tests/integration/test_commandes_routes.py`, `backend/tests/integration/test_seed_catalogue.py`

**Interfaces:**
- Produces: `Produit.visible = Column(Boolean, nullable=False, default=True, server_default=true())`; `Disponibilite` is deleted.
- `ProduitCreate.visible: bool = True`, `ProduitUpdate.visible: bool | None`, `ProduitOut.visible: bool`.
- `produit_service.get_all(db, categorie_id=None, univers=None, visibles_seulement: bool = True)`; `produit_service.get_visible(db, produit_id) -> Produit | None` (None when hidden).
- Public `GET /api/produits` and `GET /api/produits/{id}` only see visible products (hidden → 404 « Produit introuvable »).
- 🔒 `GET /api/produits/admin` (all products, same filters) and 🔒 `GET /api/produits/admin/{produit_id}` (any product, 404 if absent). Declare both **before** `/{produit_id}`.
- `commande_service.ProduitIndisponibleError` is now raised when `not produit.visible`; message unchanged.
- The 409 detail on product deletion becomes « Produit présent dans des commandes : masquez-le plutôt que de le supprimer ».

- [ ] **Step 1: Write the failing tests**
  - `test_list_produits_public_cache_les_produits_masques` (one visible, one hidden → public list has 1, `/admin` list with token has 2); `test_get_produit_masque_404_en_public_200_en_admin`; `test_update_produit_peut_masquer` (PUT `{"visible": false}` → 200, `visible` false); `test_post_commande_refuse_un_produit_masque` (→ 422 « « Tabouret » n'est plus disponible »); unit `test_create_refuse_un_produit_masque`.
  - Replace `test_list_produits_returns_422_for_unknown_disponibilite` / `..._filters_by_disponibilite` / `test_create_refuse_un_produit_non_disponible` / the devis « quelle que soit sa disponibilité » test by their `visible` equivalents or delete them when meaningless; `test_seed_catalogue_covers_every_disponibilite` becomes `test_seed_catalogue_tous_les_produits_sont_visibles`.
  - Add `("get", "/api/produits/admin")`, `("get", "/api/produits/admin/1")` to `ROUTES_ADMIN`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Migration: add `visible` (server default true), drop `disponibilite`, drop type `disponibilite_enum`; `downgrade` recreates the type and the column with `server_default='disponible'`, then drops `visible`.
- [ ] **Step 4:** Model, schemas, service, routes, commande check, seed (drop the disponibilité element of each `PRODUITS` tuple), all test fixtures (`grep -rn Disponibilite backend` must return nothing).
- [ ] **Step 5:** Apply migration to both DBs, downgrade/upgrade check, full suite → PASS.
- [ ] **Step 6: Commit** `feat: replace product availability with a visible flag and add admin product routes`

---

### Task 5: Teintes (finishes) — backend

**Files:**
- Create: `backend/app/models/teinte.py`, `backend/app/schemas/teinte.py`, `backend/app/services/teinte_service.py`, `backend/app/routers/teintes.py`, migration `<rev>_add_teinte_tables.py`
- Modify: `backend/app/models/__init__.py`, `backend/app/models/produit.py`, `backend/app/schemas/produit.py`, `backend/app/services/produit_service.py`, `backend/app/routers/produits.py`, `backend/app/routers/reponses.py`, `backend/app/main.py` (router + tag « Teintes »)
- Test: `backend/tests/unit/test_teinte_service.py`, `backend/tests/integration/test_teintes_routes.py`, `backend/tests/integration/test_produits_routes.py`, `test_securite_et_erreurs.py`

**Interfaces:**
- Produces: `Teinte(id, nom: String not null, image_url: String not null, ordre: Integer default 0, active: Boolean default true)`; association table `produit_teinte(produit_id FK produit.id ON DELETE CASCADE, teinte_id FK teinte.id ON DELETE RESTRICT, PK(produit_id, teinte_id))`; `Produit.teintes = relationship("Teinte", secondary=produit_teinte, order_by="Teinte.ordre", lazy="selectin")`.
- `TeinteOut(id, nom, image_url, ordre, active)`, `TeinteUpdate(nom: str | None (1–40, stripped), ordre: int | None (≥ 0), active: bool | None)`.
- `ProduitCreate.teinte_ids: list[int] = []`, `ProduitUpdate.teinte_ids: list[int] | None` (None = unchanged, `[]` = none), `ProduitOut.teintes: list[TeinteOut]` (all linked teintes, active or not; the public front filters).
- `teinte_service`: `get_all(db) -> list[Teinte]` (by `ordre`, then `id`); `create(db, nom: str, ordre: int, image_url: str) -> Teinte`; `update(db, teinte_id, data: dict) -> Teinte | None`; `replace_image(db, teinte_id, image_url) -> Teinte | None`; `delete(db, teinte_id) -> bool`, raises `TeinteUtiliseeError` when a product offers it; `get_many(db, ids: list[int]) -> list[Teinte]`, raises `TeinteIntrouvableError` if any id is missing.
- `produit_service.create/update` pop `teinte_ids` from `data` before the generic field loop, resolve it through `teinte_service.get_many` and assign `produit.teintes` before committing (unknown id → `TeinteIntrouvableError`, nothing saved; in `update`, `None` leaves the teintes untouched, `[]` clears them).
- Routes (all 🔒, prefix `/api/teintes`): `GET ""` → list; `POST ""` multipart (`nom: Form`, `ordre: Form = 0`, `fichier: File`) → 201, image stored with `photo_service.upload_to_cloudinary`; `PUT "/{teinte_id}"` JSON `TeinteUpdate` → 200/404; `POST "/{teinte_id}/image"` multipart `fichier` → 200/404; `DELETE "/{teinte_id}"` → 204/404/409 « Teinte proposée par des produits : désactivez-la ». Product routes: `TeinteIntrouvableError` → 422 « Teinte introuvable ».

- [ ] **Step 1: Write the failing tests**
  - unit: `test_delete_refuse_une_teinte_utilisee`, `test_get_many_leve_si_un_id_manque`, `test_update_change_les_champs_envoyes`.
  - integration: `test_create_teinte_avec_image` (PNG bytes upload → 201, `image_url` under `/uploads/`, `active` true); `test_list_teintes_triees_par_ordre`; `test_update_teinte_desactive`; `test_replace_image_teinte`; `test_delete_teinte_libre_204`; `test_delete_teinte_proposee_409`; `test_create_produit_avec_teintes` (→ `teintes` ids in order of `ordre`); `test_update_produit_teinte_ids_vide_retire_tout`; `test_create_produit_teinte_inconnue_422_et_rien_n_est_cree` (product count unchanged).
  - Each new integration file's `clean_db` deletes `Produit`, `Teinte`, `Categorie`, `Admin` in that order.
  - Add the five teinte routes to `ROUTES_ADMIN`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Model, migration (two tables; `downgrade` drops both), schemas, service, router, produit wiring.
- [ ] **Step 4:** Apply to both DBs, downgrade/upgrade check, full suite → PASS.
- [ ] **Step 5: Commit** `feat: add teintes with images and link them to produits`

---

### Task 6: Demo seed for the three univers and the teintes

**Files:**
- Modify: `backend/seed_catalogue.py`, `backend/tests/integration/test_seed_catalogue.py`
- Create: `backend/seed_photos/teintes/{naturel,charcoal,hazelnut,bourbon,vienna}.svg` (flat 200×200 squares; colours from the mockup: `#d9c4a3`, `#3b3836`, `#8a6747`, `#6b3b22`, `#a8845c`)

**Interfaces:**
- Consumes: `Univers`, `Teinte`, `Produit.teintes`, `Produit.visible` (Tasks 3–5).
- Produces: `CATEGORIES` as `(nom, slug, univers)`: the four current ones in `meubles`, plus `("Vases", "vases", ceramique)`, `("Bols et tasses", "bols-et-tasses", ceramique)`, `("Carnets", "carnets", papeterie)`, `("Cartes", "cartes", papeterie)`; 2 demo products per new category (invented names/prices, plausible dimensions); `TEINTES` = the five above in that order; every wooden product (`meubles`) offers all five teintes, others none; `seed_teintes(db, upload_dir)` copies the SVGs like `seed_photos` does and is idempotent (by `nom`).

- [ ] **Step 1: Write the failing tests:** `test_seed_catalogue_couvre_les_trois_univers`, `test_seed_teintes_cree_cinq_teintes_une_seule_fois` (run twice → 5), `test_seed_les_meubles_proposent_les_teintes` (a `meubles` product has 5 teintes, a `ceramique` one 0).
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement; `__main__` calls `seed_catalogue`, `seed_teintes`, `seed_photos`. **Step 4:** Full suite → PASS; run `python seed_catalogue.py` on dev DB → « Catalogue de démonstration en place. »
- [ ] **Step 5: Commit** `feat: seed demo categories for the three univers and five teintes`

---

### Task 7: Public shop — univers landing page and listing

**Files:**
- Create: `frontend/src/utils/univers.js`, `frontend/src/utils/univers.test.js`, `frontend/src/pages/PageBoutique.jsx`, `frontend/src/pages/PageUnivers.jsx`
- Modify: `frontend/src/main.jsx`, `frontend/src/api/produits.js`, `frontend/src/utils/produit.js`, `frontend/src/utils/produit.test.js`, `frontend/src/components/FiltreCategorie.jsx`, `frontend/src/components/CarteProduit.jsx`, `frontend/src/pages/PageAccueil.jsx`, `frontend/src/index.css`, `frontend/package.json` (add `src/utils/univers.test.js` to `test`)
- Delete: `frontend/src/pages/PageCatalogue.jsx`, `frontend/src/components/FiltreDisponibilite.jsx`, `frontend/src/components/MentionDisponibilite.jsx`

**Interfaces:**
- Produces in `utils/univers.js`: `UNIVERS = [{ code: 'meubles', nom: 'Meubles', image }, { code: 'ceramique', nom: 'Céramique', image }, { code: 'papeterie', nom: 'Papeterie', image }]` (images: existing `assets/vitrine/matiere.webp`, `detail.webp`, `univers.webp`, provisional); `universParCode(code) -> objet | null`; `categoriesDeLUnivers(categories, code) -> categories filtered`; `messageUniversVide = 'Bientôt disponible : les pièces de cet univers arrivent.'`.
- `utils/produit.js`: delete `DISPONIBILITES`, `libelleDisponibilite`, `disponibiliteValide`, `actionsFiche`, the ranking in `piecesChoisies` (now: produits with photos, API order, first n); `prixAffiche(produit)` always returns `À partir de ${formatPrix(produit.prix)}`; add `teintesVisibles(produit) -> produit.teintes filtered on active, sorted by ordre`.
- `getProduits({ univers = null, categorie = null } = {})`.
- Routes: `boutique` → `PageBoutique`; `boutique/:univers` and `boutique/:univers/:categorie` → `PageUnivers` (unknown univers, or a category slug not in that univers → `PageIntrouvable`).

- [ ] **Step 1: Write the failing tests** (`node:test`): `universParCode` known/unknown; `categoriesDeLUnivers` keeps only matching `univers`; `prixAffiche` always prefixes « À partir de »; `teintesVisibles` drops inactive and sorts by `ordre`; `piecesChoisies` keeps produits with photos in API order, at most n. Remove the tests of deleted functions.
- [ ] **Step 2:** `npm test` → FAIL.
- [ ] **Step 3:** Implement utils, API param, `PageBoutique` (three large tiles as in the option C mockup: image, univers name in uppercase over a dark gradient, link to `/boutique/<code>`), `PageUnivers` (title = univers name, `FiltreCategorie` with « Tout » + that univers' categories linking to `/boutique/<univers>/<slug>`, grid via `avecPhotosDabord`, `EtatChargement` with `messageVide={messageUniversVide}`), remove availability mentions from `CarteProduit`, update `PageAccueil`. Header « Boutique » link unchanged.
- [ ] **Step 4:** `npm test`, `npm run lint`, `npm run build` → pass. Manual check with backend running: `/boutique` shows 3 tiles; `/boutique/ceramique` lists the seeded vases and bowls; `/boutique/meubles/tabourets` filters; `/boutique/jardin` → 404 page; a hidden product disappears from the grid.
- [ ] **Step 5: Commit** `feat: add univers landing page and per-univers shop listing`

---

### Task 8: Fiche produit — finishes and made-to-order copy

**Files:**
- Create: `frontend/src/components/ChoixTeinte.jsx`
- Modify: `frontend/src/components/InfosProduit.jsx`, `frontend/src/index.css`

**Interfaces:**
- Consumes: `teintesVisibles`, `prixAffiche` (Task 7).
- Produces: `<ChoixTeinte teintes={[...]} valeur={id|null} onChange={(id) => …} />` — a radiogroup of square images (40 px, name under each, selected = 2 px black outline offset 2 px), keyboard-accessible (`role="radiogroup"`, each item `role="radio"` + `aria-checked`). Renders nothing for an empty list. Lot 2 reads `valeur` to put the teinte in « Ma demande ».

- [ ] **Step 1:** `InfosProduit`: price via `prixAffiche`; `ChoixTeinte` under the description with local state, default = the teinte named « Naturel » if present, else none; under it the exact « Le prix final peut varier… » sentence (only when the product has teintes); one primary button « Ajouter au panier » (existing cart call, for every visible product) and one secondary link « Une question ? Contactez l'atelier » to `/contact?produit=<id>`; under the actions the exact « Fabriqué à la commande · … » line. Remove the availability-based actions and notes.
- [ ] **Step 2:** `npm test`, `npm run lint`, `npm run build` → pass.
- [ ] **Step 3: Manual check:** fiche of « Tabouret Trapèze » shows 5 swatches with Naturel selected, arrows/space change the selection; a ceramic product shows no swatch and no price-variation sentence; an inactive teinte (deactivate one via Swagger) disappears.
- [ ] **Step 4: Commit** `feat: show finishes and made-to-order notes on the product page`

---

### Task 9: Back-office — categories tab, teintes tab, product form

**Files:**
- Create: `frontend/src/components/admin/OngletCategories.jsx`, `frontend/src/components/admin/OngletTeintes.jsx`
- Modify: `frontend/src/pages/admin/PageAdmin.jsx`, `frontend/src/components/admin/FormulaireProduit.jsx`, `frontend/src/components/admin/OngletProduits.jsx`, `frontend/src/pages/admin/PageProduitAdmin.jsx`, `frontend/src/utils/admin.js`, `frontend/src/utils/admin.test.js`, `frontend/src/utils/erreurs.test.js` (if it references availability)

**Interfaces:**
- Consumes: admin routes from Tasks 3–5 through `useAuth().appel(path, options)`; `UNIVERS` (Task 7).
- Produces in `utils/admin.js`: `PRODUIT_VIDE` with `visible: true, teinte_ids: []` instead of `disponibilite`; `formulaireDepuisProduit` maps `teintes` → `teinte_ids` (ids as numbers) and `visible`; `produitPourApi` sends `visible` (bool) and `teinte_ids` (numbers); `slugDepuisNom(nom) -> string` (lowercase, accents removed with `normalize('NFD')`, non `[a-z0-9]` runs → `-`, trimmed of `-`), e.g. `slugDepuisNom('Bols & Tasses') === 'bols-tasses'`, `slugDepuisNom('Céramique') === 'ceramique'`.
- `ONGLETS` in `PageAdmin`: produits, categories (« Catégories »), teintes (« Teintes »), commandes, devis.

- [ ] **Step 1: Write the failing tests** for `slugDepuisNom` (the two examples + `'  Été 2026 '` → `'ete-2026'`) and the updated `formulaireDepuisProduit`/`produitPourApi` (`visible`, `teinte_ids`).
- [ ] **Step 2:** `npm test` → FAIL. **Step 3:** Implement utils.
- [ ] **Step 4:** `OngletCategories`: one section per univers listing its categories (nom, slug); a creation form (nom, univers select, slug pre-filled with `slugDepuisNom(nom)` until edited by hand); per row « Modifier » (inline nom/slug/univers, `PUT`) and « Supprimer » (confirm; 409 message shown via `messageErreurApi`).
- [ ] **Step 5:** `OngletTeintes`: table (image 40 px, nom, ordre, active toggle, « Changer l'image », « Supprimer »); creation form (nom, ordre, image file) using `formulaire` multipart; 409 message shown.
- [ ] **Step 6:** `FormulaireProduit`: remove the availability select; add a « Visible sur le site » checkbox and a « Finitions proposées » checkbox list of all teintes (loaded with `GET /api/teintes`; inactive ones shown with « (désactivée) »). Price label « Prix à partir de (€) ». `OngletProduits` lists via `GET /api/produits/admin`, column « Visible » (Oui/Non); `PageProduitAdmin` loads via `/produits/admin/<id>`.
- [ ] **Step 7:** `npm test`, `npm run lint`, `npm run build` → pass. Manual check: create a category « Bols » in Céramique (slug `bols`), rename it, move it; create a teinte with an image, deactivate it; edit a product: hide it, tick two teintes, save, reopen → state kept; delete a teinte that a product offers → 409 message.
- [ ] **Step 8: Commit** `feat: manage categories and teintes from the back-office`

---

### Task 10: Docs, full verification, PR

**Files:**
- Modify: `README.md` (features, DB diagram: `categorie.univers`, `produit.visible`, `teinte`, `produit_teinte`; API table: new routes), `docs/bugs.md` (B22, B23, B24, B28 → corrected with their commits; counts updated), `docs/tests-api.md` (new section « 20. Catalogue v2 » with the manual checks of Tasks 3–5, PASS/FAIL as observed), `docs/evolutions-futures.md` (items 4–6 and 8–9 marked done)

- [ ] **Step 1:** Update the docs from what was actually built.
- [ ] **Step 2:** Full verification: backend `pytest -q` → all pass; frontend `npm test`, `npm run lint`, `npm run build` → pass; fresh DB path: `alembic downgrade base` then `upgrade head` on the dev DB, `seed.py`, `seed_catalogue.py`, then the manual walk-through of Tasks 7–9 in the browser.
- [ ] **Step 3: Commit** `docs: document the v2 catalogue (univers, teintes, visibility)`
- [ ] **Step 4:** Push `Branche-v2-lot1-catalogue`, open the PR to `main` (French title « v2 lot 1 : catalogue en trois univers, teintes et visibilité », body = summary + test results, no Claude attribution), tell Rémy it is ready to review and merge.
