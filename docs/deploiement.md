# Maison Guillard — Mise en ligne (Render)

Ce document explique, dans l'ordre, comment mettre le site en ligne et quoi vérifier ensuite.
Tout ce qui est décrit dans `render.yaml` se crée presque tout seul ; le reste (comptes,
domaine, clés) se fait à la main, une fois.

> **À savoir :** cette mise en ligne n'a pas encore été faite en vrai. Le premier déploiement est le
> moment où l'on découvre ce qu'un test local ne montre pas : suivre la liste de vérifications en
> bas de page, et noter ici ce qui a dû être corrigé.

## Ce qu'on met en ligne

```mermaid
flowchart LR
    V([Visiteur]) -->|HTTPS| S["Site React<br/>www.votre-domaine.fr<br/>(Render, site statique)"]
    S -->|"HTTPS, appels /api"| A["API FastAPI<br/>api.votre-domaine.fr<br/>(Render, service web)"]
    A --> DB[(PostgreSQL<br/>Render, Francfort)]
    A --> C[[Cloudinary<br/>photos]]
    A --> B[[Brevo<br/>e-mails]]
    A <--> ST[[Stripe<br/>paiement]]
```

- Le **site** et l'**API** sont deux services sur deux adresses (`www.` et `api.`). L'API n'accepte
  les appels du navigateur que depuis l'adresse du site (réglage `CORS_ORIGINS`).
- Chaque fusion sur la branche `main` redéploie tout seul. L'API applique d'abord les migrations de
  la base (`alembic upgrade head`) : un déploiement avec une migration cassée ne démarre pas.
- Au démarrage en production, l'API **vérifie sa configuration** et refuse de démarrer, en listant ce
  qui manque ou est dangereux (secret trop court, clé Stripe absente, adresse en `http://`…).

## Avant de commencer : les comptes

| Quoi | Pour quoi | Remarque |
|---|---|---|
| **Render** | héberger la base, l'API et le site | une carte bancaire est demandée ; la base gratuite expire, prendre un plan payant avec sauvegardes |
| **Stripe**, au nom de l'artisane | encaisser | activer le compte (identité, IBAN) **avant** de passer en réel : cela peut prendre quelques jours |
| **Cloudinary** | photos des produits | l'offre gratuite suffit pour démarrer |
| **Brevo** | e-mails | vérifier l'adresse (ou le domaine) d'expédition avant d'envoyer |
| **Nom de domaine** | l'adresse du site | à acheter chez un registraire, puis à relier à Render |
| **GitHub** | le dépôt relié à Render | déjà en place |

À rassembler aussi, pour les pages légales : nom légal, SIRET, adresse de l'atelier, e-mail et
téléphone, mention de TVA, nom du médiateur de la consommation, directeur de la publication.

## Les étapes

**1. Cloudinary.** Créer le compte, puis dans « Tableau de bord » copier l'**API environment
variable** : c'est une adresse du type `cloudinary://CLÉ:SECRET@NOM`. Elle servira de `CLOUDINARY_URL`.

**2. Brevo.** Créer le compte, vérifier l'adresse d'expédition (idéalement le domaine, avec les
enregistrements SPF et DKIM proposés par Brevo), puis « SMTP et API » > « SMTP » pour obtenir le
**login** (`SMTP_USER`) et une **clé SMTP** (`SMTP_PASSWORD`). Le serveur est
`smtp-relay.brevo.com`, port `587` (déjà dans `render.yaml`).

**3. Render : créer l'ensemble.** « New » > **Blueprint**, choisir ce dépôt, branche `main`. Render
lit `render.yaml` et propose la base, l'API et le site. Il demande les variables marquées
`sync: false` (tableau plus bas). Pour celles qui dépendent du domaine (`SITE_URL`, `CORS_ORIGINS`,
`VITE_API_URL`), mettre une valeur provisoire (`https://example.fr`) puis la corriger à l'étape 4.

**4. Les domaines.** Dans chaque service Render, « Settings » > « Custom Domains » :
`www.votre-domaine.fr` pour le site, `api.votre-domaine.fr` pour l'API. Render indique les
enregistrements DNS à créer chez le registraire ; le certificat HTTPS est automatique. Puis corriger :

- `SITE_URL` et `CORS_ORIGINS` = `https://www.votre-domaine.fr` (service API) ;
- `VITE_API_URL` = `https://api.votre-domaine.fr/api` (service site). Cette variable est lue **à la
  construction** du site : après l'avoir changée, relancer un déploiement du site.

**5. Stripe en réel.** Passer le tableau de bord en mode **production**, puis :

- « Développeurs » > « Clés API » : copier la clé secrète `sk_live_…` dans `STRIPE_SECRET_KEY` ;
- « Développeurs » > « Webhooks » > « Ajouter un endpoint » : adresse
  `https://api.votre-domaine.fr/api/stripe/webhook`, événement **`checkout.session.completed`** ;
  copier le « secret de signature » `whsec_…` dans `STRIPE_WEBHOOK_SECRET`.

C'est ici que la page « Webhooks » du tableau de bord sert enfin : elle exige une adresse publique,
ce qu'`localhost` n'est pas (en développement on utilise le Stripe CLI, voir le README).

**6. Le premier administrateur.** La base de production est vide. Dans le « Shell » du service API
sur Render, une seule fois, avec un mot de passe long :

```
SEED_ADMIN_EMAIL=adresse@exemple.fr SEED_ADMIN_PASSWORD='un-mot-de-passe-long' python seed.py
```

Ne pas ajouter ces deux variables à l'environnement de façon permanente. Ne pas lancer
`seed_catalogue.py` : il crée des produits de démonstration.

**7. Le contenu.** Se connecter à `https://www.votre-domaine.fr/admin`, puis :
« Informations du devis » (identité légale, frais de livraison, conditions, messages types),
Catégories, Finitions, Produits avec leurs photos. Remplacer les coordonnées d'exemple dans
`frontend/src/config/coordonnees.js` (e-mail, téléphone, zone, réseaux) et fusionner sur `main`.

**8. Les pages légales.** Les trois pages (CGV, mentions légales, données personnelles) sont des
**textes modèles à faire valider par un professionnel**. Une fois validées et les champs « à
compléter » remplis, passer `TEXTE_A_VALIDER` à `false` dans `frontend/src/config/legal.js` pour
retirer le bandeau. Si le texte des CGV change, incrémenter `CGV_VERSION` à la fois dans
`frontend/src/config/legal.js` et dans `backend/app/services/paiement_service.py` : la version
acceptée est enregistrée avec chaque devis payé.

## Variables d'environnement

**API** (service `maison-guillard-api`)

| Variable | Valeur |
|---|---|
| `APP_ENV` | `production` (déjà dans `render.yaml`) |
| `TRUST_PROXY` | `1` (déjà dans `render.yaml`) |
| `DATABASE_URL` | fournie par la base Render (liée dans `render.yaml`) |
| `JWT_SECRET` | générée par Render (liée dans `render.yaml`) |
| `SITE_URL` | `https://www.votre-domaine.fr` |
| `CORS_ORIGINS` | `https://www.votre-domaine.fr` (plusieurs : séparées par des virgules) |
| `STRIPE_SECRET_KEY` | `sk_live_…` |
| `STRIPE_WEBHOOK_SECRET` | `whsec_…` de l'endpoint de production |
| `CLOUDINARY_URL` | `cloudinary://CLÉ:SECRET@NOM` |
| `SMTP_HOST`, `SMTP_PORT` | `smtp-relay.brevo.com`, `587` (déjà dans `render.yaml`) |
| `SMTP_USER`, `SMTP_PASSWORD` | login et clé SMTP de Brevo |
| `EMAIL_EXPEDITEUR` | `Maison Guillard <contact@votre-domaine.fr>` (adresse vérifiée dans Brevo) |
| `EMAIL_ARTISAN` | l'adresse qui reçoit les nouvelles demandes, paiements et messages |
| `DOCS_ENABLED` | `1` seulement pour rouvrir la documentation Swagger (`/docs`) |

**Site** (service `maison-guillard-site`) : `VITE_API_URL` et `NODE_VERSION` (déjà dans `render.yaml`).

## Vérifier après la mise en ligne

À faire dans l'ordre, avec un vrai petit paiement, puis un remboursement :

1. `https://api.votre-domaine.fr/api/health` répond `{"status":"ok"}` ; `/docs` répond 404.
2. Le site s'affiche, la boutique charge les produits (sinon : `CORS_ORIGINS` ou `VITE_API_URL`).
3. Se connecter à `/admin`. Ajouter une photo à un produit, redéployer, vérifier qu'elle est toujours
   là (elle est sur Cloudinary, pas sur le disque de l'API).
4. Envoyer une demande depuis le site avec une vraie adresse : l'e-mail d'accusé de réception arrive,
   et l'artisane reçoit la notification.
5. Envoyer le devis depuis l'admin : l'e-mail arrive avec le PDF, le lien du devis s'ouvre.
6. Accepter et payer avec une vraie carte (petit montant) : la page passe à « Paiement reçu », la
   demande devient « Payée » dans l'admin, les deux e-mails partent. Dans Stripe,
   « Développeurs » > « Webhooks » montre l'événement livré avec le code 200.
7. Annuler la commande depuis la page du devis : remboursement visible dans Stripe, e-mails reçus.
8. Taper dix fois de suite un mauvais mot de passe sur `/admin/connexion` : la dixième tentative
   répond « Trop de tentatives ».
9. Les trois pages légales s'ouvrent depuis le pied de page, avec l'identité de l'entreprise.

## Au quotidien

- **Déployer** : fusionner sur `main`. Render reconstruit le site et l'API, applique les migrations.
- **Voir ce qui se passe** : onglet « Logs » de chaque service Render. Une panne d'envoi d'e-mail ou
  un paiement dont le montant ne correspond pas y est journalisé.
- **Sauvegardes** : celles de la base Render (à activer avec le plan choisi). Tester une restauration
  au moins une fois.
- **Clés compromises** : régénérer la clé concernée (Stripe, Cloudinary, Brevo) puis mettre à jour
  la variable dans Render. Changer `JWT_SECRET` déconnecte tout le monde.

## Limites connues

- La **limitation de requêtes** compte en mémoire : elle suppose **une seule instance** de l'API
  (c'est le cas du plan choisi). Avec plusieurs instances, chacune compterait de son côté.
- Les **images supprimées** dans l'admin ne sont pas retirées de Cloudinary (elles restent
  invisibles, mais occupent de la place).
- La **pastille de couleur** d'une finition sur le PDF du devis n'apparaît que pour les images
  stockées sur le disque (développement) ; avec Cloudinary, le PDF affiche le nom de la finition
  sans pastille.
- Les **devis expirés** passent à « expiré » à la lecture, sans tâche planifiée.
- Version de Python : `render.yaml` demande 3.12 ; le développement local tourne en 3.14. Si Render
  refuse cette version, ajuster `PYTHON_VERSION`.

## Local et production, en bref

| | En local | En production |
|---|---|---|
| Base | PostgreSQL 16 dans Docker | PostgreSQL géré par Render, avec sauvegardes |
| API | `uvicorn --reload`, port 3000 | `uvicorn` sans rechargement, derrière le proxy de Render |
| Site | serveur Vite (port 5173), proxy `/api` | fichiers construits par `npm run build`, site statique Render |
| Photos | `backend/uploads/` | Cloudinary |
| E-mails | Gmail ou autre SMTP de test | Brevo |
| Paiement | Stripe en mode test, `stripe listen` | Stripe en mode production, webhook configuré |
| Connexion | HTTP | HTTPS (certificat automatique) |
| Documentation `/docs` | ouverte | fermée |
