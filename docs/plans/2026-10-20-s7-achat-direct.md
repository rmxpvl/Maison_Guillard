# S7 — Achat direct (panier, commande, confirmation) Implementation Plan

**Goal:** A visitor adds available pieces to a cart, sends an order with contact details, and sees
a confirmation; the order is stored as `en_attente`, and (if the admin turned it on) the artisan
and the customer receive an email.

**Architecture:** Backend gains three tables (`commande`, `ligne_commande`, `parametre`), a
`commande_service` that always reads prices from the database, a public `POST /api/commandes`, two
admin routes for the email setting, and an `email_service` (standard-library `smtplib`) run in a
FastAPI `BackgroundTasks`. Frontend gains pure cart functions in `utils/panier.js`
(`node:test`-tested), a `PanierContext` persisted in `localStorage`, and three pages
(`/panier`, `/commande`, `/commande/confirmation`).

**Tech Stack:** Python 3.14, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2 (+ `email-validator`),
pytest, PostgreSQL 16 (docker-compose); Node 25, React 19, react-router-dom 7, Vite, `node:test`.

**Spec:** `docs/specs/2026-10-20-s7-achat-direct-design.md`

**Who types what:** Remy types every line of app code (backend and frontend). Each task is
explained before typing; tests and git are run together after each task.

## Global Constraints

- Branch: `Branche-S7` (already created from `main`, holds the spec).
- Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`), no trailers.
- Commands are run from `backend/` with `.\.venv\Scripts\python.exe` (PowerShell), or from
  `frontend/` with `npm`. Docker Desktop must be running (`docker compose up -d`).
- Every migration is applied to **both** databases: `maison_guillard` and `maison_guillard_test`.
- Only `disponible` products can be ordered. Quantity per line: **1 to 10**.
- The price is never read from the request: always `produit.prix` from the database.
- `email_commande_actif` defaults to **false**. An SMTP failure never fails an order.
- `.env` is never committed; `.env.example` documents every variable without secrets.
- UI text in French. API error `detail` messages in French.

## Review Focus

- An admin deletes a product that already appears in an order → **409** with a French message,
  not a 500 (Task 2).
- A product in the visitor's cart was switched to `rupture` (or deleted) before checkout → **422**
  naming the product, cart kept so the visitor can remove it (Tasks 4 and 9).
- Email setting on but SMTP down or not configured → the order still returns **201** (Task 6).
- `localStorage` holds a corrupted or outdated cart → the site shows an empty cart instead of
  crashing (Task 7).
- Name or address made only of spaces → **422** (Task 3).

---

### Task 1: Models and migration (`commande`, `ligne_commande`, `parametre`)

**Files:**
- Create: `backend/app/models/commande.py`
- Create: `backend/app/models/parametre.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/alembic/env.py:16`
- Create: `backend/alembic/versions/<generated>_add_commande_ligne_commande_parametre.py`

**Interfaces:**
- Produces: `StatutCommande` enum, `Commande` (with `lignes` and the computed `total`),
  `LigneCommande` (with `produit`), `Parametre`.

- [ ] **Step 1: Create `backend/app/models/commande.py`**

```python
import enum
from decimal import Decimal

from sqlalchemy import Column, DateTime, Enum as SqlEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class StatutCommande(str, enum.Enum):
    en_attente = "en_attente"
    confirmee = "confirmee"
    expediee = "expediee"
    livree = "livree"
    annulee = "annulee"


class Commande(Base):
    __tablename__ = "commande"

    id = Column(Integer, primary_key=True, index=True)
    nom_client = Column(String, nullable=False)
    email = Column(String, nullable=False)
    telephone = Column(String, nullable=True)
    adresse = Column(String, nullable=False)
    statut = Column(
        SqlEnum(StatutCommande, name="statut_commande_enum"),
        nullable=False,
        default=StatutCommande.en_attente,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    lignes = relationship(
        "LigneCommande",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Not a column: recomputed from the lines each time it is read.
    @property
    def total(self) -> Decimal:
        return sum(
            (ligne.prix_unitaire_snapshot * ligne.quantite for ligne in self.lignes),
            Decimal("0"),
        )


class LigneCommande(Base):
    __tablename__ = "ligne_commande"

    id = Column(Integer, primary_key=True, index=True)
    commande_id = Column(
        Integer, ForeignKey("commande.id", ondelete="CASCADE"), nullable=False
    )
    # No cascade here: deleting a produit must never erase an order line.
    produit_id = Column(Integer, ForeignKey("produit.id"), nullable=False)
    quantite = Column(Integer, nullable=False)
    prix_unitaire_snapshot = Column(Numeric(10, 2), nullable=False)
    produit = relationship("Produit", lazy="selectin")
```

- [ ] **Step 2: Create `backend/app/models/parametre.py`**

```python
from sqlalchemy import Boolean, Column, Integer, false

from app.database import Base


# Site settings the admin can change. A single row, created on first read.
class Parametre(Base):
    __tablename__ = "parametre"

    id = Column(Integer, primary_key=True)
    email_commande_actif = Column(
        Boolean, nullable=False, default=False, server_default=false()
    )
```

- [ ] **Step 3: Export the models — replace `backend/app/models/__init__.py` with**

```python
from app.models.admin import Admin
from app.models.categorie import Categorie
from app.models.produit import Produit, Disponibilite
from app.models.photo import Photo
from app.models.commande import Commande, LigneCommande, StatutCommande
from app.models.parametre import Parametre

__all__ = [
    "Admin",
    "Categorie",
    "Produit",
    "Disponibilite",
    "Photo",
    "Commande",
    "LigneCommande",
    "StatutCommande",
    "Parametre",
]
```

- [ ] **Step 4: Let Alembic see the new tables — in `backend/alembic/env.py`, replace line 16 with**

```python
from app.models import Admin, Categorie, Produit, Photo, Commande, LigneCommande, Parametre  # noqa: F401 — import so Base.metadata sees the tables
```

- [ ] **Step 5: Generate the migration**

Run (from `backend/`):
```powershell
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "add commande ligne_commande parametre"
```
Expected: `Generating ...\alembic\versions\<id>_add_commande_ligne_commande_parametre.py ... done`.
Open the file and check `upgrade()` creates `commande` (with
`sa.Enum('en_attente', ..., name='statut_commande_enum')`), `ligne_commande` (two foreign keys,
`ondelete='CASCADE'` on `commande_id` only) and `parametre` (`server_default=sa.text('false')`).

Autogenerate does **not** drop the PostgreSQL enum type on downgrade. At the end of `downgrade()`,
after the `op.drop_table('commande')` line, add:
```python
    sa.Enum(name='statut_commande_enum').drop(op.get_bind(), checkfirst=True)
```

- [ ] **Step 6: Apply the migration to both databases**

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
$env:DATABASE_URL = (Select-String -Path .env -Pattern '^TEST_DATABASE_URL=(.*)').Matches.Groups[1].Value
.\.venv\Scripts\python.exe -m alembic upgrade head
Remove-Item Env:DATABASE_URL
```
Expected: both runs end with `Running upgrade 6225571fe9c4 -> <id>, add commande ligne_commande parametre`.
(The second run targets the test database: `load_dotenv()` never overrides a variable that is
already set.)

- [ ] **Step 7: Check nothing broke**

Run: `.\.venv\Scripts\python.exe -m pytest -q`
Expected: `80 passed`.

- [ ] **Step 8: Commit**

```powershell
git add app/models alembic/env.py alembic/versions
git commit -m "feat: add commande, ligne_commande and parametre tables"
```

---

### Task 2: Refuse deleting a product that is in an order (409)

**Files:**
- Modify: `backend/app/services/produit_service.py` (`delete`, new exception)
- Modify: `backend/app/routers/produits.py` (`delete_produit`)
- Create: `backend/tests/integration/test_suppression_produit_commande.py`

**Interfaces:**
- Consumes: `Commande`, `LigneCommande` (Task 1).
- Produces: `produit_service.ProduitEnCommandeError`.

- [ ] **Step 1: Write the failing test — `backend/tests/integration/test_suppression_produit_commande.py`**

```python
import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie
from app.models.commande import Commande, LigneCommande
from app.models.produit import Disponibilite, Produit
from app.services import auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    # Commande first: its lines reference produits.
    for modele in (Commande, Produit, Categorie, Admin):
        db.query(modele).delete()
    db.commit()
    yield db
    for modele in (Commande, Produit, Categorie, Admin):
        db.query(modele).delete()
    db.commit()
    db.close()


def _admin_token(db):
    db.add(Admin(email="admin@test.com", password_hash=auth_service.hash_password("test-password-123")))
    db.commit()
    return auth_service.login(db, "admin@test.com", "test-password-123")


def test_delete_produit_present_dans_une_commande_renvoie_409(clean_db):
    token = _admin_token(clean_db)
    categorie = Categorie(nom="Tables", slug="tables")
    clean_db.add(categorie)
    clean_db.commit()
    produit = Produit(
        nom="Table basse", description="En chêne", categorie_id=categorie.id,
        prix=199.99, dimensions="120x60x40cm", disponibilite=Disponibilite.disponible,
    )
    clean_db.add(produit)
    clean_db.commit()
    clean_db.add(Commande(
        nom_client="Jeanne", email="jeanne@test.com", adresse="1 rue du Bois",
        lignes=[LigneCommande(produit_id=produit.id, quantite=1, prix_unitaire_snapshot=199.99)],
    ))
    clean_db.commit()

    res = client.delete(f"/api/produits/{produit.id}", headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 409
    assert "rupture" in res.json()["detail"]
```

- [ ] **Step 2: Run it to see it fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/integration/test_suppression_produit_commande.py -v`
Expected: FAIL with `sqlalchemy.exc.IntegrityError` (`ForeignKeyViolation` on `ligne_commande`).

- [ ] **Step 3: In `backend/app/services/produit_service.py`, add the exception under `CategorieIntrouvableError`**

```python
class ProduitEnCommandeError(Exception):
    """Raised when deleting a produit that appears in at least one order line."""
```

and replace `delete` with:

```python
def delete(db: Session, produit_id: int) -> bool:
    produit = get_by_id(db, produit_id)
    if produit is None:
        return False

    db.delete(produit)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ProduitEnCommandeError()
    return True
```

- [ ] **Step 4: In `backend/app/routers/produits.py`, replace `delete_produit`**

```python
@router.delete(
    "/{produit_id}",
    status_code=204,
    summary="Supprimer un produit et ses photos",
    responses={
        **NON_AUTORISE,
        **PRODUIT_INTROUVABLE,
        409: {"description": "Produit présent dans des commandes"},
    },
)
def delete_produit(
    produit_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    try:
        deleted = produit_service.delete(db, produit_id)
    except produit_service.ProduitEnCommandeError:
        raise HTTPException(
            status_code=409,
            detail="Produit présent dans des commandes : passez-le en rupture",
        )
    if not deleted:
        raise HTTPException(status_code=404, detail="Produit introuvable")
```

- [ ] **Step 5: Run the test, then the whole suite**

Run: `.\.venv\Scripts\python.exe -m pytest tests/integration/test_suppression_produit_commande.py -v` → PASS.
Run: `.\.venv\Scripts\python.exe -m pytest -q` → `81 passed`.

- [ ] **Step 6: Commit**

```powershell
git add app/services/produit_service.py app/routers/produits.py tests/integration/test_suppression_produit_commande.py
git commit -m "feat: return 409 when deleting a produit that is in an order"
```

---

### Task 3: Order schemas and `commande_service`

**Files:**
- Modify: `backend/requirements.txt` (add `email-validator`)
- Create: `backend/app/schemas/commande.py`
- Create: `backend/app/services/commande_service.py`
- Create: `backend/tests/unit/test_commande_service.py`
- Create: `backend/tests/unit/test_commande_schema.py`

**Interfaces:**
- Consumes: `Commande`, `LigneCommande` (Task 1); `Produit`, `Disponibilite`.
- Produces: `CommandeIn`, `CommandeOut`, `LigneCommandeIn`, `LigneCommandeOut`;
  `commande_service.create(db: Session, data: dict) -> Commande`;
  `commande_service.ProduitIntrouvableError` (attr `produit_id`),
  `commande_service.ProduitIndisponibleError` (attrs `produit_id`, `nom`).

- [ ] **Step 1: Install `email-validator` (needed by Pydantic's `EmailStr`)**

```powershell
.\.venv\Scripts\python.exe -m pip install email-validator
.\.venv\Scripts\python.exe -m pip show email-validator
```
Add a line `email-validator==<version shown>` to `requirements.txt`.

- [ ] **Step 2: Write the failing schema tests — `backend/tests/unit/test_commande_schema.py`**

```python
import pytest
from pydantic import ValidationError

from app.schemas.commande import CommandeIn


def _commande(**changes):
    data = {
        "nom_client": "Jeanne Martin",
        "email": "jeanne@test.com",
        "adresse": "1 rue du Bois, 44000 Nantes",
        "lignes": [{"produit_id": 1, "quantite": 2}],
    }
    data.update(changes)
    return data


def test_commande_valide_sans_telephone():
    commande = CommandeIn(**_commande())
    assert commande.telephone is None


@pytest.mark.parametrize(
    "changes",
    [
        {"lignes": []},
        {"lignes": [{"produit_id": 1, "quantite": 0}]},
        {"lignes": [{"produit_id": 1, "quantite": 11}]},
        {"lignes": [{"produit_id": 1, "quantite": 1}, {"produit_id": 1, "quantite": 2}]},
        {"email": "pas-un-email"},
        {"nom_client": "   "},
        {"adresse": ""},
    ],
)
def test_commande_invalide_est_refusee(changes):
    with pytest.raises(ValidationError):
        CommandeIn(**_commande(**changes))
```

- [ ] **Step 3: Run it to see it fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/unit/test_commande_schema.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.schemas.commande'`.

- [ ] **Step 4: Create `backend/app/schemas/commande.py`**

```python
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.commande import StatutCommande


class LigneCommandeIn(BaseModel):
    produit_id: int
    quantite: int = Field(ge=1, le=10)


class CommandeIn(BaseModel):
    # "   " becomes "" before min_length is checked, so blank fields are refused.
    model_config = ConfigDict(str_strip_whitespace=True)

    nom_client: str = Field(min_length=1, max_length=100)
    email: EmailStr
    telephone: str | None = Field(default=None, max_length=30)
    adresse: str = Field(min_length=1, max_length=300)
    lignes: list[LigneCommandeIn] = Field(min_length=1, max_length=50)

    @field_validator("lignes")
    @classmethod
    def un_produit_par_ligne(cls, lignes: list[LigneCommandeIn]) -> list[LigneCommandeIn]:
        ids = [ligne.produit_id for ligne in lignes]
        if len(ids) != len(set(ids)):
            raise ValueError("Chaque produit ne doit apparaître qu'une fois")
        return lignes


class LigneCommandeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produit_id: int
    quantite: int
    prix_unitaire_snapshot: Decimal


class CommandeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom_client: str
    email: str
    telephone: str | None
    adresse: str
    statut: StatutCommande
    created_at: datetime
    lignes: list[LigneCommandeOut]
    total: Decimal
```

- [ ] **Step 5: Run the schema tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/unit/test_commande_schema.py -v`
Expected: 8 passed.

- [ ] **Step 6: Write the failing service tests — `backend/tests/unit/test_commande_service.py`**

```python
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.models.produit import Disponibilite
from app.services import commande_service


def _produit(id, prix, disponibilite=Disponibilite.disponible, nom="Table basse"):
    return MagicMock(id=id, prix=Decimal(prix), disponibilite=disponibilite, nom=nom)


def _data(lignes):
    return {
        "nom_client": "Jeanne Martin",
        "email": "jeanne@test.com",
        "telephone": None,
        "adresse": "1 rue du Bois",
        "lignes": lignes,
    }


def _db_qui_trouve(*produits):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = list(produits)
    return db


def test_create_prend_le_prix_en_base_et_calcule_le_total():
    db = _db_qui_trouve(_produit(1, "199.99"), _produit(2, "50.00"))

    commande = commande_service.create(
        db,
        _data([
            # An extra "prix" key from a malicious client must be ignored.
            {"produit_id": 1, "quantite": 2, "prix": "0.01"},
            {"produit_id": 2, "quantite": 1},
        ]),
    )

    assert [l.prix_unitaire_snapshot for l in commande.lignes] == [Decimal("199.99"), Decimal("50.00")]
    assert commande.total == Decimal("449.98")
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.parametrize("disponibilite", [Disponibilite.rupture, Disponibilite.sur_commande])
def test_create_refuse_un_produit_non_disponible(disponibilite):
    db = _db_qui_trouve(_produit(3, "80.00", disponibilite, nom="Lampe"))

    with pytest.raises(commande_service.ProduitIndisponibleError) as erreur:
        commande_service.create(db, _data([{"produit_id": 3, "quantite": 1}]))

    assert erreur.value.nom == "Lampe"
    db.commit.assert_not_called()


def test_create_refuse_un_produit_inconnu():
    db = _db_qui_trouve(None)

    with pytest.raises(commande_service.ProduitIntrouvableError) as erreur:
        commande_service.create(db, _data([{"produit_id": 999, "quantite": 1}]))

    assert erreur.value.produit_id == 999
    db.commit.assert_not_called()
```

- [ ] **Step 7: Run them to see them fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/unit/test_commande_service.py -v`
Expected: FAIL with `ImportError: cannot import name 'commande_service'`.

- [ ] **Step 8: Create `backend/app/services/commande_service.py`**

```python
from sqlalchemy.orm import Session

from app.models.commande import Commande, LigneCommande
from app.models.produit import Disponibilite, Produit


class ProduitIntrouvableError(Exception):
    """Raised when an order line references a produit that does not exist."""

    def __init__(self, produit_id: int):
        super().__init__(produit_id)
        self.produit_id = produit_id


class ProduitIndisponibleError(Exception):
    """Raised when an order line references a produit that is not 'disponible'."""

    def __init__(self, produit: Produit):
        super().__init__(produit.id)
        self.produit_id = produit.id
        self.nom = produit.nom


def create(db: Session, data: dict) -> Commande:
    lignes = []
    for ligne in data["lignes"]:
        produit = db.query(Produit).filter(Produit.id == ligne["produit_id"]).first()
        if produit is None:
            raise ProduitIntrouvableError(ligne["produit_id"])
        if produit.disponibilite != Disponibilite.disponible:
            raise ProduitIndisponibleError(produit)
        # The price comes from the database, never from the request.
        lignes.append(
            LigneCommande(
                produit_id=produit.id,
                quantite=ligne["quantite"],
                prix_unitaire_snapshot=produit.prix,
            )
        )

    commande = Commande(
        nom_client=data["nom_client"],
        email=data["email"],
        telephone=data.get("telephone"),
        adresse=data["adresse"],
        lignes=lignes,
    )
    db.add(commande)
    db.commit()
    db.refresh(commande)
    return commande
```

- [ ] **Step 9: Run the unit tests, then the whole suite**

Run: `.\.venv\Scripts\python.exe -m pytest tests/unit/test_commande_service.py tests/unit/test_commande_schema.py -v` → 12 passed.
Run: `.\.venv\Scripts\python.exe -m pytest -q` → `93 passed`.

- [ ] **Step 10: Commit**

```powershell
git add requirements.txt app/schemas/commande.py app/services/commande_service.py tests/unit/test_commande_schema.py tests/unit/test_commande_service.py
git commit -m "feat: add commande schemas and service with database prices"
```

---

### Task 4: `POST /api/commandes`

**Files:**
- Create: `backend/app/routers/commandes.py`
- Modify: `backend/app/main.py` (tag + router)
- Create: `backend/tests/integration/test_commandes_routes.py`

**Interfaces:**
- Consumes: `CommandeIn`, `CommandeOut`, `commande_service` (Task 3).
- Produces: `POST /api/commandes` → 201 `CommandeOut` / 422 `{"detail": str}` for business
  errors, 422 `{"detail": [...]}` for validation errors. Task 6 adds the email call to this route.

- [ ] **Step 1: Write the failing tests — `backend/tests/integration/test_commandes_routes.py`**

```python
import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.categorie import Categorie
from app.models.commande import Commande
from app.models.parametre import Parametre
from app.models.produit import Disponibilite, Produit

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    # Commande first: its lines reference produits.
    for modele in (Commande, Parametre, Produit, Categorie):
        db.query(modele).delete()
    db.commit()
    yield db
    for modele in (Commande, Parametre, Produit, Categorie):
        db.query(modele).delete()
    db.commit()
    db.close()


def _produit(db, nom="Table basse", prix=199.99, disponibilite=Disponibilite.disponible):
    categorie = db.query(Categorie).first()
    if categorie is None:
        categorie = Categorie(nom="Tables", slug="tables")
        db.add(categorie)
        db.commit()
    produit = Produit(
        nom=nom, description="En chêne", categorie_id=categorie.id, prix=prix,
        dimensions="120x60x40cm", disponibilite=disponibilite,
    )
    db.add(produit)
    db.commit()
    db.refresh(produit)
    return produit


def _corps(lignes):
    return {
        "nom_client": "Jeanne Martin",
        "email": "jeanne@test.com",
        "telephone": "06 12 34 56 78",
        "adresse": "1 rue du Bois, 44000 Nantes",
        "lignes": lignes,
    }


def test_post_commande_cree_la_commande_en_attente(clean_db):
    table = _produit(clean_db, prix=199.99)
    lampe = _produit(clean_db, nom="Lampe", prix=80)

    res = client.post("/api/commandes", json=_corps([
        {"produit_id": table.id, "quantite": 2},
        {"produit_id": lampe.id, "quantite": 1},
    ]))

    assert res.status_code == 201
    body = res.json()
    assert body["statut"] == "en_attente"
    assert body["total"] == "479.98"
    assert [l["prix_unitaire_snapshot"] for l in body["lignes"]] == ["199.99", "80.00"]
    assert clean_db.query(Commande).count() == 1


@pytest.mark.parametrize("disponibilite", [Disponibilite.rupture, Disponibilite.sur_commande])
def test_post_commande_refuse_un_produit_non_disponible(clean_db, disponibilite):
    produit = _produit(clean_db, nom="Tabouret", disponibilite=disponibilite)

    res = client.post("/api/commandes", json=_corps([{"produit_id": produit.id, "quantite": 1}]))

    assert res.status_code == 422
    assert res.json()["detail"] == "« Tabouret » n'est plus disponible"
    assert clean_db.query(Commande).count() == 0


def test_post_commande_refuse_un_produit_inconnu(clean_db):
    res = client.post("/api/commandes", json=_corps([{"produit_id": 999999, "quantite": 1}]))

    assert res.status_code == 422
    assert res.json()["detail"] == "Produit n°999999 introuvable"


def test_post_commande_refuse_un_corps_invalide(clean_db):
    res = client.post("/api/commandes", json=_corps([]))

    assert res.status_code == 422
    assert isinstance(res.json()["detail"], list)  # Pydantic's validation format
```

- [ ] **Step 2: Run them to see them fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/integration/test_commandes_routes.py -v`
Expected: FAIL, `assert 404 == 201` (the route does not exist yet).

- [ ] **Step 3: Create `backend/app/routers/commandes.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.commande import CommandeIn, CommandeOut
from app.services import commande_service

router = APIRouter(prefix="/api/commandes", tags=["Commandes"])


@router.post(
    "",
    response_model=CommandeOut,
    status_code=201,
    summary="Passer une commande",
    responses={422: {"description": "Données invalides, produit introuvable ou indisponible"}},
)
def create_commande(payload: CommandeIn, db: Session = Depends(get_db)):
    try:
        commande = commande_service.create(db, payload.model_dump())
    except commande_service.ProduitIntrouvableError as erreur:
        raise HTTPException(status_code=422, detail=f"Produit n°{erreur.produit_id} introuvable")
    except commande_service.ProduitIndisponibleError as erreur:
        raise HTTPException(status_code=422, detail=f"« {erreur.nom} » n'est plus disponible")
    return commande
```

- [ ] **Step 4: Register it in `backend/app/main.py`**

Change the import line to:
```python
from app.routers import auth, categories, commandes, produits
```
Add to `TAGS`, after the `"Photos"` entry:
```python
    {"name": "Commandes", "description": "Achat direct : un visiteur passe une commande."},
```
Add after `app.include_router(produits.photos_router)`:
```python
app.include_router(commandes.router)
```

- [ ] **Step 5: Run the tests, then the whole suite**

Run: `.\.venv\Scripts\python.exe -m pytest tests/integration/test_commandes_routes.py -v` → 5 passed.
Run: `.\.venv\Scripts\python.exe -m pytest -q` → `98 passed`.

- [ ] **Step 6: Commit**

```powershell
git add app/routers/commandes.py app/main.py tests/integration/test_commandes_routes.py
git commit -m "feat: add POST /api/commandes"
```

---

### Task 5: Email setting — `parametre_service` and admin routes

**Files:**
- Create: `backend/app/schemas/parametre.py`
- Create: `backend/app/services/parametre_service.py`
- Create: `backend/app/routers/parametres.py`
- Modify: `backend/app/main.py` (tag + router)
- Modify: `backend/tests/integration/test_securite_et_erreurs.py` (`ROUTES_ADMIN`)
- Create: `backend/tests/integration/test_parametres_routes.py`

**Interfaces:**
- Consumes: `Parametre` (Task 1).
- Produces: `parametre_service.get(db) -> Parametre` (creates the row if missing),
  `parametre_service.update(db, data: dict) -> Parametre`; `GET`/`PUT /api/parametres` (admin).

- [ ] **Step 1: Write the failing tests — `backend/tests/integration/test_parametres_routes.py`**

```python
import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.parametre import Parametre
from app.services import auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    db.query(Parametre).delete()
    db.query(Admin).delete()
    db.commit()
    yield db
    db.query(Parametre).delete()
    db.query(Admin).delete()
    db.commit()
    db.close()


def _entetes(db):
    db.add(Admin(email="admin@test.com", password_hash=auth_service.hash_password("test-password-123")))
    db.commit()
    token = auth_service.login(db, "admin@test.com", "test-password-123")
    return {"Authorization": f"Bearer {token}"}


def test_email_commande_desactive_par_defaut(clean_db):
    res = client.get("/api/parametres", headers=_entetes(clean_db))

    assert res.status_code == 200
    assert res.json() == {"email_commande_actif": False}


def test_admin_active_puis_relit_le_reglage(clean_db):
    entetes = _entetes(clean_db)

    res = client.put("/api/parametres", json={"email_commande_actif": True}, headers=entetes)
    assert res.status_code == 200

    assert client.get("/api/parametres", headers=entetes).json() == {"email_commande_actif": True}
    assert clean_db.query(Parametre).count() == 1  # still a single row
```

In `backend/tests/integration/test_securite_et_erreurs.py`, add two entries at the end of
`ROUTES_ADMIN`:
```python
    ("get", "/api/parametres"),
    ("put", "/api/parametres"),
```

- [ ] **Step 2: Run them to see them fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/integration/test_parametres_routes.py tests/integration/test_securite_et_erreurs.py -v`
Expected: FAIL, `assert 404 == 200` and `assert 404 == 401`.

- [ ] **Step 3: Create `backend/app/schemas/parametre.py`**

```python
from pydantic import BaseModel, ConfigDict


class ParametreIn(BaseModel):
    email_commande_actif: bool


class ParametreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email_commande_actif: bool
```

- [ ] **Step 4: Create `backend/app/services/parametre_service.py`**

```python
from sqlalchemy.orm import Session

from app.models.parametre import Parametre


def get(db: Session) -> Parametre:
    parametre = db.query(Parametre).first()
    if parametre is None:
        parametre = Parametre(email_commande_actif=False)
        db.add(parametre)
        db.commit()
        db.refresh(parametre)
    return parametre


def update(db: Session, data: dict) -> Parametre:
    parametre = get(db)
    parametre.email_commande_actif = data["email_commande_actif"]
    db.commit()
    db.refresh(parametre)
    return parametre
```

- [ ] **Step 5: Create `backend/app/routers/parametres.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_admin import require_admin
from app.routers.reponses import NON_AUTORISE
from app.schemas.parametre import ParametreIn, ParametreOut
from app.services import parametre_service

router = APIRouter(prefix="/api/parametres", tags=["Paramètres"])


@router.get(
    "",
    response_model=ParametreOut,
    summary="Lire les réglages du site",
    responses=NON_AUTORISE,
)
def get_parametres(db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    return parametre_service.get(db)


@router.put(
    "",
    response_model=ParametreOut,
    summary="Modifier les réglages du site",
    responses=NON_AUTORISE,
)
def update_parametres(
    payload: ParametreIn,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    return parametre_service.update(db, payload.model_dump())
```

- [ ] **Step 6: Register it in `backend/app/main.py`**

Import line:
```python
from app.routers import auth, categories, commandes, parametres, produits
```
Add to `TAGS`, after `"Commandes"`:
```python
    {"name": "Paramètres", "description": "Réglages du site, dont l'e-mail automatique à chaque commande."},
```
Add after `app.include_router(commandes.router)`:
```python
app.include_router(parametres.router)
```

- [ ] **Step 7: Run the tests, then the whole suite**

Run: `.\.venv\Scripts\python.exe -m pytest tests/integration/test_parametres_routes.py tests/integration/test_securite_et_erreurs.py -v` → all passed.
Run: `.\.venv\Scripts\python.exe -m pytest -q` → `104 passed`.

- [ ] **Step 8: Commit**

```powershell
git add app/schemas/parametre.py app/services/parametre_service.py app/routers/parametres.py app/main.py tests/integration/test_parametres_routes.py tests/integration/test_securite_et_erreurs.py
git commit -m "feat: add admin setting for order emails"
```

---

### Task 6: Order emails (`email_service` + background task)

**Files:**
- Create: `backend/app/services/email_service.py`
- Modify: `backend/app/routers/commandes.py`
- Modify: `backend/.env.example`, `backend/.env` (not committed)
- Create: `backend/tests/unit/test_email_service.py`
- Modify: `backend/tests/integration/test_commandes_routes.py` (3 tests)

**Interfaces:**
- Consumes: `Commande` with `lignes[].produit.nom` (Task 1), `parametre_service.get` (Task 5),
  `create_commande` route (Task 4).
- Produces: `email_service.messages_nouvelle_commande(commande) -> list[EmailMessage]`,
  `email_service.envoyer(messages: list[EmailMessage]) -> None` (never raises).

Why the messages are built in the route and only *sent* in the background: background tasks run
after the response, when the database session is already closed. Building the emails while the
order is still loaded avoids reading a closed session.

- [ ] **Step 1: Write the failing unit tests — `backend/tests/unit/test_email_service.py`**

```python
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services import email_service


@pytest.fixture(autouse=True)
def smtp_env(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.test")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@test.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setenv("EMAIL_EXPEDITEUR", "site@test.com")
    monkeypatch.setenv("EMAIL_ARTISAN", "artisan@test.com")


def _commande():
    ligne = MagicMock(quantite=2, prix_unitaire_snapshot=Decimal("199.99"))
    ligne.produit.nom = "Table basse"
    return MagicMock(
        id=42, nom_client="Jeanne Martin", email="jeanne@test.com", telephone=None,
        adresse="1 rue du Bois", lignes=[ligne], total=Decimal("399.98"),
    )


def test_messages_pour_l_artisan_et_le_client():
    artisan, client = email_service.messages_nouvelle_commande(_commande())

    assert artisan["To"] == "artisan@test.com"
    assert artisan["Subject"] == "Nouvelle commande n°42"
    assert "Table basse x 2" in artisan.get_content()
    assert "399.98 €" in artisan.get_content()
    assert client["To"] == "jeanne@test.com"
    assert "48 h" in client.get_content()


def test_envoyer_passe_par_smtp_avec_starttls():
    with patch("app.services.email_service.smtplib.SMTP") as smtp:
        email_service.envoyer(email_service.messages_nouvelle_commande(_commande()))

    serveur = smtp.return_value.__enter__.return_value
    serveur.starttls.assert_called_once()
    serveur.login.assert_called_once_with("user@test.com", "secret")
    assert serveur.send_message.call_count == 2


def test_envoyer_ne_leve_jamais_d_erreur():
    with patch("app.services.email_service.smtplib.SMTP", side_effect=OSError("réseau coupé")):
        email_service.envoyer(email_service.messages_nouvelle_commande(_commande()))  # no exception
```

- [ ] **Step 2: Run them to see them fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/unit/test_email_service.py -v`
Expected: FAIL with `ImportError: cannot import name 'email_service'`.

- [ ] **Step 3: Create `backend/app/services/email_service.py`**

```python
import logging
import os
import smtplib
from email.message import EmailMessage

from app.models.commande import Commande

logger = logging.getLogger(__name__)


def _recapitulatif(commande: Commande) -> str:
    lignes = [
        f"- {ligne.produit.nom} x {ligne.quantite} : "
        f"{ligne.prix_unitaire_snapshot * ligne.quantite} €"
        for ligne in commande.lignes
    ]
    return "\n".join(lignes) + f"\n\nTotal : {commande.total} €"


def _message(destinataire: str, sujet: str, texte: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = os.environ["EMAIL_EXPEDITEUR"]
    message["To"] = destinataire
    message["Subject"] = sujet
    message.set_content(texte)
    return message


def messages_nouvelle_commande(commande: Commande) -> list[EmailMessage]:
    artisan = _message(
        os.environ["EMAIL_ARTISAN"],
        f"Nouvelle commande n°{commande.id}",
        f"Client : {commande.nom_client}\n"
        f"E-mail : {commande.email}\n"
        f"Téléphone : {commande.telephone or 'non renseigné'}\n"
        f"Adresse : {commande.adresse}\n\n"
        f"{_recapitulatif(commande)}\n",
    )
    client = _message(
        commande.email,
        f"Maison Guillard : commande n°{commande.id} reçue",
        f"Bonjour {commande.nom_client},\n\n"
        f"Nous avons bien reçu votre commande n°{commande.id} :\n\n"
        f"{_recapitulatif(commande)}\n\n"
        "Maison Guillard vous contacte sous 48 h pour le paiement et la livraison.\n",
    )
    return [artisan, client]


def envoyer(messages: list[EmailMessage]) -> None:
    # Runs after the response: an email problem must never cancel an order.
    try:
        with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"]), timeout=10) as serveur:
            serveur.starttls()
            serveur.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
            for message in messages:
                serveur.send_message(message)
    except Exception:
        logger.exception("Envoi des e-mails de commande impossible")
```

- [ ] **Step 4: Run the unit tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/unit/test_email_service.py -v` → 3 passed.

- [ ] **Step 5: Add the failing route tests at the end of `backend/tests/integration/test_commandes_routes.py`**

Add at the top with the other imports:
```python
from unittest.mock import patch
```
Add at the end:
```python
@pytest.fixture
def smtp_env(monkeypatch):
    for nom, valeur in {
        "SMTP_HOST": "smtp.test", "SMTP_PORT": "587", "SMTP_USER": "user@test.com",
        "SMTP_PASSWORD": "secret", "EMAIL_EXPEDITEUR": "site@test.com",
        "EMAIL_ARTISAN": "artisan@test.com",
    }.items():
        monkeypatch.setenv(nom, valeur)


def _activer_email(db, actif):
    db.add(Parametre(email_commande_actif=actif))
    db.commit()


def test_aucun_email_quand_le_reglage_est_desactive(clean_db, smtp_env):
    produit = _produit(clean_db)
    _activer_email(clean_db, False)

    with patch("app.services.email_service.smtplib.SMTP") as smtp:
        res = client.post("/api/commandes", json=_corps([{"produit_id": produit.id, "quantite": 1}]))

    assert res.status_code == 201
    smtp.assert_not_called()


def test_deux_emails_quand_le_reglage_est_active(clean_db, smtp_env):
    produit = _produit(clean_db)
    _activer_email(clean_db, True)

    # TestClient runs background tasks before returning the response.
    with patch("app.services.email_service.smtplib.SMTP") as smtp:
        res = client.post("/api/commandes", json=_corps([{"produit_id": produit.id, "quantite": 1}]))

    assert res.status_code == 201
    assert smtp.return_value.__enter__.return_value.send_message.call_count == 2


def test_commande_creee_meme_si_le_serveur_smtp_est_injoignable(clean_db, smtp_env):
    produit = _produit(clean_db)
    _activer_email(clean_db, True)

    with patch("app.services.email_service.smtplib.SMTP", side_effect=OSError("réseau coupé")):
        res = client.post("/api/commandes", json=_corps([{"produit_id": produit.id, "quantite": 1}]))

    assert res.status_code == 201
    assert clean_db.query(Commande).count() == 1
```

- [ ] **Step 6: Run them to see the "activé" test fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/integration/test_commandes_routes.py -v`
Expected: `test_deux_emails_quand_le_reglage_est_active` FAILS (`assert 0 == 2`); the other two
pass already (nothing is sent yet).

- [ ] **Step 7: Call the email service from the route — replace `backend/app/routers/commandes.py` with**

```python
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.commande import CommandeIn, CommandeOut
from app.services import commande_service, email_service, parametre_service

router = APIRouter(prefix="/api/commandes", tags=["Commandes"])


@router.post(
    "",
    response_model=CommandeOut,
    status_code=201,
    summary="Passer une commande",
    responses={422: {"description": "Données invalides, produit introuvable ou indisponible"}},
)
def create_commande(
    payload: CommandeIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        commande = commande_service.create(db, payload.model_dump())
    except commande_service.ProduitIntrouvableError as erreur:
        raise HTTPException(status_code=422, detail=f"Produit n°{erreur.produit_id} introuvable")
    except commande_service.ProduitIndisponibleError as erreur:
        raise HTTPException(status_code=422, detail=f"« {erreur.nom} » n'est plus disponible")

    if parametre_service.get(db).email_commande_actif:
        try:
            messages = email_service.messages_nouvelle_commande(commande)
        except KeyError:
            # A missing EMAIL_* variable must not cancel the order either.
            messages = []
        if messages:
            background_tasks.add_task(email_service.envoyer, messages)
    return commande
```

- [ ] **Step 8: Run the tests, then the whole suite**

Run: `.\.venv\Scripts\python.exe -m pytest tests/integration/test_commandes_routes.py tests/unit/test_email_service.py -v` → all passed.
Run: `.\.venv\Scripts\python.exe -m pytest -q` → `110 passed`.

- [ ] **Step 9: Document the variables — append to `backend/.env.example`**

```
# E-mails de commande (envoyés seulement si le réglage est activé, PUT /api/parametres).
# En dev : Gmail + mot de passe d'application. Au déploiement : SMTP de l'hébergeur et adresse de l'artisane.
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=adresse@gmail.com
SMTP_PASSWORD=mot-de-passe-d-application
EMAIL_EXPEDITEUR=adresse@gmail.com
EMAIL_ARTISAN=adresse@gmail.com
```

Then create the Gmail **app password** (Google account → Sécurité → Validation en deux étapes
must be on → « Mots de passe des applications » → create one named "Maison Guillard") and add the
same six lines to `backend/.env` with real values: your Gmail address for `SMTP_USER`,
`EMAIL_EXPEDITEUR` and `EMAIL_ARTISAN`, and the 16-character app password (no spaces) for
`SMTP_PASSWORD`.

- [ ] **Step 10: Commit**

```powershell
git status   # .env must NOT appear
git add app/services/email_service.py app/routers/commandes.py .env.example tests/unit/test_email_service.py tests/integration/test_commandes_routes.py
git commit -m "feat: send order emails when the admin setting is on"
```

---

### Task 7: Cart rules — `utils/panier.js`

**Files:**
- Create: `frontend/src/utils/panier.js`
- Create: `frontend/src/utils/panier.test.js`
- Modify: `frontend/package.json` (`test` script)

**Interfaces:**
- Consumes: `photoPrincipale(photos)` from `utils/produit.js`.
- Produces: `QUANTITE_MAX`, `ajouterLigne(lignes, produit)`,
  `changerQuantiteLigne(lignes, produitId, quantite)`, `retirerLigne(lignes, produitId)`,
  `compterArticles(lignes)`, `totalPanier(lignes)`, `lignesValides(valeur)`,
  `lignesPourApi(lignes)`. A line is `{ produit_id, nom, prix, photo, quantite }`.

- [ ] **Step 1: Write the failing tests — `frontend/src/utils/panier.test.js`**

```js
import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  ajouterLigne,
  changerQuantiteLigne,
  compterArticles,
  lignesPourApi,
  lignesValides,
  retirerLigne,
  totalPanier,
} from './panier.js'

const table = { id: 1, nom: 'Table basse', prix: '199.99', photos: [{ id: 5, url: 'https://x/t.jpg', ordre: 0, principale: true }] }
const lampe = { id: 2, nom: 'Lampe', prix: '80.00', photos: [] }

test('ajouterLigne adds a new line with quantity 1 and the main photo', () => {
  assert.deepEqual(ajouterLigne([], table), [
    { produit_id: 1, nom: 'Table basse', prix: '199.99', photo: 'https://x/t.jpg', quantite: 1 },
  ])
  assert.equal(ajouterLigne([], lampe)[0].photo, null)
})

test('ajouterLigne on a product already in the cart adds 1, capped at 10', () => {
  const une = ajouterLigne([], table)
  assert.equal(ajouterLigne(une, table)[0].quantite, 2)
  const dix = changerQuantiteLigne(une, 1, 10)
  assert.equal(ajouterLigne(dix, table)[0].quantite, 10)
})

test('changerQuantiteLigne keeps the quantity between 1 and 10', () => {
  const lignes = ajouterLigne([], table)
  assert.equal(changerQuantiteLigne(lignes, 1, 0)[0].quantite, 1)
  assert.equal(changerQuantiteLigne(lignes, 1, 42)[0].quantite, 10)
  assert.equal(changerQuantiteLigne(lignes, 1, '3')[0].quantite, 3)
})

test('retirerLigne, compterArticles and totalPanier', () => {
  let lignes = ajouterLigne(ajouterLigne([], table), lampe)
  lignes = changerQuantiteLigne(lignes, 1, 2)
  assert.equal(compterArticles(lignes), 3)
  assert.equal(totalPanier(lignes).toFixed(2), '479.98')
  assert.deepEqual(retirerLigne(lignes, 1).map((l) => l.produit_id), [2])
})

test('lignesValides turns anything unexpected from localStorage into an empty cart', () => {
  assert.deepEqual(lignesValides(null), [])
  assert.deepEqual(lignesValides('texte'), [])
  assert.deepEqual(lignesValides({ produit_id: 1 }), [])
  assert.deepEqual(lignesValides([{ produit_id: 'x', quantite: 1 }]), [])
  const bon = ajouterLigne([], table)
  assert.deepEqual(lignesValides(bon), bon)
})

test('lignesPourApi sends only produit_id and quantite', () => {
  assert.deepEqual(lignesPourApi(ajouterLigne([], table)), [{ produit_id: 1, quantite: 1 }])
})
```

- [ ] **Step 2: Run them alongside the existing tests — change the `test` script in `frontend/package.json`**

```json
    "test": "node --test src/utils/produit.test.js src/utils/panier.test.js"
```
Run (from `frontend/`): `npm test`
Expected: FAIL with `Cannot find module '...src/utils/panier.js'`.

- [ ] **Step 3: Create `frontend/src/utils/panier.js`**

```js
import { photoPrincipale } from './produit.js'

export const QUANTITE_MAX = 10

// Any input (text from a <select>, a number, garbage) becomes an integer between 1 and 10.
function borner(quantite) {
  const n = Math.trunc(Number(quantite))
  if (!Number.isFinite(n) || n < 1) return 1
  return Math.min(n, QUANTITE_MAX)
}

// nom, prix and photo are only for display: the API recomputes the price.
function ligneDepuisProduit(produit) {
  return {
    produit_id: produit.id,
    nom: produit.nom,
    prix: produit.prix,
    photo: photoPrincipale(produit.photos)?.url ?? null,
    quantite: 1,
  }
}

export function ajouterLigne(lignes, produit) {
  if (lignes.some((l) => l.produit_id === produit.id)) {
    return lignes.map((l) => (l.produit_id === produit.id ? { ...l, quantite: borner(l.quantite + 1) } : l))
  }
  return [...lignes, ligneDepuisProduit(produit)]
}

export function changerQuantiteLigne(lignes, produitId, quantite) {
  return lignes.map((l) => (l.produit_id === produitId ? { ...l, quantite: borner(quantite) } : l))
}

export function retirerLigne(lignes, produitId) {
  return lignes.filter((l) => l.produit_id !== produitId)
}

export function compterArticles(lignes) {
  return lignes.reduce((somme, l) => somme + l.quantite, 0)
}

export function totalPanier(lignes) {
  return lignes.reduce((somme, l) => somme + Number(l.prix) * l.quantite, 0)
}

// localStorage can hold anything (old format, hand edits): keep it only if it looks right.
export function lignesValides(valeur) {
  if (!Array.isArray(valeur)) return []
  const ok = valeur.every(
    (l) => l && Number.isInteger(l.produit_id) && Number.isInteger(l.quantite) && typeof l.nom === 'string',
  )
  return ok ? valeur : []
}

export function lignesPourApi(lignes) {
  return lignes.map((l) => ({ produit_id: l.produit_id, quantite: l.quantite }))
}
```

- [ ] **Step 4: Run the tests**

Run: `npm test` → all tests pass (the existing `produit` tests plus 6 new ones).

- [ ] **Step 5: Commit**

```powershell
git add src/utils/panier.js src/utils/panier.test.js package.json
git commit -m "feat: add cart rules with node tests"
```

---

### Task 8: `PanierContext`, header badge, "Ajouter au panier"

**Files:**
- Create: `frontend/src/context/PanierContext.jsx`
- Modify: `frontend/src/main.jsx` (provider)
- Modify: `frontend/src/components/Header.jsx`
- Modify: `frontend/src/utils/produit.js` (`ACTIONS`: `code` field)
- Modify: `frontend/src/components/InfosProduit.jsx`
- Modify: `frontend/src/pages/PageFicheProduit.jsx` (`key` on `InfosProduit`)
- Modify: `frontend/src/index.css`

**Interfaces:**
- Consumes: everything from `utils/panier.js` (Task 7).
- Produces: `PanierProvider`, `usePanier()` returning
  `{ lignes, ajouter(produit), changerQuantite(produitId, quantite), retirer(produitId), vider(), nombreArticles, total }`.
  `ajouter`, `changerQuantite`, `retirer` and `vider` keep the same identity between renders
  (Task 10 uses `vider` in a `useEffect`).

- [ ] **Step 1: Create `frontend/src/context/PanierContext.jsx`**

```jsx
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import * as panier from '../utils/panier.js'

const CLE = 'maison-guillard-panier'
const PanierContext = createContext(null)

// Private browsing or blocked storage can make localStorage throw: start empty then.
function lirePanier() {
  try {
    return panier.lignesValides(JSON.parse(localStorage.getItem(CLE)))
  } catch {
    return []
  }
}

export function PanierProvider({ children }) {
  const [lignes, setLignes] = useState(lirePanier)

  useEffect(() => {
    try {
      localStorage.setItem(CLE, JSON.stringify(lignes))
    } catch {
      // Storage unavailable: the cart still works until the page is closed.
    }
  }, [lignes])

  // useCallback with no deps: same function on every render, safe to use in effects.
  const ajouter = useCallback((produit) => setLignes((l) => panier.ajouterLigne(l, produit)), [])
  const changerQuantite = useCallback(
    (produitId, quantite) => setLignes((l) => panier.changerQuantiteLigne(l, produitId, quantite)),
    [],
  )
  const retirer = useCallback((produitId) => setLignes((l) => panier.retirerLigne(l, produitId)), [])
  const vider = useCallback(() => setLignes([]), [])

  const valeur = useMemo(
    () => ({
      lignes,
      ajouter,
      changerQuantite,
      retirer,
      vider,
      nombreArticles: panier.compterArticles(lignes),
      total: panier.totalPanier(lignes),
    }),
    [lignes, ajouter, changerQuantite, retirer, vider],
  )

  return <PanierContext.Provider value={valeur}>{children}</PanierContext.Provider>
}

export function usePanier() {
  const contexte = useContext(PanierContext)
  if (contexte === null) throw new Error('usePanier doit être utilisé dans <PanierProvider>')
  return contexte
}
```

- [ ] **Step 2: Wrap the app — in `frontend/src/main.jsx`**

Add the import:
```jsx
import { PanierProvider } from './context/PanierContext.jsx'
```
and wrap `<BrowserRouter>…</BrowserRouter>`:
```jsx
  <StrictMode>
    <PanierProvider>
      <BrowserRouter>
        {/* routes unchanged */}
      </BrowserRouter>
    </PanierProvider>
  </StrictMode>,
```

- [ ] **Step 3: Header — replace `frontend/src/components/Header.jsx` with**

```jsx
import { Link, NavLink } from 'react-router-dom'
import Logo from './Logo.jsx'
import { usePanier } from '../context/PanierContext.jsx'

export default function Header() {
  const { nombreArticles } = usePanier()
  return (
    <header className="entete">
      <Link to="/" className="entete__logo" aria-label="Maison Guillard, accueil">
        <Logo />
      </Link>
      <nav className="entete__nav" aria-label="Navigation principale">
        <NavLink to="/boutique">Boutique</NavLink>
        <NavLink to="/qui-sommes-nous">Qui sommes-nous</NavLink>
        <NavLink to="/contact">Contact</NavLink>
      </nav>
      <div className="entete__actions">
        <Link
          to="/panier"
          className="bouton bouton--discret"
          aria-label={`Panier, ${nombreArticles} article${nombreArticles > 1 ? 's' : ''}`}
        >
          Panier
          {nombreArticles > 0 && <span className="pastille" aria-hidden="true">{nombreArticles}</span>}
        </Link>
      </div>
    </header>
  )
}
```

- [ ] **Step 4: Give the cart action a code — in `frontend/src/utils/produit.js`, change the `disponible` entry of `ACTIONS`**

```js
  disponible: [
    { libelle: 'Ajouter au panier', principale: true, code: 'panier' },
    { libelle: 'Personnaliser ce modèle', principale: false },
  ],
```
(The existing `actionsFiche` test compares only the `libelle`s, so it still passes.)

- [ ] **Step 5: Enable the button — replace `frontend/src/components/InfosProduit.jsx` with**

```jsx
import { useState } from 'react'
import { Link } from 'react-router-dom'
import MentionDisponibilite from './MentionDisponibilite.jsx'
import { usePanier } from '../context/PanierContext.jsx'
import { actionsFiche, prixAffiche } from '../utils/produit.js'

export default function InfosProduit({ produit }) {
  const { ajouter } = usePanier()
  const [ajoute, setAjoute] = useState(false)

  function ajouterAuPanier() {
    ajouter(produit)
    setAjoute(true)
  }

  return (
    <div className="infos">
      <h1>{produit.nom}</h1>
      <p className="infos__prix">{prixAffiche(produit)}</p>
      <MentionDisponibilite disponibilite={produit.disponibilite} />
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
        {actionsFiche(produit.disponibilite).map((action) =>
          action.code === 'panier' ? (
            <button
              key={action.libelle}
              type="button"
              className="bouton bouton--principal"
              onClick={ajouterAuPanier}
            >
              {action.libelle}
            </button>
          ) : (
            <button
              key={action.libelle}
              type="button"
              className={action.principale ? 'bouton bouton--principal' : 'bouton'}
              disabled
              title="Bientôt disponible"
            >
              {action.libelle}
            </button>
          ),
        )}
      </div>
      {ajoute && (
        <p className="infos__ajoute" role="status">
          Ajouté au panier. <Link to="/panier">Voir le panier</Link>
        </p>
      )}
    </div>
  )
}
```

- [ ] **Step 6: Reset the message when changing product — in `frontend/src/pages/PageFicheProduit.jsx`**

Replace `<InfosProduit produit={produit.data} />` with:
```jsx
            <InfosProduit key={produit.data.id} produit={produit.data} />
```

- [ ] **Step 7: Styles — append to `frontend/src/index.css`**

```css
/* Panier : pastille du header, confirmation d'ajout */
.pastille {
  display: inline-block; min-width: 1.4em; margin-left: .5em; padding: 0 .35em;
  border-radius: 1em; background: var(--couleur-texte); color: var(--couleur-fond);
  font-size: .7rem; line-height: 1.4em; text-align: center; letter-spacing: 0;
}
.infos__ajoute { margin-top: 1rem; color: var(--couleur-texte-doux); }
.infos__ajoute a { color: var(--couleur-texte); }
```

- [ ] **Step 8: Check in the browser**

Run the backend (`uvicorn` on :3000) and `npm run dev` (from `frontend/`). On a `disponible`
fiche: click « Ajouter au panier » twice → the badge shows 2 and the message appears. Reload the
page → the badge still shows 2. On a `sur_commande` fiche the buttons stay disabled.
Run: `npm test` and `npm run lint` → no errors.

- [ ] **Step 9: Commit**

```powershell
git add src/context src/main.jsx src/components/Header.jsx src/components/InfosProduit.jsx src/utils/produit.js src/pages/PageFicheProduit.jsx src/index.css
git commit -m "feat: add cart context, header badge and add-to-cart button"
```

---

### Task 9: Cart page — `PagePanier` and `LigneArticlePanier`

**Files:**
- Create: `frontend/src/components/LigneArticlePanier.jsx`
- Create: `frontend/src/pages/PagePanier.jsx`
- Modify: `frontend/src/main.jsx` (route)
- Modify: `frontend/src/index.css`

**Interfaces:**
- Consumes: `usePanier()` (Task 8), `QUANTITE_MAX` (Task 7), `formatPrix` (`utils/produit.js`).
- Produces: route `/panier`, link to `/commande`.

- [ ] **Step 1: Create `frontend/src/components/LigneArticlePanier.jsx`**

```jsx
import { Link } from 'react-router-dom'
import { QUANTITE_MAX } from '../utils/panier.js'
import { formatPrix } from '../utils/produit.js'

const QUANTITES = Array.from({ length: QUANTITE_MAX }, (_, i) => i + 1)

export default function LigneArticlePanier({ ligne, changerQuantite, retirer }) {
  return (
    <li className="ligne-panier">
      {ligne.photo ? (
        <img src={ligne.photo} alt="" className="ligne-panier__photo" />
      ) : (
        <div className="ligne-panier__photo photo-vide" aria-hidden="true" />
      )}
      <div className="ligne-panier__infos">
        <Link to={`/produits/${ligne.produit_id}`}>{ligne.nom}</Link>
        <span>{formatPrix(ligne.prix)}</span>
      </div>
      <label className="ligne-panier__quantite">
        Quantité
        <select
          value={ligne.quantite}
          onChange={(e) => changerQuantite(ligne.produit_id, e.target.value)}
        >
          {QUANTITES.map((q) => <option key={q} value={q}>{q}</option>)}
        </select>
      </label>
      <span className="ligne-panier__sous-total">{formatPrix(Number(ligne.prix) * ligne.quantite)}</span>
      <button type="button" className="bouton bouton--discret" onClick={() => retirer(ligne.produit_id)}>
        Retirer
      </button>
    </li>
  )
}
```

- [ ] **Step 2: Create `frontend/src/pages/PagePanier.jsx`**

```jsx
import { Link } from 'react-router-dom'
import LigneArticlePanier from '../components/LigneArticlePanier.jsx'
import { usePanier } from '../context/PanierContext.jsx'
import { formatPrix } from '../utils/produit.js'

export default function PagePanier() {
  const { lignes, changerQuantite, retirer, total } = usePanier()

  if (lignes.length === 0) {
    return (
      <section className="etat contenu">
        <h1>Votre panier est vide</h1>
        <Link to="/boutique">Découvrir la boutique</Link>
      </section>
    )
  }

  return (
    <section className="contenu section panier">
      <h1>Votre panier</h1>
      <ul className="panier__lignes">
        {lignes.map((ligne) => (
          <LigneArticlePanier
            key={ligne.produit_id}
            ligne={ligne}
            changerQuantite={changerQuantite}
            retirer={retirer}
          />
        ))}
      </ul>
      <p className="panier__total">Total : <strong>{formatPrix(total)}</strong></p>
      <p className="infos__note">Paiement et livraison convenus avec l'artisan après la commande.</p>
      <Link to="/commande" className="bouton bouton--principal">Passer commande</Link>
    </section>
  )
}
```

- [ ] **Step 3: Add the route — in `frontend/src/main.jsx`**

Import:
```jsx
import PagePanier from './pages/PagePanier.jsx'
```
Add before the `path="*"` route:
```jsx
          <Route path="panier" element={<PagePanier />} />
```

- [ ] **Step 4: Styles — append to `frontend/src/index.css`**

```css
.panier__lignes { list-style: none; margin: 2rem 0; padding: 0; border-top: 1px solid var(--couleur-filet); }
.ligne-panier {
  display: grid; grid-template-columns: 80px 1fr auto auto auto; gap: 1rem; align-items: center;
  padding: 1rem 0; border-bottom: 1px solid var(--couleur-filet);
}
.ligne-panier__photo { width: 80px; height: 80px; object-fit: cover; }
.ligne-panier__infos { display: flex; flex-direction: column; gap: .25rem; }
.ligne-panier__infos a { color: var(--couleur-texte); }
.ligne-panier__quantite { display: flex; gap: .5rem; align-items: center; font-size: .85rem; }
.panier__total { font-size: 1.2rem; text-align: right; }
@media (max-width: 640px) {
  .ligne-panier { grid-template-columns: 64px 1fr; }
  .ligne-panier__photo { width: 64px; height: 64px; }
}
```

- [ ] **Step 5: Check in the browser**

`/panier` with items: change a quantity → sub-total, total and header badge update; « Retirer »
removes the line; removing the last line shows « Votre panier est vide ». Narrow the window to
phone width → each line wraps without horizontal scroll.
Run: `npm run lint` → no errors.

- [ ] **Step 6: Commit**

```powershell
git add src/components/LigneArticlePanier.jsx src/pages/PagePanier.jsx src/main.jsx src/index.css
git commit -m "feat: add cart page"
```

---

### Task 10: Order form and confirmation

**Files:**
- Modify: `frontend/src/api/client.js` (`ApiError.detail`, `apiPost`)
- Create: `frontend/src/api/commandes.js`
- Create: `frontend/src/pages/PageFormulaireCommande.jsx`
- Create: `frontend/src/pages/PageConfirmationCommande.jsx`
- Modify: `frontend/src/main.jsx` (2 routes)
- Modify: `frontend/src/index.css`

**Interfaces:**
- Consumes: `usePanier()` (Task 8), `lignesPourApi` (Task 7), `POST /api/commandes` (Task 4).
- Produces: `apiPost(path, body)`, `ApiError.detail` (French message from the API or `null`),
  `creerCommande(commande)`; routes `/commande` and `/commande/confirmation` (router state
  `{ numero, total }`).

Why the cart is emptied on the confirmation page and not in the form: if the form emptied it, it
would re-render with an empty cart and redirect to `/panier` before React Router finished going to
the confirmation.

- [ ] **Step 1: Replace `frontend/src/api/client.js` with**

```js
export class ApiError extends Error {
  // detail: the API's French message when it sends one as a string, else null.
  constructor(status, message, detail = null) {
    super(message)
    this.status = status
    this.detail = detail
  }
}

export async function apiGet(path) {
  const res = await fetch(`/api${path}`)
  if (!res.ok) {
    throw new ApiError(res.status, `Erreur API ${res.status}`)
  }
  return res.json()
}

export async function apiPost(path, body) {
  const res = await fetch(`/api${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    // Business errors send a string; Pydantic validation errors send a list.
    const detail = typeof data?.detail === 'string' ? data.detail : null
    throw new ApiError(res.status, `Erreur API ${res.status}`, detail)
  }
  return data
}
```

- [ ] **Step 2: Create `frontend/src/api/commandes.js`**

```js
import { apiPost } from './client.js'

export function creerCommande(commande) {
  return apiPost('/commandes', commande)
}
```

- [ ] **Step 3: Create `frontend/src/pages/PageFormulaireCommande.jsx`**

```jsx
import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client.js'
import { creerCommande } from '../api/commandes.js'
import { usePanier } from '../context/PanierContext.jsx'
import { lignesPourApi } from '../utils/panier.js'
import { formatPrix } from '../utils/produit.js'

const CHAMPS_VIDES = { nom_client: '', email: '', telephone: '', adresse: '' }

function messageErreur(erreur) {
  if (!(erreur instanceof ApiError)) return 'Connexion impossible. Vérifiez votre connexion et réessayez.'
  if (erreur.detail) return erreur.detail
  if (erreur.status === 422) return 'Vérifiez les informations saisies.'
  return "La commande n'a pas pu être envoyée. Réessayez dans un instant."
}

export default function PageFormulaireCommande() {
  const { lignes, total } = usePanier()
  const navigate = useNavigate()
  const [champs, setChamps] = useState(CHAMPS_VIDES)
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState(null)

  if (lignes.length === 0) return <Navigate to="/panier" replace />

  function changer(e) {
    setChamps({ ...champs, [e.target.name]: e.target.value })
  }

  async function envoyer(e) {
    e.preventDefault()
    setEnvoi(true)
    setErreur(null)
    try {
      const commande = await creerCommande({
        ...champs,
        telephone: champs.telephone.trim() || null,
        lignes: lignesPourApi(lignes),
      })
      navigate('/commande/confirmation', {
        replace: true,
        state: { numero: commande.id, total: commande.total },
      })
    } catch (err) {
      setErreur(messageErreur(err))
      setEnvoi(false)
    }
  }

  return (
    <section className="contenu section deux-colonnes commande">
      <form className="formulaire" onSubmit={envoyer}>
        <h1>Vos coordonnées</h1>
        <label>
          Nom et prénom
          <input name="nom_client" value={champs.nom_client} onChange={changer} required maxLength={100} autoComplete="name" />
        </label>
        <label>
          E-mail
          <input name="email" type="email" value={champs.email} onChange={changer} required autoComplete="email" />
        </label>
        <label>
          Téléphone (facultatif)
          <input name="telephone" type="tel" value={champs.telephone} onChange={changer} maxLength={30} autoComplete="tel" />
        </label>
        <label>
          Adresse de livraison
          <textarea name="adresse" value={champs.adresse} onChange={changer} required maxLength={300} rows={3} autoComplete="street-address" />
        </label>
        {erreur && <p className="message-erreur" role="alert">{erreur}</p>}
        <button type="submit" className="bouton bouton--principal" disabled={envoi}>
          {envoi ? 'Envoi…' : 'Confirmer la commande'}
        </button>
        <p className="infos__note">Aucun paiement en ligne : Maison Guillard vous contacte pour le paiement et la livraison.</p>
      </form>
      <aside className="recapitulatif">
        <h2>Récapitulatif</h2>
        <ul>
          {lignes.map((l) => (
            <li key={l.produit_id}>
              <span>{l.nom} × {l.quantite}</span>
              <span>{formatPrix(Number(l.prix) * l.quantite)}</span>
            </li>
          ))}
        </ul>
        <p className="panier__total">Total : <strong>{formatPrix(total)}</strong></p>
        <Link to="/panier">Modifier le panier</Link>
      </aside>
    </section>
  )
}
```

- [ ] **Step 4: Create `frontend/src/pages/PageConfirmationCommande.jsx`**

```jsx
import { useEffect } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { usePanier } from '../context/PanierContext.jsx'
import { formatPrix } from '../utils/produit.js'

export default function PageConfirmationCommande() {
  const { state } = useLocation()
  const { vider } = usePanier()
  const numero = state?.numero

  // The order is saved: the cart can be emptied now (see the plan note in Task 10).
  useEffect(() => {
    if (numero) vider()
  }, [numero, vider])

  if (!numero) return <Navigate to="/" replace />

  return (
    <section className="etat contenu">
      <p className="surtitre">Merci</p>
      <h1>Commande n°{numero} reçue</h1>
      <p>Montant : {formatPrix(state.total)}</p>
      <p>Maison Guillard vous contacte sous 48 h pour le paiement et la livraison.</p>
      <Link to="/boutique">Retour à la boutique</Link>
    </section>
  )
}
```

- [ ] **Step 5: Add the routes — in `frontend/src/main.jsx`**

Imports:
```jsx
import PageConfirmationCommande from './pages/PageConfirmationCommande.jsx'
import PageFormulaireCommande from './pages/PageFormulaireCommande.jsx'
```
After the `panier` route:
```jsx
          <Route path="commande" element={<PageFormulaireCommande />} />
          <Route path="commande/confirmation" element={<PageConfirmationCommande />} />
```

- [ ] **Step 6: Styles — append to `frontend/src/index.css`**

```css
.formulaire { display: flex; flex-direction: column; gap: 1.2rem; }
.formulaire label { display: flex; flex-direction: column; gap: .4rem; font-size: .85rem; }
.formulaire input, .formulaire textarea {
  padding: .7rem; border: 1px solid var(--couleur-filet); background: var(--couleur-surface);
  color: var(--couleur-texte); font: inherit;
}
.formulaire input:focus, .formulaire textarea:focus { outline: 1px solid var(--couleur-texte); }
.formulaire .bouton { align-self: flex-start; }
.message-erreur { color: var(--couleur-erreur); }
.recapitulatif ul { list-style: none; padding: 0; }
.recapitulatif li { display: flex; justify-content: space-between; gap: 1rem; padding: .5rem 0; border-bottom: 1px solid var(--couleur-filet); }
```

- [ ] **Step 7: Check in the browser**

1. Cart with 2 products → « Passer commande » → fill the form → « Confirmer la commande » →
   confirmation « Commande n°X reçue » with the total; header badge back to 0.
2. Open `/commande/confirmation` directly → redirected to `/`.
3. Open `/commande` with an empty cart → redirected to `/panier`.
4. Put a product in the cart, switch it to `rupture` in Swagger (`PUT /api/produits/{id}`), send
   the order → message « « Nom » n'est plus disponible », cart unchanged.
5. Stop the backend, send the order → « Connexion impossible… » (Vite's proxy answers 500 or
   502 here: the message is then « La commande n'a pas pu être envoyée… », also acceptable).

Run: `npm test` and `npm run lint` → no errors.

- [ ] **Step 8: Commit**

```powershell
git add src/api src/pages/PageFormulaireCommande.jsx src/pages/PageConfirmationCommande.jsx src/main.jsx src/index.css
git commit -m "feat: add order form and confirmation page"
```

---

### Task 11: Full manual test with a real email, docs

**Files:**
- Create: `docs/2026-10-XX-s7-resume.md` (date of the day it is written)
- Modify: `docs/outils.html` (new tools: `email-validator`, `smtplib` + Gmail SMTP)
- Modify: `docs/tests-api.md` (Commandes and Paramètres scenarios)

- [ ] **Step 1: Real email check**

1. Swagger → Authorize → `PUT /api/parametres` with `{"email_commande_actif": true}`.
2. Pass an order from the site with your own email as the customer email.
3. Expected: two emails in your Gmail inbox (« Nouvelle commande n°X » and « Maison Guillard :
   commande n°X reçue »), within a minute.
4. `PUT /api/parametres` with `false`, pass another order → no email.

- [ ] **Step 2: Docs**

- `docs/tests-api.md`: add the `POST /api/commandes` (201, 422 unavailable, 422 invalid body) and
  `GET`/`PUT /api/parametres` (200, 401) scenarios, same table format as the existing ones.
- `docs/outils.html`: add `email-validator` and `smtplib` / Gmail SMTP (what it is, why it is used
  here), same card format as the existing tools.
- `docs/2026-10-XX-s7-resume.md`: what was built, decisions taken with the cousin (no stock,
  offline payment, optional emails), errors met during the block, and the « À adapter au
  déploiement » list copied from the spec.

- [ ] **Step 3: Final checks and commit**

```powershell
cd backend; .\.venv\Scripts\python.exe -m pytest -q; cd ..\frontend; npm test; npm run lint; cd ..
git add docs
git commit -m "docs: add S7 summary, API test scenarios and new tools"
```
Expected: all tests pass, lint clean.
