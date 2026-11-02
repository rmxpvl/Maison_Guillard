# Maison Guillard — Revues de sprint

> À la fin de chaque sprint : ce qui était prévu, ce qui a été livré, la démonstration jouée, et le
> résultat des tests. La démonstration est un parcours complet, dans Swagger pour l'API et dans le
> navigateur pour le site. Les règles métier ont été décidées avec l'artisane (ma cousine, la
> stakeholder). Le détail de chaque sprint est dans son résumé (`docs/2026-…-resume.md`).

---

## Sprint 1 — S4 : initialisation et authentification (14 → 17 septembre)

**Objectif** : un projet qui démarre et une administratrice qui peut se connecter.

**Livré**
- PostgreSQL dans Docker, application FastAPI, `GET /api/health`.
- Table `admin` et première migration Alembic.
- Mots de passe hachés avec bcrypt, JWT signé valable 8 h.
- `POST /api/auth/login` et la dépendance `require_admin` (401 sans jeton valide).
- `seed.py` : le compte admin est créé depuis les variables d'environnement, jamais en dur.

**Démonstration** : connexion dans Swagger, jeton reçu, route protégée accessible avec le jeton et
refusée sans.

**Tests** : 14 (unitaires sur `auth_service` + intégration sur la route de connexion).

**Non livré** : la page de connexion du frontend, reportée (voir `suivi-et-metriques.md`).

---

## Sprint 2 — S5 : API du catalogue (22 septembre → 6 octobre)

**Objectif** : l'artisane peut gérer catégories, produits et photos par l'API.

**Livré**
- Catégories : liste publique, création et suppression admin ; suppression refusée (409) si un
  produit l'utilise.
- Produits : liste filtrable (catégorie, disponibilité), détail, création, **mise à jour
  partielle**, suppression.
- Photos : upload de fichier, une seule photo principale par produit, suppression en cascade avec
  le produit. Stockage local en attendant Cloudinary.
- Correctifs après relecture (6 octobre) : 409 sur un slug en double, 422 pour une catégorie
  inexistante ou un filtre invalide, migration réversible, tests isolés de la base de dev.

**Démonstration** : scénario complet dans Swagger (créer une catégorie, un produit, une photo,
tenter de supprimer la catégorie → 409).

**Tests** : 47 au moment de la PR #1, puis des tests de non-régression pour chaque correctif.

**PR** : #1, #2, et la fusion des correctifs du 6 octobre.

---

## Sprint 3 — S6 : site public, vitrine et qualité de l'API (10 → 13 octobre)

**Objectif** : un visiteur parcourt le catalogue ; l'API est documentée et vérifiée à la main.

**Livré**
- Application React : accueil (vitrine), boutique avec filtres, fiche produit avec galerie,
  « Qui sommes-nous », Contact, page 404.
- Règles d'affichage des trois disponibilités, décidées avec l'artisane.
- Direction artistique : police Jost, palette, logo en SVG.
- Catalogue de démonstration (12 produits, 3 vraies pièces photographiées).
- Swagger en français avec les réponses d'erreur ; 16 tests de sécurité sur les routes admin ;
  rapport de 30 tests manuels (`docs/tests-api.md`).

**Démonstration** : parcours de chaque page, vérifié par captures d'écran en largeur ordinateur
(1440 px) et mobile (500 px). Décidé avec l'artisane : le sens de « sur commande » et la place du
sur-mesure sur la page Contact.

**Tests** : 80 backend, 10 frontend, 30 vérifications manuelles (toutes PASS).

**PR** : #3, #4, #5.

---

## Sprint 4 — S7 : achat direct (20 → 23 octobre)

**Objectif** : un visiteur passe une commande ; l'artisane est prévenue.

**Livré**
- Tables `commande`, `ligne_commande`, `parametre`.
- `POST /api/commandes` : validation complète, **prix toujours relu en base**, produits
  indisponibles refusés (422).
- E-mails à l'artisane et au client en tâche de fond, activables par un réglage.
- Suppression d'un produit déjà commandé refusée (409).
- Panier (sauvegardé dans le navigateur), page panier, formulaire de commande, confirmation.
- Nouvelle direction artistique noir et blanc, transitions entre les pages.

**Démonstration** : commande complète passée depuis le site, réception réelle des deux e-mails.
Décidé avec l'artisane : pas de gestion de stock, paiement et livraison réglés avec elle.

**Tests** : 110 backend, 19 frontend, 16 vérifications manuelles (toutes PASS).

**PR** : #6.

---

## Sprint 5 — S8 : demande de devis (23 → 26 octobre)

**Objectif** : un visiteur demande un devis, lié à un produit ou non.

**Livré**
- Table `devis` ; supprimer un produit garde ses devis (`SET NULL`).
- `POST /api/devis`, e-mails réutilisant le réglage des commandes.
- Formulaire sur la page Contact ; les trois boutons des fiches produit y mènent avec le produit
  pré-rempli.

**Démonstration** : demande de devis depuis une pièce « sur commande », une pièce vendue et une
pièce disponible.

**Tests** : 129 backend, 23 frontend, 9 vérifications manuelles (toutes PASS).

**PR** : #7.

---

## Sprint 6 — S9 : back-office (26 octobre)

**Objectif** : l'artisane gère tout depuis une interface, sans Swagger.

**Livré**
- API : liste des commandes et des devis (filtre par statut), changement de statut.
- Connexion `/admin/connexion` ; jeton dans le `sessionStorage` ; déconnexion automatique sur 401.
- Tableau de bord : interrupteur e-mail, onglets Produits, Commandes et Devis.
- Gestion des produits et de leurs photos.
- Nouveau pied de page.

**Démonstration** : connexion au back-office, création d'un produit et ajout de ses photos,
passage d'une commande en « Expédiée » et d'un devis en « En discussion », déconnexion.

**Tests** : 151 backend, 27 frontend, 11 vérifications manuelles d'API (toutes PASS) et parcours
complet du back-office.

**PR** : #8.

---

## Sprint 7 — Finition (26 → 30 octobre)

**Livré** : entête transparent et nouvelles photos de l'accueil (PR #9, #10), guide de préparation
de la soutenance, liste des évolutions futures (PR #11).
