# Maison Guillard — Rétrospectives de sprint

> À la fin de chaque sprint, trois questions : qu'est-ce qui a bien marché, quelles difficultés,
> et qu'est-ce que je change pour le sprint suivant. La dernière colonne montre que chaque
> amélioration a bien été appliquée ensuite.

---

## Sprint 1 — S4 : initialisation et authentification

| Ce qui a bien marché | Difficultés | Amélioration pour la suite |
|---|---|---|
| Changer de stack au tout début, avant le code métier : aucun code à réécrire. | La structure du plan n'a pas été respectée partout (`require_admin` mal rangé, bug B01). | Relire la structure des dossiers du plan avant de commencer chaque tâche. |
| Les tests unitaires avec une base simulée : la logique est testée sans démarrer PostgreSQL. | Le frontend prévu n'a pas été fait. | Plutôt qu'un sprint trop chargé, prioriser le backend (MVP-first). |
| Secrets dans `.env`, compte admin créé par un script. | Le code de S4 n'avait pas été tapé à la main : plus difficile à expliquer. | **À partir de S5, je tape moi-même tout le code backend.** |

---

## Sprint 2 — S5 : API du catalogue

| Ce qui a bien marché | Difficultés | Amélioration pour la suite |
|---|---|---|
| Taper le backend à la main : je peux expliquer chaque ligne. | La relecture après fusion a trouvé **5 défauts**, dont 3 erreurs 500 (B04 à B08). | **Tester les cas d'erreur, pas seulement le cas normal** : chaque route a maintenant ses tests 404/409/422. |
| L'architecture router → service → modèle se répète pour chaque ressource : rapide à étendre. | Le test qui vidait la base de dev (B08) est passé inaperçu longtemps. | Un `conftest.py` racine force la base de test pour tout le monde. |
| Cloudinary remplacé par un stockage local derrière une seule fonction. | Le sprint a duré deux semaines au lieu d'une. | Relire le code **avant** de fusionner, pas après. |

---

## Sprint 3 — S6 : site public, vitrine et qualité de l'API

| Ce qui a bien marché | Difficultés | Amélioration pour la suite |
|---|---|---|
| **Le redécoupage en petits blocs** : un bloc conçu, planifié et livré dans la journée. | Retard sur le plan de route (le site public n'était pas commencé au 10 octobre). | Garder des blocs de 1 à 4 jours jusqu'à la fin. |
| Les règles d'affichage décidées avec l'artisane plutôt que supposées. | Bug B09 (500 en supprimant un produit avec photos) : ma première correction était fausse. | **Vérifier une correction par un test vu rouge puis vert**, ne jamais la supposer bonne. |
| Les captures d'écran ont révélé des défauts invisibles dans le code (B11, B12). | Page blanche attribuée à tort à l'outil au lieu d'être investiguée (B13). | Page blanche → ouvrir la console du navigateur (F12) en premier. |
| Rapport de tests manuels qui sert aussi de script de démonstration. | — | Ajouter une section au rapport à chaque sprint (fait en S7, S8, S9). |

---

## Sprint 4 — S7 : achat direct

| Ce qui a bien marché | Difficultés | Amélioration pour la suite |
|---|---|---|
| Le prix relu en base : un test manuel prouve qu'un faux prix est ignoré. | Du temps perdu sur l'environnement : Docker éteint, backend pas lancé, mauvais mot de passe SMTP (B16, B17). | Vérifications de démarrage notées dans `docs/commandes.md` : `docker compose ps`, deux terminaux. |
| Les e-mails en tâche de fond : une panne SMTP ne bloque pas la commande (testé avec un faux serveur). | Une fonction React Router annoncée comme faite alors qu'elle ne marchait pas dans notre mode (B15). | **Vérifier qu'une fonctionnalité s'applique à notre configuration avant de dire qu'elle est faite.** |
| Une demande de l'artisane en cours de sprint (noir et blanc) absorbée sans retard. | Sprint le plus gros (11 tâches). | Réduire le périmètre des sprints suivants pour tenir la date du jury. |

---

## Sprint 5 — S8 : demande de devis

| Ce qui a bien marché | Difficultés | Amélioration pour la suite |
|---|---|---|
| Périmètre volontairement réduit : 5 tâches seulement, livrées en trois jours. | Une faute de frappe invisible pour les tests (B19). | Relire les fichiers que les tests n'exécutent pas (`__init__.py`). |
| Réutilisation du code de S7 (e-mails, messages d'erreur partagés). | Un test manuel a envoyé un vrai e-mail (réglage activé). | Les tests manuels désactivent le réglage puis le remettent dans son état. |
| Choix `SET NULL` pour les devis, réfléchi par rapport aux commandes (409). | — | — |

---

## Sprint 6 — S9 : back-office

| Ce qui a bien marché | Difficultés | Amélioration pour la suite |
|---|---|---|
| Le back-office réutilise toutes les routes existantes : seulement 4 nouvelles routes. | Des imports effacés en en ajoutant d'autres (B20). | **Toujours relire `git diff` avant de lancer les tests et de commiter.** |
| Les tests unitaires ont signalé tout de suite une fonction oubliée (B21). | Un fichier modifié mais pas enregistré dans l'éditeur. | Vérifier `git status` avant chaque commit. |
| Périmètre « essentiel » choisi à l'avance : sprint tenu en une journée. | Pas de pagination, catégories toujours dans Swagger. | Noté dans `docs/evolutions-futures.md`. |

---

## Bilan général du projet

**À garder pour un prochain projet**
- Une conception et un plan écrits avant le code, pour chaque sprint.
- Le TDD : voir le test échouer avant d'écrire le code.
- Une branche et une Pull Request par sprint, avec relecture du diff.
- Les décisions métier prises avec la cliente, pas supposées.

**À faire autrement**
- **Des sprints courts dès le départ** : les blocs de 1 à 4 jours ont mieux marché que les
  semaines.
- **Un outil de suivi visuel** (GitHub Projects ou Trello) : utile pour montrer l'avancement à
  quelqu'un d'autre.
- **Des issues GitHub pour les bugs** au moment où ils sont trouvés, liées au commit de
  correction, au lieu de les rassembler après coup.
- **Déployer tôt**, même une version minimale, pour découvrir les problèmes de production avant
  la fin.
