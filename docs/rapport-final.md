# Maison Guillard — Rapport final

> Étape 5 du projet de portfolio (clôture). Bilan du MVP par rapport au dossier de cadrage
> (`Documentation/Maison-Guillard-MVP.pdf`), leçons apprises et points clés de la rétrospective.
> Projet réalisé seul, du 21 août au 30 octobre 2026.

## 1. Résumé des résultats

**Le MVP est complet et fonctionnel** : les trois objectifs SMART du cadrage sont atteints, et les
16 éléments du périmètre « in-scope » sont livrés, dont 2 partiellement. L'application a été
évaluée à **85 %** lors de la revue technique. L'artisane l'a testée le 2 novembre et souhaite en
faire son vrai site.

### Fonctionnalités principales livrées

- **Site public** : accueil, boutique filtrable par catégorie et par disponibilité, fiche produit
  avec galerie de photos, pages « Qui sommes-nous » et « Contact ».
- **Achat direct** : panier sauvegardé dans le navigateur, commande en invité, confirmation,
  prix toujours relus en base.
- **Demande de devis** : formulaire lié ou non à un produit.
- **Back-office sécurisé** : connexion (bcrypt + JWT), gestion des produits et de leurs photos,
  suivi des commandes et des devis avec changement de statut.
- **E-mails automatiques** à l'artisane et au client, activables par un réglage (hors périmètre
  initial, ajouté à la demande de l'artisane).

### Comparaison avec les objectifs SMART du cadrage

| Objectif du cadrage | Critère | Résultat | Atteint |
|---|---|---|---|
| 1. Catalogue | au moins 10 produits en base, couvrant tables, chaises, tabourets et lampes, visibles sur le site public | 12 produits dans les 4 catégories, dont 3 vraies pièces photographiées | ✅ |
| 2. Back-office | interface authentifiée : créer, consulter, modifier, supprimer des produits, gérer descriptions, prix, disponibilités et photos | tout est disponible dans l'interface `/admin` | ✅ |
| 3. Commandes et devis | les deux parcours, et leur gestion par l'administrateur | achat direct et devis en ligne, listes et statuts dans le back-office | ✅ |

### Comparaison avec le périmètre du cadrage

| Élément « in-scope » | Résultat |
|---|---|
| Application responsive, site public, catalogue, catégories, fiches produits | ✅ livré (vérifié à 1 440 px et 500 px de large) |
| Photos, descriptions, prix, disponibilité | ✅ livré |
| Base de données relationnelle, API REST | ✅ PostgreSQL 16, 8 tables, 4 migrations ; 22 routes documentées dans Swagger |
| Authentification et autorisation administrateur | ✅ bcrypt + JWT, 15 routes protégées |
| CRUD des produits, gestion des images | ✅ livré · ⚠️ **partiel** : le format et la taille des fichiers envoyés ne sont pas contrôlés, contrairement à la mesure prévue pour le risque n°3 |
| Panier, création et gestion des commandes | ✅ livré |
| Demandes de devis et leur gestion | ✅ livré |
| Validation des données et gestion des erreurs | ✅ livré · ⚠️ **partiel** : un prix négatif, un nom vide ou un slug mal formé sont encore acceptés pour un produit ou une catégorie (bugs B22 à B24) |
| Mesures de sécurité de base | ✅ mots de passe hachés, jetons signés, requêtes paramétrées, prix relus en base, secrets hors du dépôt |
| Tests et documentation | ✅ 178 tests automatisés, 66 vérifications manuelles, README avec diagrammes |

**Écarts assumés**
- **Paiement en ligne** : non intégré, comme le cadrage le permettait (« évalué en fonction du
  temps disponible »). Le paiement et la livraison se règlent directement avec l'artisane.
- **Gestion des catégories** : possible par l'API (Swagger), pas encore dans l'interface. Avec
  4 catégories rarement modifiées, ce n'était pas prioritaire.
- **Mise en ligne** : le MVP tourne en local ; le plan de déploiement est prêt
  (`docs/deploiement.md`).

### Indicateurs clés

| Indicateur | Valeur |
|---|---|
| Tâches réalisées / prévues | **47 / 48 (98 %)** |
| Tests automatisés | **178** (151 backend, 27 frontend), tous au vert |
| Vérifications manuelles (Swagger + navigateur) | **66 / 66 PASS** |
| Bugs enregistrés / corrigés | **28 / 21 (75 %)**, dont les **6 bloquants tous corrigés** |
| Pull Requests fusionnées | **13**, une par sprint ou bloc |
| Commits sur `main` | **107**, au format Conventional Commits |
| Délai | fin prévue le 21 octobre, MVP complet le 26 octobre (**+5 jours**) |
| Revue technique | **85 %** |

Détail : `docs/gestion-projet/suivi-et-metriques.md`, `docs/bugs.md`, `docs/resultats-tests.md`.

### Retours des utilisateurs

- **L'artisane (stakeholder), le 2 novembre** : elle a beaucoup apprécié le site et veut l'utiliser
  pour son activité, en payant son développement. Son test a fait apparaître un bug (B28 : le
  bouton « afficher le mot de passe » d'Edge disparaissait) et de nouveaux besoins : tout fabriquer
  sur commande, trois boutiques (meubles, céramique, papeterie), choix des teintes, paiement en
  ligne.
- **La revue technique (SWE)** : réponses techniques solides ; points faibles sur le frontend et sur
  l'écriture de requêtes SQL de mémoire.
- **Le manager** : a recommandé des comptes clients, gardés pour une évolution future.

## 2. Leçons apprises

### Ce qui a bien marché, et pourquoi

| Ce qui a marché | Pourquoi |
|---|---|
| **Une conception et un plan écrits avant chaque sprint** | Chaque tâche était claire avant d'écrire du code ; les décisions sont tracées dans `docs/specs/` et `docs/plans/`. |
| **Le TDD** (test vu en échec avant le code) | Il a attrapé des erreurs réelles : une correction fausse pour B09, une fonction oubliée deux fois (B21). |
| **Une architecture en couches répétée** (router → schéma → service → modèle) | Chaque nouvelle ressource suivait le même modèle : rapide à construire et à expliquer à l'oral. |
| **Les décisions métier prises avec l'artisane** | Pas de stock, paiement hors ligne, sens de « sur commande » : rien n'a été supposé, donc rien n'a été refait pour cette raison. |
| **Les petits blocs de 1 à 4 jours** (à partir du 10 octobre) | Ils ont rattrapé l'essentiel du retard : 4 blocs livrés en 16 jours. |
| **Une branche et une PR par sprint**, avec relecture du diff | `main` est restée fonctionnelle ; un effacement d'imports a été vu avant les tests (B20). |
| **Taper le backend à la main** | Je pouvais justifier chaque ligne pendant la revue. |

### Les difficultés, et comment elles ont été résolues

| Difficulté | Solution |
|---|---|
| **Changement de stack** (Node.js → Python) au début du développement | Fait avant tout code métier : rien à réécrire, modèle de données et routes inchangés. |
| **Retard sur le plan de route** (site public non commencé au 10 octobre) | Redécoupage du reste en 5 blocs courts ; périmètre réduit à l'essentiel pour le devis et le back-office. |
| **Bugs bloquants de S5** (erreurs 500 au lieu de 409/422, tests qui vidaient la base de développement) | Une passe de correctifs avant de continuer, puis la règle de toujours tester les cas d'erreur. |
| **Problèmes d'environnement** (Docker éteint, deux serveurs à lancer, Git sous WSL, mot de passe SMTP) | Vérifications de démarrage notées dans `docs/commandes.md` ; Git utilisé depuis PowerShell. |
| **Le frontend, domaine que je maîtrise moins** | Frontend généré avec une IA à partir de S7, puis relu et expliqué ; règles d'affichage sorties dans des fonctions pures et testées. |

### Ce que je ferais autrement

1. **Des sprints courts dès le début**, au lieu de semaines : les blocs courts ont mieux marché.
2. **Un outil de suivi visuel** (GitHub Projects) et **des issues GitHub pour chaque bug** au moment
   où il est trouvé, au lieu de les rassembler après coup.
3. **Plus de temps pour les tests avec l'utilisatrice réelle**, et plus tôt : le test de
   l'artisane, après la fin du MVP, a révélé un bug et des besoins que mes propres tests ne
   pouvaient pas montrer.
4. **Déployer tôt une version minimale**, pour découvrir les contraintes de production avant la fin.
5. **Pratiquer régulièrement le SQL écrit à la main** : l'ORM m'a protégé des injections, mais m'a
   fait oublier la syntaxe, ce que la revue a montré.

## 3. Rétrospective (points clés)

Projet solo : pas de réunion d'équipe. La rétrospective a été faite en trois temps : une
rétrospective personnelle à la fin de chaque sprint (`docs/gestion-projet/retrospectives.md`), le
retour de l'artisane après sa démonstration, et celui de la revue technique. Les trois questions de
l'énoncé :

**Qu'est-ce qui a bien marché ?**
- La méthode répétée à chaque sprint : conception, plan, TDD, PR.
- Le travail avec l'artisane : les règles venaient d'elle, et elle veut maintenant utiliser le site.

**Quelles difficultés, et comment ont-elles été résolues ?**
- Le retard, rattrapé par des blocs courts et un périmètre réduit.
- Les erreurs de qualité de S5, corrigées puis transformées en réflexes (cas d'erreur testés,
  diff relu avant chaque fusion).

**Comment améliorer la collaboration à l'avenir ?**
- Montrer le site à l'artisane **à la fin de chaque sprint**, pas seulement à la fin du projet.
- Rendre l'avancement visible pour les autres (tableau GitHub Projects, issues).
- Avec une équipe : garder une PR par fonctionnalité, avec un relecteur autre que l'auteur.

## 4. Suite du projet

Le projet continue en dehors de la formation : une **version 2** est conçue avec l'artisane
(boutique entièrement sur commande en trois univers, teintes, devis en PDF, paiement en ligne par
Stripe, mise en ligne sur Render). La version évaluée est conservée par l'étiquette Git
`v1.0-ecole`.
