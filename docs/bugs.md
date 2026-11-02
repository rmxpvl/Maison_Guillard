# Maison Guillard — Suivi des bugs

> Registre des bugs trouvés pendant le développement, avec leur cause, leur correction et le commit
> qui les corrige. Projet solo : les bugs ont été notés dans les résumés de sprint
> (`docs/2026-…-resume.md`) et dans le rapport de tests manuels (`docs/tests-api.md`), puis
> rassemblés ici.

**Gravité** : 🔴 bloquant (erreur 500, perte de données, faille) · 🟠 majeur (mauvais comportement
visible) · 🟡 mineur (confort, affichage, outillage).

**Comment un bug est-il trouvé ?** Par un test automatisé, un test manuel (Swagger ou navigateur),
une relecture du code ou du diff, ou une capture d'écran.

## Bilan

| | Nombre |
|---|---|
| Bugs enregistrés | 27 |
| Corrigés | 21 |
| Ouverts (connus, documentés) | 6, dont aucun bloquant pour le MVP |
| Bugs 🔴 bloquants | 6, tous corrigés |

## Bugs corrigés

| ID | Sprint | Gravité | Problème | Cause | Correction | Trouvé par | Commit |
|---|---|---|---|---|---|---|---|
| B01 | S4 | 🟡 | `require_admin` rangé dans le mauvais dossier, routes d'auth sans test d'intégration | Structure du plan pas respectée | Déplacé dans `app/dependencies/`, tests d'intégration ajoutés | relecture | `6e961a1` |
| B02 | S5 | 🟡 | Un fichier de test échoue quand on le lance seul | `load_dotenv()` oublié : les variables d'environnement n'étaient pas chargées | Chargement des variables ajouté | test lancé seul | pendant S5 |
| B03 | S5 | 🟠 | L'upload de photo plante au démarrage | `python-multipart`, nécessaire aux formulaires de fichiers, manquait dans `requirements.txt` | Dépendance ajoutée | test d'intégration | `8c5de42` |
| B04 | S5 | 🔴 | Créer une catégorie avec un slug déjà pris → **500** | L'erreur d'unicité de PostgreSQL n'était pas interceptée | Le service lève une erreur métier, la route répond **409** | relecture de S5 | `fade960` |
| B05 | S5 | 🔴 | Créer un produit avec une catégorie inexistante → **500** | Violation de clé étrangère non interceptée | Vérification de la catégorie, réponse **422** | relecture de S5 | `6ed3ea7` |
| B06 | S5 | 🔴 | Un filtre `?disponibilite=foo` → **500** | Paramètre typé `str` : la valeur brute arrivait à PostgreSQL, qui la refusait comme valeur d'énumération | Typé `Disponibilite` : FastAPI valide et répond **422** avant le service | relecture de S5 | `efcd62f` |
| B07 | S5 | 🟠 | Après un `alembic downgrade`, l'`upgrade` suivant échoue | Alembic ne supprime pas le type PostgreSQL `disponibilite_enum` | Suppression explicite du type dans `downgrade()` | aller-retour de migration | `e8f02e1` |
| B08 | S5 | 🔴 | Les tests pouvaient **vider la base de développement** (tables admin, catégories, produits) | Chaque fichier d'intégration redirigeait `DATABASE_URL`, mais le moteur SQLAlchemy est créé au premier import. Si un test unitaire était chargé en premier, le moteur pointait sur la base de dev | `conftest.py` à la racine des tests, chargé avant tout le reste | relecture de S5 | `ea01d23` |
| B09 | S6 | 🔴 | Supprimer un produit qui a des photos → **500** (`IntegrityError`) | SQLAlchemy tentait `UPDATE photo SET produit_id = NULL`, interdit par `NOT NULL`. `passive_deletes=True` seul ne suffisait pas (vérifié par un test) | `cascade="all, delete-orphan"` + `passive_deletes=True`. Test vu rouge puis vert | test d'intégration | `e6d1ad0` |
| B10 | S6 | 🟡 | Logo illisible à 16 px (favicon) | Cernes du bois trop serrés | Logo redessiné, favicon simplifié | rendu à plusieurs tailles | `4c78936` |
| B11 | S6 | 🟡 | Les vraies pièces arrivaient en dernier dans la boutique, derrière des cases « Photo à venir » | Tri par date seulement | `avecPhotosDabord` : produits avec photos en premier (testé) | capture d'écran | `3852309` |
| B12 | S6 | 🟡 | Pied de page au milieu des pages courtes ; texte de l'accueil peu lisible sur mobile | Mise en page CSS | Pied de page collé en bas ; voile clair derrière le texte | capture d'écran | S6 |
| B13 | S6 | 🟡 | Page blanche en développement | Vite avait mis en cache une version vide de `Layout.jsx` pendant sa réécriture | Redémarrage de Vite. Réflexe retenu : console du navigateur (F12) | navigateur | — (environnement) |
| B14 | S7 | 🔴 | Supprimer un produit déjà commandé → **500** | La clé étrangère de `ligne_commande` bloque la suppression (voulu) mais l'erreur n'était pas traitée | Vérification dans le service, réponse **409** « passez-le en rupture » | test écrit avant le code | `b87e19f` |
| B15 | S7 | 🟠 | Les transitions entre pages ne faisaient rien | L'attribut `viewTransition` de React Router ne marche qu'en mode « Data », pas avec `<BrowserRouter>` | Composant `TransitionPages` | test dans le navigateur | `5449aeb` |
| B16 | S7 | 🟠 | Connexion admin refusée dans Swagger (401) | Le mot de passe du `.env` ne correspondait plus au hash en base ; `seed.py` ne met pas à jour un admin existant | Hash régénéré depuis le `.env` | test manuel | — (données) |
| B17 | S7 | 🟠 | Connexion SMTP refusée | Le texte d'exemple était resté dans `SMTP_PASSWORD` | Vrai mot de passe d'application. Trouvé sans afficher le secret, en comparant sa longueur | test manuel | — (configuration) |
| B18 | S7 | 🟡 | Les e-mails « n'arrivaient pas » | Gmail range dans « Envoyés » un e-mail dont l'expéditeur est aussi le destinataire | Aucune : comportement de Gmail, documenté | test manuel | — |
| B19 | S8 | 🟡 | `"StatusDevis"` au lieu de `"StatutDevis"` dans `__all__` | Faute de frappe, invisible pour les tests (personne ne fait `import *`) | Corrigé, puis vérifié en exécutant cet import | relecture | `71a8496` |
| B20 | S9 | 🟠 | Imports de `get_db` et des services effacés dans `routers/commandes.py` | Bloc d'imports réécrit au lieu d'être complété | Imports restaurés avant le commit | relecture du `git diff` | avant `c3c2140` |
| B21 | S9 | 🟠 | `update_statut` oubliée dans deux services | Fonction non écrite | Ajoutée ; signalée par un `AttributeError` dans les tests unitaires | tests unitaires | S9 |

## Bugs et limites ouverts

| ID | Gravité | Problème | Correction prévue |
|---|---|---|---|
| B22 | 🟠 | Un produit peut être créé avec un **prix négatif ou nul** | `Field(gt=0)` sur `prix` dans `schemas/produit.py` |
| B23 | 🟠 | Un produit peut être créé avec un **nom vide** | `Field(min_length=1)` et `str_strip_whitespace` |
| B24 | 🟡 | Un **slug** de catégorie accepte majuscules et espaces | Expression régulière `^[a-z0-9-]+$` |
| B25 | 🟡 | Le panier affiche l'**ancien prix** si l'artisane le change entre-temps | Relire les prix à l'ouverture du panier. La commande, elle, utilise déjà le bon prix |
| B26 | 🟠 | **Pas de limite de requêtes** sur `POST /api/commandes` et `POST /api/devis` (spam possible) | Limite par adresse IP (`slowapi` ou Nginx), réponse 429 |
| B27 | 🟡 | 220 avertissements `DeprecationWarning` pendant les tests | Ils viennent de `python-jose` (`datetime.utcnow()`), pas du projet. Remplacer par `PyJWT` |

Les bugs B22 à B24 ont été trouvés pendant les tests manuels du 13 octobre (`docs/tests-api.md`,
« Limites connues »). Les corrections sont listées dans `docs/evolutions-futures.md`.
