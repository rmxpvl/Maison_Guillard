# Maison Guillard — Préparation du jury (30 octobre 2026)

Deux parties : le **scénario de démonstration** (environ 10 minutes) et les **questions probables**
avec des réponses courtes à savoir dire avec ses propres mots.

---

## 1. Avant la démo (la veille et 30 minutes avant)

**La veille**
- [ ] PR #8 et #9 mergées : `main` contient tout. `git pull` sur `main`.
- [ ] Coordonnées et liens réseaux réels dans `frontend/src/config/coordonnees.js` (sinon assumer
      que ce sont des valeurs d'exemple).
- [ ] Une commande et une demande de devis récentes en base, pour que le back-office ne soit pas vide.
- [ ] Faire une capture d'écran de chaque étape de la démo : plan B si quelque chose plante.

**30 minutes avant**
1. Lancer **Docker Desktop**, puis `docker compose up -d` (PostgreSQL).
2. Terminal 1 : `cd backend` puis `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 3000`.
3. Terminal 2 : `cd frontend` puis `npm run dev`.
4. Vérifier `http://localhost:3000/api/health` → `{"status": "ok"}` et `http://localhost:5173`.
5. Panier vide, aucune session admin ouverte (fenêtre de navigateur neuve).
6. Réglage e-mail **activé** (onglet administration) et Gmail ouvert sur **« Messages envoyés »**
   (l'expéditeur et le destinataire étant la même adresse, les e-mails y sont rangés).
7. Garder un onglet **Swagger** (`http://localhost:3000/docs`) ouvert en réserve.

---

## 2. Scénario de démonstration (≈ 10 minutes)

### 1. Le contexte (1 min)
> « Maison Guillard est l'atelier de ma cousine, qui fabrique du mobilier en bois massif. Le site
> présente ses pièces, permet d'acheter celles qui sont disponibles, de demander un devis pour le
> sur-mesure, et lui donne un back-office pour tout gérer. »

Montrer la page d'accueil : entête transparent sur la photo, qui devient blanc au défilement.

### 2. La boutique (1 min 30)
- **Boutique** : filtrer par catégorie puis par disponibilité (l'URL change : le filtre se partage).
- Ouvrir une fiche avec plusieurs photos (**Tabouret Trapèze**) : fondu entre les photos.
- Expliquer les trois disponibilités et ce qu'elles déclenchent :
  - **disponible** → « Ajouter au panier » ;
  - **sur commande** → « Demander un devis » (prix « À partir de ») ;
  - **rupture** (affiché « Vendu ») → « Demander un modèle similaire ».

### 3. L'achat direct (2 min)
- Ajouter deux pièces disponibles → la pastille du panier change.
- **Panier** : changer une quantité, montrer le total.
- **Passer commande** → remplir le formulaire → **Commande n°X reçue**.
- Montrer les **deux e-mails** reçus (artisane + client).
> « Le prix n'est jamais envoyé par le navigateur : le serveur le relit en base et le recopie dans
> la commande. Personne ne peut modifier le prix depuis le navigateur. »

### 4. La demande de devis (1 min)
- Sur une fiche **sur commande** : « Demander un devis » → la page Contact s'ouvre sur le
  formulaire, avec « À propos de : … ».
- Envoyer → **Demande n°X envoyée**.

### 5. Le back-office (3 min)
- `/admin` → page de connexion. Montrer d'abord un **mauvais mot de passe**, puis le bon.
- **Commandes** : ouvrir la commande qui vient d'être passée, la passer en « Expédiée ».
- **Devis** : ouvrir la demande, la passer en « En discussion ».
- **Produits** : créer un produit, ajouter une photo, le voir apparaître dans la boutique publique.
- Essayer de **supprimer un produit déjà commandé** → message « passez-le en rupture ».
> « Une commande ne doit jamais perdre ses lignes : la base refuse la suppression, et l'API la
> traduit en un message clair. Pour un devis, au contraire, le lien vers le produit est simplement
> effacé. »
- **Déconnexion**, puis retour sur `/admin` → renvoyé à la connexion.

### 6. La qualité (1 min)
- Lancer les tests : `python -m pytest -q` (**151 tests**) et `npm test` (**27 tests**).
- Montrer Swagger : routes regroupées en français, bouton **Authorize**.
- Citer `docs/tests-api.md` : tests manuels documentés, tous PASS.

### Plan B
- API qui ne répond pas → page « Impossible de charger les données » : relancer uvicorn.
- Tests figés → Docker n'est pas lancé.
- E-mail qui n'arrive pas → regarder « Messages envoyés » ; sinon montrer le test automatisé
  `test_deux_emails_quand_le_reglage_est_active`.
- Tout le reste → les captures d'écran préparées la veille.

---

## 3. Questions probables et réponses

### Architecture et choix techniques

**Pourquoi FastAPI alors que la doc technique prévoyait Node/Express ?**
Le choix a été revu après le jalon de septembre. Python avec FastAPI apporte la validation des
données intégrée (Pydantic), la documentation Swagger générée automatiquement, et une stack que je
maîtrise mieux. Le modèle de données et les routes de la doc sont restés les mêmes.

**Comment le code backend est-il organisé ?**
En couches : les **routeurs** reçoivent la requête HTTP, les **schémas** Pydantic valident les
données, les **services** contiennent la logique métier, les **modèles** SQLAlchemy décrivent les
tables. Un service ne connaît pas HTTP : il lève une exception métier, et c'est le routeur qui
choisit le code (404, 409, 422).

**Comment le front parle-t-il au back ?**
Par `fetch` sur `/api/...`. En développement, Vite redirige `/api` vers FastAPI (proxy) : le
navigateur ne voit qu'une seule adresse, donc pas besoin de configurer CORS.

### Base de données

**Qu'est-ce qu'une migration ?**
Un script versionné qui fait passer la structure de la base d'une version à la suivante
(`upgrade`) ou revient en arrière (`downgrade`). Il y a une seule base, et un historique d'étapes
pour la faire évoluer sans perdre les données.

**Qu'est-ce qu'une session SQLAlchemy ?**
L'espace de travail d'une requête avec la base : elle accumule les modifications et les valide
toutes ensemble au `commit`, ou les annule au `rollback`. Chaque requête HTTP a sa propre session.

**Pourquoi `prix_unitaire_snapshot` ?**
Pour que la commande garde le prix du jour de l'achat, même si l'artisane change le prix plus tard.

**Pourquoi le total n'est pas une colonne ?**
Il est recalculé à partir des lignes (`@property`) : il ne peut jamais être en désaccord avec elles.

**Différence entre la suppression d'un produit commandé et d'un produit cité dans un devis ?**
Commande : clé étrangère sans cascade → la base refuse, l'API renvoie **409**. Devis :
`ON DELETE SET NULL` → le devis reste, seul le lien est effacé. Une commande a besoin de ses
produits, un devis non.

**Combien de commandes peut-on stocker ?**
L'identifiant va jusqu'à plus de 2 milliards ; en pratique la limite serait l'affichage du
back-office, sans pagination pour l'instant, ce qui convient au volume d'un artisan.

### Sécurité

**Comment l'administratrice est-elle authentifiée ?**
Au login, le serveur vérifie le mot de passe (haché avec **bcrypt**, jamais stocké en clair) et
renvoie un **JWT** signé (`python-jose`, HS256), valable 8 heures. Le front l'envoie dans l'en-tête
`Authorization: Bearer …` ; la dépendance `require_admin` le vérifie sur chaque route protégée.

**Où est gardé le jeton côté navigateur, et pourquoi ?**
Dans le `sessionStorage` : il disparaît à la fermeture du navigateur, ce qui est plus sûr sur un
ordinateur partagé. Si l'API répond 401 (jeton expiré), le front déconnecte automatiquement.

**Qu'est-ce qui empêche un client de tricher sur le prix ?**
Le prix ne fait pas partie de ce que le client envoie : seulement l'identifiant du produit et la
quantité. Le serveur relit le prix en base. Un test le vérifie.

**Comment les entrées sont-elles validées ?**
Par Pydantic : e-mail valide, champs non vides (espaces retirés), quantités de 1 à 10, longueurs
maximales. Toute donnée invalide est refusée avec un **422** avant d'arriver au code métier.

**Que se passe-t-il si l'envoi d'e-mail tombe en panne ?**
Rien pour le client : l'e-mail part en **tâche de fond** après la réponse, et une erreur SMTP est
seulement écrite dans les logs. La commande est enregistrée quoi qu'il arrive (test automatisé).

**Où sont les secrets ?**
Dans `backend/.env`, jamais commité (`.gitignore`). `.env.example` documente les variables sans
valeur. Pour Gmail, un **mot de passe d'application**, révocable, et pas le mot de passe du compte.

**Quelles limites de sécurité connaissez-vous ?**
Pas de limite au nombre de commandes envoyées par une même personne (une protection anti-abus
serait à ajouter) ; HTTPS à mettre en place au déploiement.

### Tests et qualité

**Comment avez-vous testé ?**
En TDD : le test est écrit et vu en échec avant le code. **151 tests** backend (unitaires avec une
base simulée par `MagicMock`, intégration avec `TestClient` sur une vraie base de test), **27 tests**
frontend (`node:test` sur les fonctions pures), et des tests manuels documentés dans
`docs/tests-api.md`.

**Comment testez-vous l'envoi d'e-mails sans en envoyer ?**
`unittest.mock.patch` remplace le client SMTP par un faux, qui enregistre les appels sans rien
envoyer ; on vérifie le nombre d'envois selon le réglage.

**Comment travaillez-vous avec Git ?**
Une branche par bloc (`Branche-S7`, `Branche-S8`…), des commits courts au format Conventional
Commits (`feat:`, `fix:`, `docs:`), une Pull Request par bloc avec la liste des tests passés.

### Frontend

**Comment le panier fonctionne-t-il ?**
Un **Context React** partage le panier entre les composants ; il est sauvegardé dans le
`localStorage` pour survivre au rechargement. Les règles (ajout, plafond à 10, total) sont des
fonctions pures testées séparément.

**Pourquoi `localStorage` pour le panier et `sessionStorage` pour le jeton ?**
Le panier doit survivre à la fermeture du navigateur (confort du client) ; le jeton, au
contraire, doit disparaître (sécurité).

**Comment fonctionne la transition entre les pages ?**
`TransitionPages` garde l'ancienne page affichée grâce à `<Routes location>` pendant qu'elle sort,
puis affiche la nouvelle. Le sens du glissement suit l'ordre du menu. Les animations sont coupées si
le visiteur a demandé à son système de les réduire.

### Méthode et suite

**Comment avez-vous travaillé avec votre « cliente » ?**
Chaque règle métier a été décidée avec elle : sens de « sur commande », pas de gestion de stock,
paiement hors ligne, e-mails optionnels, direction artistique noire et blanche.

**Les images sont-elles générées par IA ?**
Les deux grandes images d'ambiance de l'accueil, oui ; aucune photo de produit ne l'est. La règle
retenue : un décor peut être mis en scène, mais le meuble montré à la vente doit être fidèle
(sinon, risque de pratique commerciale trompeuse).

**Avez-vous utilisé l'IA pour coder ?**
Comme assistant : pour expliquer, relire et proposer des solutions. Depuis l'achat direct, les
fichiers de test et le frontend ont été générés puis expliqués ; le code backend, je l'ai tapé
moi-même. Je peux justifier chaque choix.

**Que reste-t-il pour une vraie mise en ligne ?**
Hébergement avec HTTPS ; `.env` de production (SMTP de l'hébergeur, adresse de l'artisane) ;
vraies coordonnées et photos ; intégration réelle de Cloudinary pour les photos ; pagination et
gestion des catégories dans le back-office ; protection anti-abus ; paiement en ligne si besoin.
