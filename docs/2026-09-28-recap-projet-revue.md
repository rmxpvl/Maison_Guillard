# Maison Guillard — Récapitulatif du projet (préparation manual review)

> Document de préparation pour expliquer le projet à l'oral. Couvre tout ce qui a été fait jusqu'au
> 2026-09-28 : cadrage, S4 (auth admin), S5 (back-office produits/catégories/photos). Sources
> détaillées : `docs/specs/`, `docs/plans/`, `docs/2026-09-23-s5-resume.md`.

## 1. Le projet en une minute

**Maison Guillard** : application web pour un artisan menuisier — présenter et vendre ses meubles
faits main. Deux parcours client : achat direct (panier → commande) et demande de devis
(formulaire → suivi par l'artisan). Un seul compte administrateur (l'artisan lui-même) gère le
catalogue via un back-office. Pas de compte client dans le MVP (achat/devis en mode invité).

Projet de formation solo, 9 semaines (21 août → 21 octobre 2026), méthode MVP-first :
catalogue + back-office avant parcours client, achat direct avant devis.

## 2. Stack technique et son historique

**Stack actuelle** : Python 3.14 / FastAPI (API REST) / SQLAlchemy 2.x + Alembic (ORM +
migrations) / PostgreSQL 16 (docker-compose) / JWT + bcrypt (auth) / React + Vite (frontend, pas
encore démarré).

**Point important à savoir expliquer** : le projet a démarré sur Node.js/Express/Prisma, puis a
basculé sur Python/FastAPI/SQLAlchemy **en cours de S4** (décision personnelle assumée, documentée
dans le commit `2341dbf refactor: switch backend stack from Node/Express/Prisma to
Python/FastAPI/SQLAlchemy` et dans la doc technique révisée le 14 septembre). Le premier scaffold
Node a été abandonné avant d'aller plus loin — pas de code Node qui traîne dans le projet actuel.

## 3. Architecture générale

Trois couches, toujours dans cet ordre pour chaque fonctionnalité :

```
Requête HTTP
   ↓
Router (app/routers/*.py)      — reçoit la requête, valide via un schema, appelle le service
   ↓
Service (app/services/*.py)    — logique métier pure, ne connaît rien à HTTP
   ↓
Modèle SQLAlchemy (app/models/*.py) — structure de la table en base
   ↓
PostgreSQL
```

**Pourquoi cette séparation (question probable à l'oral)** : chaque couche a une responsabilité
unique et peut être testée isolément. Le service ne sait rien de qui l'appelle (HTTP, script,
tâche planifiée) — la règle métier "on ne supprime pas une catégorie encore utilisée" par exemple
vit uniquement dans `categorie_service.py`, testée sans même démarrer un serveur.

Deux autres couches transverses :
- **Schemas Pydantic** (`app/schemas/*.py`) — valident automatiquement les données entrantes (JSON
  du client) et contrôlent la forme des données sortantes. Si un champ manque ou a le mauvais type,
  FastAPI répond `422` avant même que le code métier s'exécute.
- **Dependencies** (`app/dependencies/`) — `require_admin` vérifie le token JWT et bloque avec
  `401` les routes protégées, injecté via `Depends(require_admin)` dans la signature d'une route.

## 4. S4 — Initialisation du projet et authentification admin

Objectif de la semaine (plan de route) : *"Initialiser le projet (backend, base de données,
squelette frontend) ; authentification et autorisation administrateur."*

Ce qui a été construit :
- `docker-compose.yml` — Postgres local, un service, healthcheck.
- Squelette FastAPI (`app/main.py`) avec `GET /api/health`.
- Modèle `Admin` (id, email, password_hash, created_at) + première migration Alembic.
- `auth_service.py` :
  - `hash_password` / `verify_password` — bcrypt, jamais de mot de passe en clair stocké.
  - `login(db, email, password)` — vérifie les identifiants, renvoie un JWT signé (`HS256`,
    expire après 8h) ou lève `InvalidCredentialsError`.
  - `verify_token(token)` — décode et valide un JWT.
- `require_admin` — dépendance FastAPI, lit le header `Authorization: Bearer <token>`, renvoie
  `401` si absent/invalide.
- `POST /api/auth/login` — `{email, motDePasse}` → `200 {token}` ou `401`.
- Script `seed.py` — crée le compte admin depuis des variables d'environnement (jamais de mot de
  passe en dur dans le code).
- Tests : 14 (unitaires sur `auth_service` avec DB simulée + intégration sur la route login avec
  vraie base de test).

**Angle sécurité à mentionner à l'oral** : bcrypt (hachage + salage automatique, résistant au
brute-force contrairement à un simple SHA256), JWT stateless (pas de session côté serveur à
gérer/protéger), secrets jamais commités (`.env` gitignored, `.env.example` documente les
variables sans valeurs réelles), expiration du token limitée dans le temps.

## 5. S5 — Back-office : produits, catégories, photos

Objectif de la semaine : *"Back-office : CRUD produits, gestion des catégories et des
photographies."*

### Catégories (`/api/categories`)
- Modèle : id, nom, slug unique.
- `GET` public (liste), `POST`/`DELETE` admin.
- Règle métier : suppression refusée (`409`) si un produit référence encore la catégorie —
  empêche de casser l'intégrité référentielle du catalogue par accident.

### Produits (`/api/produits`)
- Modèle : nom, description, catégorie (clé étrangère), prix, dimensions, disponibilité (valeur
  parmi `disponible` / `rupture` / `sur_commande` — type énuméré, impossible d'insérer autre chose
  en base), date de création.
- `GET` (liste filtrable par catégorie/disponibilité, détail par id) publics.
- `POST`/`PUT`/`DELETE` admin. Le `PUT` accepte une **mise à jour partielle** — envoyer seulement
  `{"disponibilite": "rupture"}` ne touche à rien d'autre (logique : chaque champ du schema
  d'update est optionnel, le service ne modifie que les champs non-`None`).

### Photos (`/api/produits/:id/photos`, `/api/photos/:id`)
- Modèle : url, ordre d'affichage, indicateur "principale", produit lié (suppression en cascade —
  supprimer un produit supprime ses photos automatiquement).
- Upload multipart (`POST /api/produits/:id/photos`), suppression, et bascule de la photo
  principale (`PATCH /api/photos/:id/principale` — désactive automatiquement l'ancienne
  principale, jamais deux en même temps).
- **Décision assumée à expliquer** : l'intégration Cloudinary prévue au cadrage est **stubbée**
  (pas de compte disponible actuellement). Le fichier est sauvegardé localement
  (`backend/uploads/`, gitignored) et servi par FastAPI (`StaticFiles` monté sur `/uploads`). La
  fonction `upload_to_cloudinary(fichier) -> url` garde la même signature qu'aurait la vraie
  intégration — un futur remplacement ne touche qu'une seule fonction.

Tests S5 : 33 nouveaux (unitaires par service + intégration par router, y compris un test qui fait
un vrai upload de fichier et revérifie qu'il est bien servi ensuite).

**Total actuel : 47 tests, tous passants.**

## 6. Méthode de travail (utile si on te demande "comment tu as procédé")

Pour chaque semaine du plan de route :
1. **Spec** écrite d'abord (`docs/specs/`) — décisions de design, schéma de données,
   endpoints, en s'appuyant sur la doc technique du cadrage initial.
2. **Plan d'implémentation** détaillé (`docs/plans/`) — découpé en tâches, chacune en
   TDD (test écrit et vérifié en échec avant le code, code minimal pour le faire passer).
3. Exécution tâche par tâche, un commit Git par tâche (Conventional Commits : `feat:`, `fix:`,
   `docs:`, `chore:`, `test:`), une branche par semaine (`feature/s4-init`,
   `feature/s5-produit-categorie-photo`).
4. Merge vers `main` seulement après validation manuelle de la semaine (jamais de commit direct
   sur `main` pendant le développement de la fonctionnalité).

## 7. État Git actuel

- `main` : S4 complet + docs S5 (spec/plan), **pas encore le code S5**.
- `feature/s5-produit-categorie-photo` (poussée sur GitHub sous `Branche-S5`) : S4 + S5 complet,
  47/47 tests, **pas encore mergée dans `main`** — en attente de relecture avant merge.

## 8. Questions probables et pistes de réponse

- **"Pourquoi avoir changé de stack en cours de route ?"** → décision personnelle assumée, pas de
  regret : Python/FastAPI offre validation native (Pydantic), documentation API auto-générée
  (`/docs`), écosystème confortable pour continuer seul sur le reste du projet.
- **"Pourquoi les photos ne vont pas vraiment sur Cloudinary ?"** → pas de compte disponible
  actuellement ; le code est conçu pour que le remplacement soit une seule fonction à changer, pas
  une réécriture.
- **"Comment tu garantis que seul l'admin peut modifier le catalogue ?"** → dépendance
  `require_admin` sur chaque route d'écriture, vérifie un JWT signé avec un secret côté serveur ;
  les routes de lecture (`GET`) restent volontairement publiques pour le catalogue visible par
  tous.
- **"Comment tu testes sans dépendre d'une vraie base à chaque fois ?"** → deux niveaux : tests
  unitaires avec une session de base simulée (`MagicMock`) pour la logique pure, tests
  d'intégration avec une vraie base Postgres de test (séparée de la base de dev) pour vérifier le
  comportement HTTP réel de bout en bout.
- **"Qu'est-ce qui reste à faire ?"** → merge S5 → `main`, puis S6 (site public : catalogue,
  fiches produits, navigation par catégorie), S7 (achat direct), S8 (devis + validation/sécurité
  approfondie), S9 (tests finaux, responsive, clôture).

## 9. Limites connues (à ne pas cacher si on te le demande)

- Cloudinary stubbé (voir plus haut).
- Pas d'endpoint `PUT /categories/:id` (modification d'une catégorie existante) — seulement
  création/suppression, cohérent avec la table d'endpoints de la doc technique qui ne le liste pas.
- Frontend pas encore démarré (prévu à partir de S6).
- Paiement en ligne hors périmètre MVP (évalué seulement après le jalon S8 si le temps le permet).
