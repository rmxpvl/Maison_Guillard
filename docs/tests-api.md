# Maison Guillard — Tests manuels de l'API

**Date de test :** 2026-10-13
**Commit :** `cc5e3ce` (branche `Branche-tests-api`)
**Environnement :** Windows 11, Python 3.14, PostgreSQL 16 (Docker), API lancée avec
`uvicorn app.main:app --reload --port 3000` sur la base de développement seedée
(`seed.py` + `seed_catalogue.py`). Toutes les requêtes ont été envoyées en HTTP réel à l'API en
cours d'exécution, pas via `TestClient`.

**Couverture automatisée :** `backend/tests/`, **80 tests** (`python -m pytest -v`), dont 16 tests de
sécurité qui vérifient que les 8 routes administrateur refusent une requête sans jeton ou avec un
jeton falsifié (`tests/integration/test_securite_et_erreurs.py`). Ce document couvre les mêmes
parcours **à la main**, de bout en bout, comme seconde vérification indépendante. Il sert aussi de
script de démonstration.

**Résultat global : 30 vérifications, 30 PASS.** Les données créées pendant le test (catégorie
`test-qa`, « Produit QA » et sa photo) ont été supprimées à la fin : la base est revenue à son état
initial (12 produits, 4 catégories).

---

## Comment rejouer ces tests dans Swagger

1. Lancer la base (`docker compose up -d`) puis l'API (voir `README.md`).
2. Ouvrir **http://localhost:3000/docs**.
3. Pour chaque route : la déplier → **Try it out** → remplir les paramètres ou le corps → **Execute**
   → lire **Server response** (code et corps de la réponse).
4. Pour les routes marquées 🔒 : se connecter via `POST /api/auth/login`, copier la valeur de
   `token` (sans les guillemets), cliquer sur **Authorize** en haut de la page, la coller, puis
   **Authorize** et **Close**. Swagger ajoute alors l'en-tête `Authorization: Bearer <jeton>` à
   chaque requête.

---

## 1. L'API répond

| Requête | Attendu | Obtenu | Résultat |
|---|---|---|---|
| `GET /api/health` | 200 `{"status": "ok"}` | 200 `{"status": "ok"}` | **PASS** |

## 2. Catégories (public)

| Requête | Attendu | Obtenu | Résultat |
|---|---|---|---|
| `GET /api/categories` | 200, liste | 200, 4 catégories | **PASS** |

## 3. Catalogue et filtres (public)

| Requête | Attendu | Obtenu | Résultat |
|---|---|---|---|
| `GET /api/produits` | 200, liste | 200, 12 produits | **PASS** |
| `GET /api/produits?categorie=<id de « tabourets »>` | 200, filtrée | 200, 3 produits | **PASS** |
| `GET /api/produits?disponibilite=sur_commande` | 200, filtrée | 200, 4 produits | **PASS** |

## 4. Fiche d'un produit avec ses photos (public)

| Requête | Attendu | Obtenu | Résultat |
|---|---|---|---|
| `GET /api/produits/<id du Tabouret Trapèze>` | 200, photos triées par `ordre` | 200, 3 photos, principale = ordre 0 | **PASS** |

## 5. Erreurs sur les routes publiques

| Requête | Attendu | Obtenu | Résultat |
|---|---|---|---|
| `GET /api/produits/999999` | 404 | 404 `{"detail": "Produit introuvable"}` | **PASS** |
| `GET /api/produits?disponibilite=foo` | 422 (valeur hors liste) | 422 | **PASS** |

## 6. Protection des routes administrateur

| Requête | Attendu | Obtenu | Résultat |
|---|---|---|---|
| `POST /api/categories` **sans** jeton | 401 | 401 `{"detail": "Unauthorized"}` | **PASS** |
| `POST /api/categories` avec un jeton **inventé** | 401 | 401 `{"detail": "Unauthorized"}` | **PASS** |

## 7. Connexion de l'administrateur

| Requête | Attendu | Obtenu | Résultat |
|---|---|---|---|
| `POST /api/auth/login`, mauvais mot de passe | 401 | 401 `{"detail": "Identifiants invalides"}` | **PASS** |
| `POST /api/auth/login`, bons identifiants | 200 + `token` | 200, jeton reçu (commence par `eyJ`) | **PASS** |
| `GET /api/health/protected-check` 🔒 | 200 | 200 | **PASS** |

## 8. Gestion des catégories 🔒

| Requête | Attendu | Obtenu | Résultat |
|---|---|---|---|
| `POST /api/categories` `{"nom": "Test QA", "slug": "test-qa"}` | 201 | 201 `{"id": 11, "nom": "Test QA", "slug": "test-qa"}` | **PASS** |
| Même requête avec le slug `test-qa` déjà pris | 409 | 409 `{"detail": "Slug déjà utilisé"}` | **PASS** |

## 9. Création d'un produit 🔒

| Requête | Attendu | Obtenu | Résultat |
|---|---|---|---|
| `POST /api/produits` (« Produit QA », catégorie `test-qa`) | 201 | 201, `photos: []` | **PASS** |
| `POST /api/produits` avec `categorie_id: 999999` | 422 | 422 `{"detail": "Catégorie introuvable"}` | **PASS** |

Corps utilisé :
```json
{
  "nom": "Produit QA",
  "description": "Créé pendant le test manuel",
  "categorie_id": 11,
  "prix": "99.00",
  "dimensions": "10x10x10cm",
  "disponibilite": "disponible"
}
```

## 10. Modification partielle d'un produit 🔒

| Requête | Attendu | Obtenu | Résultat |
|---|---|---|---|
| `PUT /api/produits/<id>` avec seulement `{"prix": "120.00"}` | 200, seul le prix change | 200, prix = 120.00, nom inchangé | **PASS** |
| `PUT /api/produits/999999` | 404 | 404 | **PASS** |

## 11. Photos 🔒

| Requête | Attendu | Obtenu | Résultat |
|---|---|---|---|
| `POST /api/produits/<id>/photos` (fichier PNG, `ordre` = 0) | 201 + `url` | 201, URL sous `/uploads/` | **PASS** |
| Ouvrir l'`url` renvoyée | 200, l'image s'affiche | 200 | **PASS** |
| `PATCH /api/photos/<id>/principale` | 200, `principale: true` | 200, `principale: true` | **PASS** |

Dans Swagger, le champ `fichier` affiche un bouton **Choisir un fichier**.

## 12. Règle métier : catégorie utilisée

| Requête | Attendu | Obtenu | Résultat |
|---|---|---|---|
| `DELETE /api/categories/<id de test-qa>` alors qu'elle contient « Produit QA » | 409 | 409 `{"detail": "Catégorie utilisée par des produits"}` | **PASS** |

## 13. Suppressions et nettoyage 🔒

| Requête | Attendu | Obtenu | Résultat |
|---|---|---|---|
| `DELETE /api/photos/<id>` | 204 | 204 | **PASS** |
| Même suppression une seconde fois | 404 | 404 | **PASS** |
| `DELETE /api/produits/<id>` | 204 | 204 | **PASS** |
| `GET /api/produits/<id>` après suppression | 404 | 404 | **PASS** |
| `DELETE /api/categories/<id de test-qa>`, désormais vide | 204 | 204 | **PASS** |

## 14. Retour à l'état initial

| Vérification | Attendu | Obtenu | Résultat |
|---|---|---|---|
| Nombre de produits | 12 | 12 | **PASS** |
| Nombre de catégories | 4 | 4 | **PASS** |

---

## Limites connues (constatées, non corrigées à cette date)

Ces cas ne provoquent **pas** d'erreur aujourd'hui, alors qu'ils le devraient. Ils relèvent de la
validation des données, prévue dans un lot ultérieur :

- un produit peut être créé avec un **prix négatif ou nul** ;
- un produit peut être créé avec un **nom vide** (`""`) ;
- un **slug** de catégorie peut contenir des majuscules ou des espaces (`"Test"` accepté), alors
  qu'il sert dans l'URL de la boutique (`/boutique/<slug>`).

---

## Scénario court pour une démonstration (environ 5 minutes)

1. `GET /api/produits` : le catalogue est public.
2. `POST /api/categories` sans être connecté → **401** : l'écriture est protégée.
3. `POST /api/auth/login` → copier le jeton → **Authorize**.
4. `POST /api/categories` → **201**, puis la même requête → **409** (slug unique).
5. `POST /api/produits` dans cette catégorie → **201**.
6. `DELETE /api/categories/<id>` → **409** : on ne supprime pas une catégorie qui contient des
   produits.
7. `DELETE /api/produits/<id>`, puis `DELETE /api/categories/<id>` → **204**, **204** : la base
   est propre.
