# Maison Guillard — Commandes utiles

Aide-mémoire des commandes du projet (PowerShell, Windows). Sauf mention contraire, les commandes
se lancent depuis le dossier racine `Maison_Guillard`.

## Ce qui doit tourner

| Quoi | Où le lancer | Port | Vérifier que ça marche |
|---|---|---|---|
| Base PostgreSQL | Docker | 5432 | `docker compose ps` affiche `healthy` |
| API FastAPI | **Terminal 1** (uvicorn) | 3000 | http://localhost:3000/api/health |
| Site React | **Terminal 2** (`npm run dev`) | 5173 | http://localhost:5173 |

Un terminal ne fait tourner **qu'un serveur à la fois** : il faut deux terminaux ouverts en même
temps (dans VS Code, bouton **+** du panneau Terminal).

---

## Démarrer le projet

```powershell
# 1. Base de données (une fois, elle reste allumée)
docker compose up -d

# 2. Terminal 1 — API
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 3000

# 3. Terminal 2 — site
cd frontend
npm run dev
```

Arrêter un serveur : cliquer dans son terminal puis **Ctrl+C**.
Arrêter la base : `docker compose down` (les données sont conservées).

## Adresses

| Page | Adresse |
|---|---|
| Site | http://localhost:5173 |
| Swagger (documentation et test de l'API) | http://localhost:3000/docs |
| API, exemple | http://localhost:3000/api/produits |
| L'API vue à travers le site (proxy Vite) | http://localhost:5173/api/produits |

---

## Backend (dossier `backend`)

```powershell
cd backend

# Activer le venv (une fois par terminal) ; ensuite "python" suffit
.\.venv\Scripts\Activate.ps1

# Sans activer le venv, préfixer par le Python du projet :
.\.venv\Scripts\python.exe <commande>

# Installer les dépendances
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Mettre la base à jour (migrations Alembic)
.\.venv\Scripts\python.exe -m alembic upgrade head

# Créer le compte admin (lit SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD dans .env)
.\.venv\Scripts\python.exe seed.py

# Créer le catalogue de démo + ses photos (relançable sans doublon)
.\.venv\Scripts\python.exe seed_catalogue.py
```

### Tests backend

```powershell
cd backend

.\.venv\Scripts\python.exe -m pytest -v                    # tous les tests
.\.venv\Scripts\python.exe -m pytest -q                    # résumé court
.\.venv\Scripts\python.exe -m pytest tests/integration/test_securite_et_erreurs.py -v   # un fichier
.\.venv\Scripts\python.exe -m pytest -v -k forged          # les tests dont le nom contient "forged"
```

Docker doit tourner : les tests utilisent la base `maison_guillard_test`.

---

## Frontend (dossier `frontend`)

```powershell
cd frontend

npm install        # installer les dépendances (après un clone ou un changement de package.json)
npm run dev        # serveur de développement, port 5173
npm test           # tests des règles d'affichage (node --test)
npm run lint       # analyse du code (oxlint)
npm run build      # version optimisée pour la mise en ligne (dossier dist/)
npm run preview    # servir le build localement, port 4173
```

---

## Tester l'API dans Swagger

1. Ouvrir http://localhost:3000/docs.
2. `POST /api/auth/login` → **Try it out** → corps :
   ```json
   { "email": "<SEED_ADMIN_EMAIL>", "motDePasse": "<SEED_ADMIN_PASSWORD>" }
   ```
   → **Execute** → dans **Response body**, copier la valeur de `token` (sans les guillemets).
3. Bouton **Authorize** en haut → coller le jeton → **Authorize** → **Close**.
4. Les routes 🔒 sont maintenant utilisables (Try it out → Execute).

Scénarios complets et résultats attendus : `docs/tests-api.md`.

---

## Git

```powershell
git status                          # fichiers modifiés, branche courante
git branch --show-current           # nom de la branche
git log --oneline -10               # 10 derniers commits
git switch main                     # aller sur main
git pull                            # récupérer les changements de GitHub
git switch -c Branche-xxx           # créer une branche et y aller
git add <fichier>                   # préparer un fichier pour le commit
git commit -m "feat: ..."           # enregistrer
git push -u origin Branche-xxx      # envoyer la branche sur GitHub (1re fois)
gh pr create --base main            # ouvrir une Pull Request
gh pr view 4                        # voir l'état d'une PR
```

Avant de changer de branche : arrêter `npm run dev`. Sinon Vite peut redémarrer pendant que les
fichiers changent et perdre sa configuration (voir Dépannage).

---

## Base de données (Docker)

```powershell
docker compose ps                   # état du conteneur
docker compose logs postgres        # journaux de PostgreSQL

# Ouvrir une console SQL sur la base de développement
docker compose exec postgres psql -U maison -d maison_guillard

# Exemples de requêtes dans cette console (quitter avec \q) :
#   \dt                         liste des tables
#   SELECT id, nom, prix FROM produit;
#   SELECT id, email FROM admin;
```

---

## Dépannage

| Symptôme | Cause probable | Solution |
|---|---|---|
| Le site affiche « Impossible de charger les données » | L'API est arrêtée | Relancer uvicorn (Terminal 1) |
| Le terminal de Vite affiche `http proxy error ... ECONNREFUSED` | L'API est arrêtée | Relancer uvicorn (Terminal 1) |
| http://localhost:5173/api/produits affiche la page du site au lieu de JSON | Vite a perdu sa config (proxy) | Ctrl+C puis `npm run dev` |
| Page blanche sur le site | Erreur JavaScript ou cache de Vite | Lire la console du navigateur (F12) et le terminal de Vite ; sinon Ctrl+C puis `npm run dev`, et recharger avec **Ctrl+Maj+R** |
| `POST /api/auth/login` répond 401 avec le mot de passe du `.env` | Le mot de passe a changé dans `.env` après la création de l'admin (`seed.py` ne modifie jamais un admin existant) | Remettre l'ancien mot de passe, ou recréer l'admin : `docker compose exec postgres psql -U maison -d maison_guillard -c "DELETE FROM admin;"` puis `cd backend` et `.\.venv\Scripts\python.exe seed.py` |
| `Address already in use` / port 3000 ou 5173 déjà pris | Un ancien serveur tourne encore | Trouver le processus : `netstat -ano \| findstr :3000` (dernier nombre = PID), puis `Stop-Process -Id <PID>` |
| Les tests échouent tous avec une erreur de connexion | Docker / PostgreSQL arrêté | `docker compose up -d` |
| `.\venv\...` introuvable | Le dossier s'appelle `.venv` (avec un point) | `.\.venv\Scripts\python.exe ...` |
