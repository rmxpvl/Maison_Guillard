# S5 — Produit/Catégorie/Photo Back-office CRUD Implementation Plan

**Goal:** Ship the S5 back-office slice — admin CRUD for produits and catégories, plus photo
attachment with a single "principale" photo per produit — matching the plan de route's Semaine 5
objective: "Back-office : CRUD produits, gestion des catégories et des photographies."

**Architecture:** Same layered pattern as S4 (auth): router → Pydantic schema → service (business
logic, unit-testable with a mocked DB session) → SQLAlchemy model. Three new domains: `categorie`,
`produit`, `photo`. Admin-write routes reuse the existing `require_admin` dependency unchanged;
read routes (`GET /produits`, `GET /produits/:id`, `GET /categories`) stay public. Photo upload is
stubbed: instead of calling the real Cloudinary API, `photo_service.upload_to_cloudinary` saves the
file to a local `backend/uploads/` directory and returns a locally-served URL, served back via
FastAPI's `StaticFiles`.

**Tech Stack:** Python 3.14.4, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic, pytest + FastAPI
`TestClient`, PostgreSQL 16 (docker-compose, already running from S4).

**Spec:** `docs/specs/2026-09-22-s5-produit-categorie-photo-design.md`

## Global Constraints

- Python 3.14.4 as the floor (matches S4).
- Conventional Commits format for every commit (`feat:`, `fix:`, `docs:`, `chore:`, `test:`,
  `refactor:`).
- Work happens on a new branch `feature/s5-produit-categorie-photo`, created in Task 1 Step 1 from
  `main` (S4 is merged there and verified working — 14/14 tests passing as of 2026-09-22).
- No secrets committed: `.env` stays gitignored (already the case from S4).
- `backend/uploads/` (where the photo stub writes files) must be gitignored — never commit uploaded
  files.
- Cloudinary is stubbed for this plan — no real Cloudinary account/SDK/credentials involved. See
  Task 6.
- Exactly one `principale` photo per produit at a time; no auto-principale on first upload — the
  admin always sets it explicitly via `PATCH /photos/:id/principale`.
- Deleting a `categorie` still referenced by a `produit` must fail with a 409, never cascade-delete
  produits.
- Merging this branch back into `main` (Task 8, final step) is a merge to a shared/long-lived
  branch — stop and get explicit go-ahead from the project owner before running it, per the
  established norm from S4.

---

### Task 1: SQLAlchemy models (Categorie, Produit, Photo) + Alembic migration

**Files:**
- Create: `backend/app/models/categorie.py`
- Create: `backend/app/models/produit.py`
- Create: `backend/app/models/photo.py`
- Modify: `backend/app/models/__init__.py` (export the three new models)
- Modify: `backend/alembic/env.py` (import the new models so autogenerate sees them)
- Create: `backend/alembic/versions/` (populated by `alembic revision` in Step 5)

**Interfaces:**
- Consumes: `Base` from `app/database.py` (S4).
- Produces: `app.models.categorie.Categorie` (`id`, `nom`, `slug`), `app.models.produit.Produit`
  (`id`, `nom`, `description`, `categorie_id`, `prix`, `dimensions`, `disponibilite`, `created_at`)
  and `app.models.produit.Disponibilite` (a `str, enum.Enum` with members `disponible`, `rupture`,
  `sur_commande`), `app.models.photo.Photo` (`id`, `produit_id`, `url`, `ordre`, `principale`) — all
  later tasks import these exact names.

- [ ] **Step 1: Create the feature branch**

```bash
git checkout main
git pull origin main
git checkout -b feature/s5-produit-categorie-photo
```

- [ ] **Step 2: Create `backend/app/models/categorie.py`**

```python
from sqlalchemy import Column, Integer, String

from app.database import Base


class Categorie(Base):
    __tablename__ = "categorie"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
```

- [ ] **Step 3: Create `backend/app/models/produit.py`**

```python
import enum

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Enum as SqlEnum
from sqlalchemy.sql import func

from app.database import Base


class Disponibilite(str, enum.Enum):
    disponible = "disponible"
    rupture = "rupture"
    sur_commande = "sur_commande"


class Produit(Base):
    __tablename__ = "produit"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    description = Column(String, nullable=False)
    categorie_id = Column(Integer, ForeignKey("categorie.id"), nullable=False)
    prix = Column(Numeric(10, 2), nullable=False)
    dimensions = Column(String, nullable=False)
    disponibilite = Column(
        SqlEnum(Disponibilite, name="disponibilite_enum"), nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 4: Create `backend/app/models/photo.py`**

```python
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from app.database import Base


class Photo(Base):
    __tablename__ = "photo"

    id = Column(Integer, primary_key=True, index=True)
    produit_id = Column(
        Integer, ForeignKey("produit.id", ondelete="CASCADE"), nullable=False
    )
    url = Column(String, nullable=False)
    ordre = Column(Integer, nullable=False, default=0)
    principale = Column(Boolean, nullable=False, default=False)
```

- [ ] **Step 5: Update `backend/app/models/__init__.py`**

```python
from app.models.admin import Admin
from app.models.categorie import Categorie
from app.models.produit import Produit, Disponibilite
from app.models.photo import Photo

__all__ = ["Admin", "Categorie", "Produit", "Disponibilite", "Photo"]
```

- [ ] **Step 6: Update `backend/alembic/env.py` import line**

Find this line (added during S4):

```python
from app.models import Admin  # noqa: F401 — import so Base.metadata sees the table
```

Replace it with:

```python
from app.models import Admin, Categorie, Produit, Photo  # noqa: F401 — import so Base.metadata sees the tables
```

- [ ] **Step 7: Generate and apply the migration (dev database)**

Run (from `backend/`, venv activated): `alembic revision --autogenerate -m "add categorie produit photo tables"`
Expected: writes a new file under `backend/alembic/versions/` containing three `op.create_table(...)`
calls (`categorie`, `produit`, `photo`) and the enum type creation.

Run: `alembic upgrade head`
Expected: "Running upgrade <prev> -> <revision>, add categorie produit photo tables" with no errors.

- [ ] **Step 8: Apply the same migration to the test database**

```bash
DATABASE_URL="$TEST_DATABASE_URL" alembic upgrade head
```

(Read `TEST_DATABASE_URL` from `backend/.env` if your shell doesn't export it automatically.)

- [ ] **Step 9: Verify the tables exist**

Run: `docker compose exec postgres psql -U maison -d maison_guillard -c '\d produit'`
Expected: shows the `produit` table with columns `id, nom, description, categorie_id, prix,
dimensions, disponibilite, created_at`.

- [ ] **Step 10: Commit**

```bash
git add backend/app/models backend/alembic
git commit -m "feat: add categorie, produit, and photo models with migration"
```

---

### Task 2: `categorie_service` (unit tests, DB session mocked)

**Files:**
- Create: `backend/app/services/categorie_service.py`
- Test: `backend/tests/unit/test_categorie_service.py`

**Interfaces:**
- Consumes: `Categorie` model (Task 1), `Produit` model (Task 1, for the in-use check).
- Produces: `categorie_service.get_all(db: Session) -> list[Categorie]`,
  `categorie_service.create(db: Session, data: dict) -> Categorie`,
  `categorie_service.delete(db: Session, categorie_id: int) -> bool` (returns `False` if the
  category doesn't exist, raises `categorie_service.CategorieEnUsageError` if a `Produit` still
  references it, otherwise deletes and returns `True`). Task 3's router calls these exact names.

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/unit/test_categorie_service.py
from unittest.mock import MagicMock

import pytest

from app.services import categorie_service


def test_get_all_returns_categories_from_query():
    db = MagicMock()
    db.query.return_value.all.return_value = ["cat1", "cat2"]

    result = categorie_service.get_all(db)

    assert result == ["cat1", "cat2"]


def test_create_adds_and_commits_a_new_categorie():
    db = MagicMock()

    categorie = categorie_service.create(db, {"nom": "Tables", "slug": "tables"})

    assert categorie.nom == "Tables"
    assert categorie.slug == "tables"
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_delete_returns_false_when_categorie_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = categorie_service.delete(db, 999)

    assert result is False


def test_delete_raises_when_categorie_still_used_by_a_produit():
    db = MagicMock()
    categorie = MagicMock(id=1)
    # first .filter().first() call (fetch the categorie) returns the categorie,
    # second one (check for a referencing produit) returns a produit
    db.query.return_value.filter.return_value.first.side_effect = [categorie, MagicMock()]

    with pytest.raises(categorie_service.CategorieEnUsageError):
        categorie_service.delete(db, 1)


def test_delete_removes_categorie_when_unused():
    db = MagicMock()
    categorie = MagicMock(id=1)
    db.query.return_value.filter.return_value.first.side_effect = [categorie, None]

    result = categorie_service.delete(db, 1)

    assert result is True
    db.delete.assert_called_once_with(categorie)
    db.commit.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_categorie_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.categorie_service'`

- [ ] **Step 3: Create `backend/app/services/categorie_service.py`**

```python
from sqlalchemy.orm import Session

from app.models.categorie import Categorie
from app.models.produit import Produit


class CategorieEnUsageError(Exception):
    """Raised when deleting a category still referenced by at least one produit."""


def get_all(db: Session) -> list[Categorie]:
    return db.query(Categorie).all()


def create(db: Session, data: dict) -> Categorie:
    categorie = Categorie(**data)
    db.add(categorie)
    db.commit()
    db.refresh(categorie)
    return categorie


def delete(db: Session, categorie_id: int) -> bool:
    categorie = db.query(Categorie).filter(Categorie.id == categorie_id).first()
    if categorie is None:
        return False

    in_use = (
        db.query(Produit).filter(Produit.categorie_id == categorie_id).first()
        is not None
    )
    if in_use:
        raise CategorieEnUsageError()

    db.delete(categorie)
    db.commit()
    return True
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_categorie_service.py -v`
Expected: PASS (all 5 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/categorie_service.py backend/tests/unit/test_categorie_service.py
git commit -m "feat: add categorie_service with in-use delete guard"
```

---

### Task 3: Categories router (integration tests, real test DB)

**Files:**
- Create: `backend/app/schemas/categorie.py`
- Create: `backend/app/routers/categories.py`
- Modify: `backend/app/main.py` (mount the categories router)
- Test: `backend/tests/integration/test_categories_routes.py`

**Interfaces:**
- Consumes: `categorie_service.get_all`, `categorie_service.create`, `categorie_service.delete`,
  `categorie_service.CategorieEnUsageError` (Task 2); `get_db` (S4); `require_admin` (S4).
- Produces: `GET /api/categories`, `POST /api/categories`, `DELETE /api/categories/:id` mounted and
  working end-to-end. Nothing later depends on names from this task beyond the routes themselves.

- [ ] **Step 1: Create `backend/app/schemas/categorie.py`**

```python
from pydantic import BaseModel


class CategorieCreate(BaseModel):
    nom: str
    slug: str


class CategorieOut(BaseModel):
    id: int
    nom: str
    slug: str

    class Config:
        from_attributes = True
```

- [ ] **Step 2: Create `backend/app/routers/categories.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_admin import require_admin
from app.schemas.categorie import CategorieCreate, CategorieOut
from app.services import categorie_service

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategorieOut])
def list_categories(db: Session = Depends(get_db)):
    return categorie_service.get_all(db)


@router.post("", response_model=CategorieOut, status_code=201)
def create_categorie(
    payload: CategorieCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    return categorie_service.create(db, payload.model_dump())


@router.delete("/{categorie_id}", status_code=204)
def delete_categorie(
    categorie_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    try:
        deleted = categorie_service.delete(db, categorie_id)
    except categorie_service.CategorieEnUsageError:
        raise HTTPException(status_code=409, detail="Catégorie utilisée par des produits")
    if not deleted:
        raise HTTPException(status_code=404, detail="Catégorie introuvable")
```

- [ ] **Step 3: Mount the router in `backend/app/main.py`**

Find:

```python
from app.routers import auth

app = FastAPI(title="Maison Guillard API")

app.include_router(auth.router)
```

Replace with:

```python
from app.routers import auth, categories

app = FastAPI(title="Maison Guillard API")

app.include_router(auth.router)
app.include_router(categories.router)
```

- [ ] **Step 4: Write the failing tests**

```python
# backend/tests/integration/test_categories_routes.py
import os

os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie
from app.models.produit import Produit, Disponibilite
from app.services import auth_service

client = TestClient(app)


def _admin_token(db):
    db.query(Admin).delete()
    db.commit()
    admin = Admin(
        email="admin@test.com",
        password_hash=auth_service.hash_password("test-password-123"),
    )
    db.add(admin)
    db.commit()
    return auth_service.login(db, "admin@test.com", "test-password-123")


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    db.query(Produit).delete()
    db.query(Categorie).delete()
    db.query(Admin).delete()
    db.commit()
    yield db
    db.query(Produit).delete()
    db.query(Categorie).delete()
    db.query(Admin).delete()
    db.commit()
    db.close()


def test_list_categories_returns_empty_list_initially(clean_db):
    res = client.get("/api/categories")
    assert res.status_code == 200
    assert res.json() == []


def test_create_categorie_requires_admin(clean_db):
    res = client.post("/api/categories", json={"nom": "Tables", "slug": "tables"})
    assert res.status_code == 401


def test_create_categorie_succeeds_with_admin_token(clean_db):
    token = _admin_token(clean_db)

    res = client.post(
        "/api/categories",
        json={"nom": "Tables", "slug": "tables"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 201
    assert res.json()["slug"] == "tables"


def test_delete_categorie_returns_404_when_not_found(clean_db):
    token = _admin_token(clean_db)

    res = client.delete(
        "/api/categories/999", headers={"Authorization": f"Bearer {token}"}
    )

    assert res.status_code == 404


def test_delete_categorie_returns_409_when_used_by_a_produit(clean_db):
    db = clean_db
    token = _admin_token(db)

    categorie = Categorie(nom="Tables", slug="tables")
    db.add(categorie)
    db.commit()
    db.refresh(categorie)

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

    res = client.delete(
        f"/api/categories/{categorie.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 409


def test_delete_categorie_succeeds_when_unused(clean_db):
    db = clean_db
    token = _admin_token(db)

    categorie = Categorie(nom="Chaises", slug="chaises")
    db.add(categorie)
    db.commit()
    db.refresh(categorie)

    res = client.delete(
        f"/api/categories/{categorie.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 204
```

- [ ] **Step 5: Run tests to verify they fail**

Run: `pytest tests/integration/test_categories_routes.py -v`
Expected: FAIL — collection error or 404s before the router is wired.

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/integration/test_categories_routes.py -v`
Expected: PASS (all 6 tests)

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/categorie.py backend/app/routers/categories.py backend/app/main.py backend/tests/integration/test_categories_routes.py
git commit -m "feat: add categories router with admin create/delete and 409 in-use guard"
```

---

### Task 4: `produit_service` (unit tests, DB session mocked)

**Files:**
- Create: `backend/app/services/produit_service.py`
- Test: `backend/tests/unit/test_produit_service.py`

**Interfaces:**
- Consumes: `Produit` model, `Disponibilite` enum (Task 1).
- Produces: `produit_service.get_all(db, categorie_id=None, disponibilite=None) -> list[Produit]`,
  `produit_service.get_by_id(db, produit_id: int) -> Produit | None`,
  `produit_service.create(db, data: dict) -> Produit`,
  `produit_service.update(db, produit_id: int, data: dict) -> Produit | None` (only overwrites
  fields present and non-`None` in `data` — a true partial update), `produit_service.delete(db,
  produit_id: int) -> bool`. Task 5's router calls these exact names.

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/unit/test_produit_service.py
from unittest.mock import MagicMock

from app.services import produit_service
from app.models.produit import Disponibilite


def test_create_adds_and_commits_a_new_produit():
    db = MagicMock()

    produit = produit_service.create(
        db,
        {
            "nom": "Table basse",
            "description": "En chêne",
            "categorie_id": 1,
            "prix": 199.99,
            "dimensions": "120x60x40cm",
            "disponibilite": Disponibilite.disponible,
        },
    )

    assert produit.nom == "Table basse"
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_get_by_id_returns_none_when_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = produit_service.get_by_id(db, 999)

    assert result is None


def test_update_returns_none_when_produit_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = produit_service.update(db, 999, {"nom": "Nouveau nom"})

    assert result is None


def test_update_only_overwrites_fields_present_in_data():
    db = MagicMock()
    existing = MagicMock(nom="Ancien nom", prix=100)
    db.query.return_value.filter.return_value.first.return_value = existing

    produit_service.update(db, 1, {"nom": "Nouveau nom", "prix": None})

    assert existing.nom == "Nouveau nom"
    assert existing.prix == 100  # untouched: None means "not provided"
    db.commit.assert_called_once()


def test_delete_returns_false_when_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = produit_service.delete(db, 999)

    assert result is False


def test_delete_returns_true_and_removes_when_found():
    db = MagicMock()
    produit = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = produit

    result = produit_service.delete(db, 1)

    assert result is True
    db.delete.assert_called_once_with(produit)
    db.commit.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_produit_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.produit_service'`

- [ ] **Step 3: Create `backend/app/services/produit_service.py`**

```python
from sqlalchemy.orm import Session

from app.models.produit import Produit


def get_all(
    db: Session, categorie_id: int | None = None, disponibilite: str | None = None
) -> list[Produit]:
    query = db.query(Produit)
    if categorie_id is not None:
        query = query.filter(Produit.categorie_id == categorie_id)
    if disponibilite is not None:
        query = query.filter(Produit.disponibilite == disponibilite)
    return query.all()


def get_by_id(db: Session, produit_id: int) -> Produit | None:
    return db.query(Produit).filter(Produit.id == produit_id).first()


def create(db: Session, data: dict) -> Produit:
    produit = Produit(**data)
    db.add(produit)
    db.commit()
    db.refresh(produit)
    return produit


def update(db: Session, produit_id: int, data: dict) -> Produit | None:
    produit = get_by_id(db, produit_id)
    if produit is None:
        return None

    for key, value in data.items():
        if value is not None:
            setattr(produit, key, value)

    db.commit()
    db.refresh(produit)
    return produit


def delete(db: Session, produit_id: int) -> bool:
    produit = get_by_id(db, produit_id)
    if produit is None:
        return False

    db.delete(produit)
    db.commit()
    return True
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_produit_service.py -v`
Expected: PASS (all 6 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/produit_service.py backend/tests/unit/test_produit_service.py
git commit -m "feat: add produit_service with filtered listing and partial update"
```

---

### Task 5: Produits router (integration tests, real test DB)

**Files:**
- Create: `backend/app/schemas/produit.py`
- Create: `backend/app/routers/produits.py`
- Modify: `backend/app/main.py` (mount the produits router)
- Test: `backend/tests/integration/test_produits_routes.py`

**Interfaces:**
- Consumes: `produit_service.*` (Task 4); `categorie_service` only indirectly (a valid
  `categorie_id` is required by the FK — tests create one first); `get_db`, `require_admin` (S4).
- Produces: `GET /api/produits`, `GET /api/produits/:id`, `POST /api/produits`, `PUT
  /api/produits/:id`, `DELETE /api/produits/:id` mounted and working end-to-end. `router` (the
  `APIRouter` instance, prefix `/api/produits`) is imported and extended by Task 7 to add the photo
  upload endpoint on the same prefix.

- [ ] **Step 1: Create `backend/app/schemas/produit.py`**

```python
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from app.models.produit import Disponibilite


class ProduitCreate(BaseModel):
    nom: str
    description: str
    categorie_id: int
    prix: Decimal
    dimensions: str
    disponibilite: Disponibilite


class ProduitUpdate(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    categorie_id: Optional[int] = None
    prix: Optional[Decimal] = None
    dimensions: Optional[str] = None
    disponibilite: Optional[Disponibilite] = None


class ProduitOut(BaseModel):
    id: int
    nom: str
    description: str
    categorie_id: int
    prix: Decimal
    dimensions: str
    disponibilite: Disponibilite

    class Config:
        from_attributes = True
```

- [ ] **Step 2: Create `backend/app/routers/produits.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_admin import require_admin
from app.schemas.produit import ProduitCreate, ProduitOut, ProduitUpdate
from app.services import produit_service

router = APIRouter(prefix="/api/produits", tags=["produits"])


@router.get("", response_model=list[ProduitOut])
def list_produits(
    categorie: int | None = None,
    disponibilite: str | None = None,
    db: Session = Depends(get_db),
):
    return produit_service.get_all(db, categorie_id=categorie, disponibilite=disponibilite)


@router.get("/{produit_id}", response_model=ProduitOut)
def get_produit(produit_id: int, db: Session = Depends(get_db)):
    produit = produit_service.get_by_id(db, produit_id)
    if produit is None:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    return produit


@router.post("", response_model=ProduitOut, status_code=201)
def create_produit(
    payload: ProduitCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    return produit_service.create(db, payload.model_dump())


@router.put("/{produit_id}", response_model=ProduitOut)
def update_produit(
    produit_id: int,
    payload: ProduitUpdate,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    produit = produit_service.update(db, produit_id, payload.model_dump())
    if produit is None:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    return produit


@router.delete("/{produit_id}", status_code=204)
def delete_produit(
    produit_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    deleted = produit_service.delete(db, produit_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Produit introuvable")
```

- [ ] **Step 3: Mount the router in `backend/app/main.py`**

Find:

```python
from app.routers import auth, categories

app = FastAPI(title="Maison Guillard API")

app.include_router(auth.router)
app.include_router(categories.router)
```

Replace with:

```python
from app.routers import auth, categories, produits

app = FastAPI(title="Maison Guillard API")

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(produits.router)
```

- [ ] **Step 4: Write the failing tests**

```python
# backend/tests/integration/test_produits_routes.py
import os

os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie
from app.models.produit import Produit, Disponibilite
from app.services import auth_service

client = TestClient(app)


def _admin_token(db):
    db.query(Admin).delete()
    db.commit()
    admin = Admin(
        email="admin@test.com",
        password_hash=auth_service.hash_password("test-password-123"),
    )
    db.add(admin)
    db.commit()
    return auth_service.login(db, "admin@test.com", "test-password-123")


def _make_categorie(db, nom="Tables", slug="tables"):
    categorie = Categorie(nom=nom, slug=slug)
    db.add(categorie)
    db.commit()
    db.refresh(categorie)
    return categorie


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    db.query(Produit).delete()
    db.query(Categorie).delete()
    db.query(Admin).delete()
    db.commit()
    yield db
    db.query(Produit).delete()
    db.query(Categorie).delete()
    db.query(Admin).delete()
    db.commit()
    db.close()


def test_create_produit_requires_admin(clean_db):
    categorie = _make_categorie(clean_db)

    res = client.post(
        "/api/produits",
        json={
            "nom": "Table basse",
            "description": "En chêne",
            "categorie_id": categorie.id,
            "prix": "199.99",
            "dimensions": "120x60x40cm",
            "disponibilite": "disponible",
        },
    )

    assert res.status_code == 401


def test_create_and_get_produit(clean_db):
    token = _admin_token(clean_db)
    categorie = _make_categorie(clean_db)

    create_res = client.post(
        "/api/produits",
        json={
            "nom": "Table basse",
            "description": "En chêne",
            "categorie_id": categorie.id,
            "prix": "199.99",
            "dimensions": "120x60x40cm",
            "disponibilite": "disponible",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_res.status_code == 201
    produit_id = create_res.json()["id"]

    get_res = client.get(f"/api/produits/{produit_id}")
    assert get_res.status_code == 200
    assert get_res.json()["nom"] == "Table basse"


def test_get_produit_returns_404_when_not_found(clean_db):
    res = client.get("/api/produits/999")
    assert res.status_code == 404


def test_list_produits_filters_by_categorie(clean_db):
    db = clean_db
    token = _admin_token(db)
    cat_tables = _make_categorie(db, "Tables", "tables")
    cat_chaises = _make_categorie(db, "Chaises", "chaises")

    for nom, cat in [("Table basse", cat_tables), ("Chaise haute", cat_chaises)]:
        client.post(
            "/api/produits",
            json={
                "nom": nom,
                "description": "desc",
                "categorie_id": cat.id,
                "prix": "50.00",
                "dimensions": "10x10x10cm",
                "disponibilite": "disponible",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    res = client.get(f"/api/produits?categorie={cat_tables.id}")
    assert res.status_code == 200
    noms = [p["nom"] for p in res.json()]
    assert noms == ["Table basse"]


def test_update_produit_partial_fields(clean_db):
    db = clean_db
    token = _admin_token(db)
    categorie = _make_categorie(db)

    create_res = client.post(
        "/api/produits",
        json={
            "nom": "Table basse",
            "description": "En chêne",
            "categorie_id": categorie.id,
            "prix": "199.99",
            "dimensions": "120x60x40cm",
            "disponibilite": "disponible",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    produit_id = create_res.json()["id"]

    update_res = client.put(
        f"/api/produits/{produit_id}",
        json={"disponibilite": "rupture"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert update_res.status_code == 200
    assert update_res.json()["disponibilite"] == "rupture"
    assert update_res.json()["nom"] == "Table basse"  # untouched


def test_delete_produit(clean_db):
    db = clean_db
    token = _admin_token(db)
    categorie = _make_categorie(db)

    create_res = client.post(
        "/api/produits",
        json={
            "nom": "Table basse",
            "description": "En chêne",
            "categorie_id": categorie.id,
            "prix": "199.99",
            "dimensions": "120x60x40cm",
            "disponibilite": "disponible",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    produit_id = create_res.json()["id"]

    delete_res = client.delete(
        f"/api/produits/{produit_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_res.status_code == 204

    get_res = client.get(f"/api/produits/{produit_id}")
    assert get_res.status_code == 404
```

- [ ] **Step 5: Run tests to verify they fail**

Run: `pytest tests/integration/test_produits_routes.py -v`
Expected: FAIL before the router is wired (collection error or connection refused on `/api/produits`).

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/integration/test_produits_routes.py -v`
Expected: PASS (all 6 tests)

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/produit.py backend/app/routers/produits.py backend/app/main.py backend/tests/integration/test_produits_routes.py
git commit -m "feat: add produits router with filtered listing, partial update, and admin guards"
```

---

### Task 6: `photo_service` (stub upload, unit tests with DB session mocked)

**Files:**
- Create: `backend/app/services/photo_service.py`
- Test: `backend/tests/unit/test_photo_service.py`
- Modify: `backend/.gitignore` (ignore the local upload directory)

**Interfaces:**
- Consumes: `Photo` model (Task 1); a FastAPI `UploadFile` (Task 7 passes one in from the request).
- Produces: `photo_service.upload_to_cloudinary(fichier: UploadFile) -> str` (stub: saves the file
  under `backend/uploads/` with a random filename, returns a `http://localhost:<PORT>/uploads/...`
  URL — same signature a real Cloudinary integration would have, so swapping it later only touches
  this function), `photo_service.attach_to_produit(db, produit_id: int, url: str, ordre: int = 0) ->
  Photo`, `photo_service.delete(db, photo_id: int) -> bool`, `photo_service.set_principale(db,
  photo_id: int) -> Photo | None` (un-sets any other `principale=True` photo for the same
  `produit_id` in the same transaction). Task 7's router calls these exact names.

- [ ] **Step 1: Update `backend/.gitignore`**

Add a line:

```
uploads/
```

- [ ] **Step 2: Write the failing tests**

```python
# backend/tests/unit/test_photo_service.py
import io
from unittest.mock import MagicMock

from fastapi import UploadFile

from app.services import photo_service


def test_upload_to_cloudinary_saves_file_and_returns_local_url(tmp_path, monkeypatch):
    monkeypatch.setattr(photo_service, "UPLOAD_DIR", tmp_path)
    fichier = UploadFile(filename="chaise.jpg", file=io.BytesIO(b"fake-image-bytes"))

    url = photo_service.upload_to_cloudinary(fichier)

    assert url.startswith("http://localhost:")
    assert "/uploads/" in url
    saved_files = list(tmp_path.iterdir())
    assert len(saved_files) == 1
    assert saved_files[0].read_bytes() == b"fake-image-bytes"


def test_attach_to_produit_creates_a_photo():
    db = MagicMock()

    photo = photo_service.attach_to_produit(db, produit_id=1, url="http://x/y.jpg", ordre=2)

    assert photo.produit_id == 1
    assert photo.url == "http://x/y.jpg"
    assert photo.ordre == 2
    assert photo.principale is False
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_delete_returns_false_when_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = photo_service.delete(db, 999)

    assert result is False


def test_delete_returns_true_when_found():
    db = MagicMock()
    photo = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = photo

    result = photo_service.delete(db, 1)

    assert result is True
    db.delete.assert_called_once_with(photo)


def test_set_principale_returns_none_when_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = photo_service.set_principale(db, 999)

    assert result is None


def test_set_principale_unsets_other_photos_for_same_produit():
    db = MagicMock()
    photo = MagicMock(id=5, produit_id=1)
    db.query.return_value.filter.return_value.first.return_value = photo

    result = photo_service.set_principale(db, 5)

    assert result is photo
    assert photo.principale is True
    # the bulk-unset query ran against the same produit_id
    update_call = db.query.return_value.filter.return_value.update
    update_call.assert_called_once_with({"principale": False}, synchronize_session=False)
    db.commit.assert_called_once()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/unit/test_photo_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.photo_service'`

- [ ] **Step 4: Create `backend/app/services/photo_service.py`**

```python
import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.photo import Photo

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


def upload_to_cloudinary(fichier: UploadFile) -> str:
    """Stub: saves the file locally instead of calling the real Cloudinary API.
    Keeps the same shape (takes a file, returns a URL) a real integration would
    have, so swapping this out later touches only this function."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(fichier.filename).suffix
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / unique_name

    with dest.open("wb") as out:
        out.write(fichier.file.read())

    port = os.environ.get("PORT", "3000")
    return f"http://localhost:{port}/uploads/{unique_name}"


def attach_to_produit(db: Session, produit_id: int, url: str, ordre: int = 0) -> Photo:
    photo = Photo(produit_id=produit_id, url=url, ordre=ordre, principale=False)
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


def delete(db: Session, photo_id: int) -> bool:
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if photo is None:
        return False

    db.delete(photo)
    db.commit()
    return True


def set_principale(db: Session, photo_id: int) -> Photo | None:
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if photo is None:
        return None

    db.query(Photo).filter(Photo.produit_id == photo.produit_id).update(
        {"principale": False}, synchronize_session=False
    )
    photo.principale = True
    db.commit()
    db.refresh(photo)
    return photo
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/test_photo_service.py -v`
Expected: PASS (all 6 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/photo_service.py backend/tests/unit/test_photo_service.py backend/.gitignore
git commit -m "feat: add photo_service with local-disk upload stub and single-principale invariant"
```

---

### Task 7: Photo endpoints + static file serving (integration tests, real upload)

**Files:**
- Create: `backend/app/schemas/photo.py`
- Modify: `backend/app/routers/produits.py` (add the photo upload endpoint on the existing
  `router`, and a second `photos_router` for the two `/api/photos/:id...` endpoints)
- Modify: `backend/app/main.py` (mount `photos_router`, mount `StaticFiles` at `/uploads`)
- Test: `backend/tests/integration/test_photo_routes.py`

**Interfaces:**
- Consumes: `photo_service.*` (Task 6); `produit_service.get_by_id` (Task 4, to 404 early if the
  produit doesn't exist); `get_db`, `require_admin` (S4).
- Produces: `POST /api/produits/:id/photos`, `PATCH /api/photos/:id/principale`, `DELETE
  /api/photos/:id` mounted and working end-to-end, including files actually served back from
  `/uploads/<filename>`.

- [ ] **Step 1: Create `backend/app/schemas/photo.py`**

```python
from pydantic import BaseModel


class PhotoOut(BaseModel):
    id: int
    produit_id: int
    url: str
    ordre: int
    principale: bool

    class Config:
        from_attributes = True
```

- [ ] **Step 2: Add the photo endpoints to `backend/app/routers/produits.py`**

Add these imports at the top (alongside the existing ones):

```python
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.require_admin import require_admin
from app.schemas.photo import PhotoOut
from app.schemas.produit import ProduitCreate, ProduitOut, ProduitUpdate
from app.services import photo_service, produit_service
```

(This replaces the Task 5 import block — same names plus `File`, `Form`, `UploadFile`,
`app.schemas.photo.PhotoOut`, `app.services.photo_service`.)

Append at the end of the file, after the existing `delete_produit` route, still using the same
`router`:

```python
@router.post("/{produit_id}/photos", response_model=PhotoOut, status_code=201)
def add_photo(
    produit_id: int,
    fichier: UploadFile = File(...),
    ordre: int = Form(0),
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    produit = produit_service.get_by_id(db, produit_id)
    if produit is None:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    url = photo_service.upload_to_cloudinary(fichier)
    return photo_service.attach_to_produit(db, produit_id, url, ordre)


photos_router = APIRouter(prefix="/api/photos", tags=["photos"])


@photos_router.patch("/{photo_id}/principale", response_model=PhotoOut)
def set_photo_principale(
    photo_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    photo = photo_service.set_principale(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo introuvable")
    return photo


@photos_router.delete("/{photo_id}", status_code=204)
def delete_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    deleted = photo_service.delete(db, photo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Photo introuvable")
```

- [ ] **Step 3: Mount `photos_router` and the `/uploads` static files in `backend/app/main.py`**

Find:

```python
from app.routers import auth, categories, produits

app = FastAPI(title="Maison Guillard API")

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(produits.router)
```

Replace with:

```python
from fastapi.staticfiles import StaticFiles

from app.routers import auth, categories, produits
from app.services.photo_service import UPLOAD_DIR

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Maison Guillard API")

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(produits.router)
app.include_router(produits.photos_router)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
```

- [ ] **Step 4: Write the failing tests**

```python
# backend/tests/integration/test_photo_routes.py
import io
import os

os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.admin import Admin
from app.models.categorie import Categorie
from app.models.photo import Photo
from app.models.produit import Produit, Disponibilite
from app.services import auth_service

client = TestClient(app)


def _admin_token(db):
    db.query(Admin).delete()
    db.commit()
    admin = Admin(
        email="admin@test.com",
        password_hash=auth_service.hash_password("test-password-123"),
    )
    db.add(admin)
    db.commit()
    return auth_service.login(db, "admin@test.com", "test-password-123")


def _make_produit(db):
    categorie = Categorie(nom="Tables", slug="tables")
    db.add(categorie)
    db.commit()
    db.refresh(categorie)

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
    return produit


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    db.query(Photo).delete()
    db.query(Produit).delete()
    db.query(Categorie).delete()
    db.query(Admin).delete()
    db.commit()
    yield db
    db.query(Photo).delete()
    db.query(Produit).delete()
    db.query(Categorie).delete()
    db.query(Admin).delete()
    db.commit()
    db.close()


def test_add_photo_uploads_file_and_serves_it_back(clean_db):
    db = clean_db
    token = _admin_token(db)
    produit = _make_produit(db)

    res = client.post(
        f"/api/produits/{produit.id}/photos",
        files={"fichier": ("chaise.jpg", io.BytesIO(b"fake-image-bytes"), "image/jpeg")},
        data={"ordre": "1"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 201
    body = res.json()
    assert body["produit_id"] == produit.id
    assert body["principale"] is False

    served = client.get(body["url"].replace("http://localhost:3000", ""))
    assert served.status_code == 200
    assert served.content == b"fake-image-bytes"


def test_add_photo_returns_404_for_unknown_produit(clean_db):
    token = _admin_token(clean_db)

    res = client.post(
        "/api/produits/999/photos",
        files={"fichier": ("chaise.jpg", io.BytesIO(b"x"), "image/jpeg")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 404


def test_set_principale_unsets_previous_principale(clean_db):
    db = clean_db
    token = _admin_token(db)
    produit = _make_produit(db)
    headers = {"Authorization": f"Bearer {token}"}

    first = client.post(
        f"/api/produits/{produit.id}/photos",
        files={"fichier": ("a.jpg", io.BytesIO(b"a"), "image/jpeg")},
        headers=headers,
    ).json()
    second = client.post(
        f"/api/produits/{produit.id}/photos",
        files={"fichier": ("b.jpg", io.BytesIO(b"b"), "image/jpeg")},
        headers=headers,
    ).json()

    client.patch(f"/api/photos/{first['id']}/principale", headers=headers)
    res = client.patch(f"/api/photos/{second['id']}/principale", headers=headers)

    assert res.status_code == 200
    assert res.json()["principale"] is True

    first_after = db.query(Photo).filter(Photo.id == first["id"]).first()
    assert first_after.principale is False


def test_delete_photo(clean_db):
    db = clean_db
    token = _admin_token(db)
    produit = _make_produit(db)
    headers = {"Authorization": f"Bearer {token}"}

    photo = client.post(
        f"/api/produits/{produit.id}/photos",
        files={"fichier": ("a.jpg", io.BytesIO(b"a"), "image/jpeg")},
        headers=headers,
    ).json()

    res = client.delete(f"/api/photos/{photo['id']}", headers=headers)
    assert res.status_code == 204

    remaining = db.query(Photo).filter(Photo.id == photo["id"]).first()
    assert remaining is None
```

- [ ] **Step 5: Run tests to verify they fail**

Run: `pytest tests/integration/test_photo_routes.py -v`
Expected: FAIL before the endpoints/static mount exist (404s or connection errors).

- [ ] **Step 6: Run the full test suite to verify everything passes**

Run (from `backend/`, venv activated): `pytest -v`
Expected: PASS — every test across S4's files plus this plan's `test_categorie_service.py`,
`test_categories_routes.py`, `test_produit_service.py`, `test_produits_routes.py`,
`test_photo_service.py`, `test_photo_routes.py`.

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/photo.py backend/app/routers/produits.py backend/app/main.py backend/tests/integration/test_photo_routes.py
git commit -m "feat: add photo upload, principale toggle, and delete endpoints with static serving"
```

---

### Task 8: Docs and merge to `main`

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: nothing new.
- Produces: nothing consumed by later tasks — this is the wrap-up task for S5.

- [ ] **Step 1: Add an S5 section to `README.md`**

Append, after the existing "Tests" section:

```markdown
## S5 — Back-office produits/catégories/photos

New endpoints under `/api/produits`, `/api/categories`, `/api/photos` — see
`docs/specs/2026-09-22-s5-produit-categorie-photo-design.md` for the full design.

Photo uploads are stubbed: files are saved locally under `backend/uploads/` (gitignored) and served
back at `http://localhost:3000/uploads/<filename>` instead of going to a real Cloudinary account.
Swap `photo_service.upload_to_cloudinary` for the real SDK call when Cloudinary credentials exist —
its signature (`upload_to_cloudinary(fichier) -> url`) doesn't need to change.
```

- [ ] **Step 2: Run the full backend test suite one last time**

Run (from `backend/`, venv activated): `pytest -v`
Expected: PASS, all tests.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document S5 back-office endpoints and photo upload stub"
```

- [ ] **Step 4: Merge into `main`**

This is a merge to a shared/long-lived branch. **Stop here and get explicit go-ahead from the
project owner before running the commands below** — do not run them automatically.

```bash
git checkout main
git pull origin main
git merge --no-ff feature/s5-produit-categorie-photo -m "merge: S5 produit/categorie/photo back-office"
git push origin main
```
