# Maison Guillard v2 — Boutique sur commande, devis, paiement en ligne et mise en ligne

> Conception de la version finale livrée à l'artisane. Rédigée le 2026-11-08 à partir des retours
> de l'artisane après la présentation du MVP (voir aussi `docs/bugs.md` B28 et
> `docs/evolutions-futures.md`). La v1 (MVP évalué à l'école) est conservée par l'étiquette Git
> `v1.0-ecole`.

## 1. Intention

Le MVP vendait des pièces « disponibles » par un panier, et traitait les devis à part. En réalité,
l'artisane **fabrique tout à la commande** et ajuste le prix de chaque pièce selon la finition et
les souhaits du client. La v2 fait du site l'outil réel de son activité :

- le client compose une **demande** (un panier de pièces, avec pour chacune une teinte et un
  souhait écrit) ;
- l'artisane répond par un **devis** (prix final de chaque pièce + frais de livraison) ;
- le client **accepte et paie la totalité en ligne** ;
- l'artisane fabrique et livre **sous 15 jours** après le paiement.

Le site est **mis en ligne** par nous sur Render, avec un vrai domaine, HTTPS, paiements Stripe,
photos sur Cloudinary et e-mails par Brevo.

**Succès** = l'artisane reçoit une demande, envoie un devis, encaisse un paiement réel et suit la
fabrication **sans jamais ouvrir Swagger** ni toucher au code.

## 2. Objectifs, hors périmètre, et ce qui serait un échec

**Objectifs**
1. Corriger le bug B28 (bouton « afficher le mot de passe »).
2. Boutique en trois univers fixes (Meubles, Céramique, Papeterie), catégories gérées par
   l'artisane.
3. Teintes de finition gérées par l'artisane, choisies par le client sur la fiche produit.
4. Parcours demande → devis → paiement Stripe → fabrication → livraison, avec expiration,
   annulation et remboursement.
5. Pages légales (CGV, mentions légales, confidentialité) et acceptation des CGV avant paiement.
6. Mise en ligne sur Render, sécurisée.

**Hors périmètre (noté pour plus tard)**
- Acompte : **paiement total uniquement** (décision de l'artisane). Un acompte optionnel pourra
  être ajouté dans les paramètres plus tard.
- Comptes clients (le lien secret par e-mail en tient lieu).
- Teintes qui modifient automatiquement le prix : l'artisane ajuste le prix dans le devis.
- Options de personnalisation structurées (type de bois…) : en attente de l'artisane ; le champ
  « souhait » libre les couvre.
- Ajout d'un quatrième univers depuis le back-office.
- Partenariat Rubio : question commerciale, hors code.

**Ce qui serait un échec même si « ça marche »**
- Le site voit, transmet ou stocke un numéro de carte bancaire.
- Un client est débité sans avoir accepté le devis et les CGV, ou d'un montant différent du devis.
- Un inconnu peut lire le devis d'un autre client (identifiant devinable dans l'URL).
- Une demande ou un paiement se perd (e-mail non parti sans trace, paiement Stripe non rattaché).
- Le paiement est marqué « payé » sur la seule foi du retour du navigateur, sans confirmation
  signée de Stripe.
- Une photo de produit trompeuse sur le meuble réellement vendu.

## 3. Décisions prises avec l'artisane (via Rémy)

| Sujet | Décision |
|---|---|
| Stock | Aucun. Tout est fabriqué sur commande. |
| Univers | Meubles, Céramique, Papeterie ; tout fabriqué par l'artisane. Fixes. |
| Navigation | `/boutique` = trois grandes photos (une par univers) → page de l'univers avec ses catégories et produits (maquette C validée). |
| Prix affiché | « À partir de X € » ; peut monter ou baisser. Mention : le prix final peut varier selon la finition et les souhaits, confirmé dans le devis. |
| Panier | Conservé, plusieurs pièces de n'importe quel univers. |
| Personnalisation | Un champ libre « Votre souhait pour cette pièce », rattaché à chaque pièce ; une teinte au choix parmi celles proposées pour le produit, montrée par une petite image carrée (maquette validée). |
| Devis | L'artisane fixe le prix final de chaque pièce et les frais de livraison. |
| Validité du devis | 30 jours. |
| Paiement | Totalité en ligne, après acceptation du devis. Pas d'acompte. |
| Garantie | Fabrication + livraison sous 15 jours après le paiement, « sauf cas extrême ». |
| Annulation avant paiement | Le client refuse le devis, ou le laisse expirer. |
| Annulation payée, fabrication pas commencée | Remboursement total. |
| Annulation fabrication commencée | « Contactez l'atelier » ; l'artisane décide au cas par cas. |
| Hébergement | Render, région Europe (Francfort). |

## 4. Parcours client

### 4.1 Boutique

- `/boutique` : trois grandes images, Meubles, Céramique, Papeterie. Image d'ambiance provisoire
  par univers, remplaçable.
- `/boutique/:univers` (`meubles`, `ceramique`, `papeterie`) : titre de l'univers, filtres par
  catégorie de cet univers (« Tout » + chaque catégorie), grille des produits visibles.
- `/boutique/:univers/:categorie` : même page, catégorie présélectionnée (slug de catégorie).
- Un univers sans aucun produit visible affiche « Bientôt disponible » plutôt qu'une page vide.
- Fiche produit : l'URL actuelle `/produits/:id` est conservée.

### 4.2 Fiche produit

Maquette validée (`fiche-produit-teintes.html`, voir §12) :
- galerie de photos (existante) ;
- nom, « À partir de X € », description, dimensions ;
- **Finition** : rangée d'images carrées avec le nom de chaque teinte proposée pour ce produit ;
  « Naturel » sélectionné par défaut s'il est proposé ; aucune rangée si le produit n'a pas de
  teinte (ex. papeterie) ;
- phrase : « Le prix final peut varier selon la finition et vos souhaits ; il est confirmé dans
  votre devis. » ;
- **« Votre souhait pour cette pièce (facultatif) »** : zone de texte, 500 caractères max ;
- quantité (1 à 10) et bouton **« Ajouter à ma demande »** ;
- mention « Fabriqué à la commande · Fabrication et livraison garanties sous 15 jours après
  paiement ».

Deux ajouts du même produit avec une teinte ou un souhait différents font **deux lignes**
distinctes dans la demande ; le même produit avec la même teinte et le même souhait cumule la
quantité (plafond 10).

### 4.3 Ma demande (ancien panier)

- `/demande` : chaque ligne montre photo, nom, quantité, teinte (pastille + nom), souhait, prix
  « dès » ; on peut modifier la quantité, la teinte, le souhait, ou retirer la ligne.
- Total indicatif « à partir de », « hors livraison », et : « Rien n'est payé maintenant : vous
  recevez votre devis sous 48 h. »
- Sauvegardée dans le `localStorage` comme le panier actuel. L'entête affiche « Ma demande (n) ».
- `/demande/envoi` : nom, e-mail, téléphone (facultatif), adresse de livraison, message général
  (facultatif) → « Envoyer ma demande ».
- `/demande/confirmation` : « Demande n°X reçue. Maison Guillard vous envoie votre devis sous
  48 h. » La demande locale est vidée.
- E-mails : accusé de réception au client, notification à l'artisane.

### 4.4 Projet libre depuis la page Contact

Le formulaire de devis libre actuel reste. Il crée une **demande sans ligne de catalogue**, avec la
description du projet (et le produit d'origine en référence si l'on vient d'une fiche produit). Il
arrive dans le même onglet du back-office que les autres demandes.

### 4.5 Page du devis (lien secret)

Le client reçoit par e-mail un lien `https://<domaine>/devis/<jeton>`. Cette page est la seule
« espace client » : elle affiche toujours l'état à jour de sa demande.

| État de la demande | Ce que voit le client |
|---|---|
| en attente du devis | récapitulatif de la demande, « votre devis arrive sous 48 h » |
| devis envoyé, valide | détail : chaque pièce (teinte, souhait, prix final), frais de livraison, total, message de l'artisane, date d'expiration, mention garantie 15 jours ; case **« J'accepte les conditions générales de vente »** (lien vers les CGV) ; boutons **« Accepter et payer »** et **« Refuser le devis »** |
| devis expiré | « Ce devis a expiré le JJ/MM. Contactez l'atelier pour en recevoir un nouveau. » ; pas de paiement possible |
| refusé | « Vous avez refusé ce devis. » |
| payée | « Paiement reçu le JJ/MM. Livraison prévue au plus tard le JJ/MM. » + bouton **« Annuler ma commande »** (remboursement total) |
| en fabrication / expédiée / livrée | statut et date limite ; « Pour toute demande, contactez l'atelier » (e-mail, téléphone) ; plus de bouton d'annulation |
| annulée | « Commande annulée », et « remboursée le JJ/MM » si un remboursement a eu lieu |

« Accepter et payer » exige la case CGV cochée, puis redirige vers la page de paiement hébergée
par Stripe (Checkout). Au retour : `/devis/<jeton>?paiement=ok` affiche « Paiement en cours de
confirmation… » jusqu'à ce que le backend ait reçu la confirmation signée de Stripe (rafraîchir
l'état toutes les 2 à 3 s, une minute maximum), puis l'état « payée ». `?paiement=annule` revient
simplement sur le devis.

## 5. Back-office

L'existant est conservé (connexion, structure, onglet Produits avec photos). Changements :

### 5.1 Onglet « Demandes » (remplace « Commandes » et « Devis »)

- Liste, plus récentes d'abord, filtre par statut. Colonnes : n°, date, client, nombre de pièces,
  total (indicatif ou final), statut, **date limite** des 15 jours si payée.
- Date limite mise en évidence quand il reste 3 jours ou moins, et en rouge quand elle est
  dépassée, tant que la commande n'est pas livrée ni annulée.
- **Détail d'une demande** :
  - coordonnées du client, message général, description du projet libre le cas échéant ;
  - chaque ligne : produit, quantité, teinte, souhait, prix indicatif, **prix final** (champ
    pré-rempli avec le prix indicatif) ;
  - possibilité d'**ajouter une ligne libre** (libellé + prix + quantité), nécessaire pour chiffrer
    un projet libre ou un supplément ;
  - **frais de livraison** (champ, 0 accepté), **pré-remplis** depuis les réglages (§5.7) ;
  - **message au client** (facultatif), avec un menu pour **insérer un message type** (§5.7) ;
  - total final calculé en direct ;
  - bouton **« Aperçu »** : affiche le **PDF exact** que recevra le client (maquette validée
    `devis-pdf-apercu.html`), avec « Retour à l'édition », « Télécharger le PDF » et « Envoyer le
    devis » ;
  - **« Envoyer le devis »** (depuis l'édition ou l'aperçu) : refusé avec un message clair tant que
    les mentions obligatoires des réglages (§5.7) manquent ; sinon fige les prix, attribue le
    numéro (§5.8), fixe l'expiration (durée des réglages, 30 jours par défaut), génère le PDF et
    envoie l'e-mail avec le lien **et le PDF en pièce jointe**. Le lien est aussi affiché avec un
    bouton « Copier » (si l'e-mail n'arrive pas).
  - Une fois envoyé : prix en lecture seule. **« Modifier et renvoyer le devis »** rouvre l'édition
    tant que le client n'a pas payé ; le renvoi remplace l'ancien devis (nouvelle version du numéro,
    nouvelle expiration, nouvel e-mail ; le même lien affiche la nouvelle version).
  - Le PDF de la version en cours est téléchargeable depuis le détail de la demande.
- **Actions selon le statut** : « Passer en fabrication » (payée → en fabrication), « Expédiée »,
  « Livrée », « Rembourser » (payée ou en fabrication → remboursement total Stripe, statut annulée),
  « Annuler la demande » (avant paiement, sans remboursement).

### 5.2 Onglet « Catégories » (nouveau)

Liste groupée par univers ; créer (nom, univers ; slug généré depuis le nom et modifiable),
renommer, changer d'univers, supprimer (refusée avec message si des produits l'utilisent — règle
existante, 409).

### 5.3 Onglet « Teintes » (nouveau)

Liste ordonnée ; créer (nom + image carrée envoyée comme une photo), modifier, réordonner,
désactiver. Une teinte utilisée dans une demande existante ne peut pas être supprimée, seulement
désactivée (elle n'est plus proposée, mais reste affichée dans les anciennes demandes).

### 5.4 Fiche produit (back-office)

- Le champ « disponibilité » disparaît ; nouvelle case **« Visible sur le site »**.
- Le prix devient le prix « à partir de ».
- Cases à cocher des **teintes proposées** pour ce produit.
- Validation : prix strictement positif, nom non vide (corrige B22 et B23).

### 5.5 Paramètres

Les réglages deviennent la page « Réglages du devis » (§5.7). L'interrupteur des e-mails disparaît : en v2, les e-mails font partie du parcours (le lien du devis
part par e-mail). Si un envoi échoue, l'erreur est journalisée et le back-office affiche le lien à
copier.

### 5.7 Réglages du devis (nouvelle page)

Page du back-office où l'artisane configure ce qui revient dans chaque devis. Les valeurs réelles
ne sont pas encore connues : le seed met des valeurs d'exemple, signalées « à compléter » dans la
page.

- **Identité de l'entreprise** (sur chaque PDF) : nom commercial, forme et nom légal (ex.
  « EI Prénom Nom »), adresse de l'atelier, SIRET, e-mail, téléphone, prénom de signature du mot de
  l'atelier, mention de TVA (texte libre, ex. « TVA non applicable, art. 293 B du CGI »).
  **Obligatoires pour envoyer un devis** : nom légal, adresse, SIRET, e-mail.
- **Durée de validité** des devis, en jours (30 par défaut).
- **Frais de livraison par défaut** pour chaque univers. Règle provisoire pour une demande qui
  mélange plusieurs univers : on pré-remplit les frais **les plus élevés** parmi les univers
  présents ; l'artisane corrige si besoin. Règle à revoir avec elle, à isoler dans une seule
  fonction.
- **Messages types** : liste (titre + texte) qu'elle crée, modifie, supprime, et insère dans le
  message d'un devis en un clic (le texte reste modifiable après insertion).
- **Textes des conditions** affichés en bas du devis : paiement, fabrication et livraison,
  annulation (valeurs par défaut reprises de §3, modifiables).

### 5.8 Le PDF du devis

- Mise en page de la maquette validée `devis-pdf-apercu.html` (A4, style du site : logo, noir et
  blanc, Jost) : en-tête de l'atelier ; « DEVIS » ; numéro, date d'émission, date d'expiration ;
  client et rappel de la demande ; tableau des pièces (désignation, dimensions, teinte avec sa
  pastille, souhait du client, quantité, prix unitaire, total) ; sous-total, livraison, total à
  régler, mention de TVA ; « Le mot de l'atelier » ; les trois conditions ; zone « Bon pour
  accord » ; pied de page avec le nom légal, le SIRET et la pagination. Un devis long passe sur
  plusieurs pages, l'en-tête du tableau répété.
- **Numérotation** : `D-<année>-<n° sur 4 chiffres>`, séquence continue et sans trou, attribuée au
  premier envoi ; chaque renvoi ajoute une version (`D-2026-0001-v2`).
- Généré **côté serveur à partir des données figées** du devis : le même devis donne toujours le
  même PDF. L'aperçu utilise exactement le même rendu que le PDF envoyé.
- Après paiement, la zone « Bon pour accord » affiche la date et l'heure d'acceptation en ligne et
  la version des CGV acceptée. Le PDF téléchargeable depuis la page du client et le back-office
  reflète cet état.
- Accessible au client uniquement par son lien secret (`/devis/<jeton>`), jamais par un identifiant.

### 5.9 Bug B28 (connexion)

Masquer le bouton natif d'Edge (`input::-ms-reveal { display: none; }`) et ajouter un bouton
« Afficher / Masquer » propre au site sur le champ mot de passe de `PageConnexionAdmin.jsx`.

## 6. Données

Pas de données de production à reprendre : la v1 n'a jamais été en ligne. La migration Alembic de
la v2 peut restructurer librement. Le seed de démonstration est adapté au nouveau modèle.

### 6.1 Changements

- **`categorie`** : + `univers` (énumération `meubles | ceramique | papeterie`, obligatoire). Le
  slug d'une catégorie reste unique sur tout le site ; format contrôlé `^[a-z0-9-]+$` (corrige B24).
- **`produit`** : − `disponibilite` ; + `visible` (booléen, vrai par défaut). `prix` = prix « à
  partir de », `> 0`.
- **`teinte`** (nouvelle) : `id`, `nom`, `image_url`, `ordre`, `active`.
- **`produit_teinte`** (nouvelle, table de liaison) : `produit_id` → produit (CASCADE),
  `teinte_id` → teinte (RESTRICT) ; clé primaire composée.
- **`demande`** (remplace `commande` et `devis`) :
  - client : `nom_client`, `email`, `telephone` (facultatif), `adresse`, `message_client`
    (facultatif), `description_projet` (facultatif, projet libre), `produit_reference_id`
    (facultatif, SET NULL) ;
  - `jeton` : chaîne aléatoire unique d'au moins 32 octets (`secrets.token_urlsafe(32)`), indexée ;
  - `statut` (énumération, §6.2) ;
  - devis : `frais_livraison`, `message_artisane`, `devis_envoye_at`, `expire_at` ;
  - client : `cgv_acceptees_at`, `cgv_version` ;
  - paiement : `stripe_session_id`, `stripe_payment_intent_id`, `montant_paye`, `payee_at` ;
  - suivi : `date_limite` (= `payee_at` + 15 jours), `rembourse_at`, `created_at`.
- **`ligne_demande`** (remplace `ligne_commande`) : `demande_id` (CASCADE), `produit_id`
  (facultatif, RESTRICT : un produit déjà demandé ne se supprime pas, on le masque), `libelle`
  (copie du nom du produit, ou texte d'une ligne libre), `quantite` (1 à 10), `teinte_id`
  (facultatif, RESTRICT) + `teinte_nom` (copie), `souhait` (facultatif, 500 max),
  `prix_indicatif` (copie du prix « à partir de » à l'envoi de la demande), `prix_final`
  (facultatif jusqu'au devis).
- **`demande`** reçoit aussi : `numero_devis` (unique, attribué au premier envoi),
  `version_devis` (1, 2…), et une copie figée de ce que le PDF affiche et qui pourrait changer dans
  les réglages ensuite (identité de l'entreprise, mention de TVA, textes des conditions).
- **Réglages du devis** : la table `parametre` (une seule ligne) est étendue avec les champs de
  §5.7 ; `email_commande_actif` est supprimé. Frais par univers : une colonne par univers, ou une
  petite table, au choix du constructeur.
- **`message_type`** (nouvelle) : `id`, `titre`, `texte`, `ordre`.
- **Séquence des numéros de devis** : un compteur par année, attribué dans la même transaction que
  l'envoi (pas de doublon ni de trou, même avec deux envois simultanés).
- Totaux non stockés, recalculés (`@property`), comme aujourd'hui.
- Les tables `commande`, `ligne_commande` et `devis` sont supprimées par la migration (types
  énumérés compris, `downgrade` réversible).

### 6.2 Statuts de `demande`

```
nouvelle ──(devis envoyé)──▶ devis_envoye ──(payé, webhook Stripe)──▶ payee ──▶ en_fabrication ──▶ expediee ──▶ livree
    │                           │  ▲ (modifier et renvoyer)              │              │
    │                           │  └────────────┘                        │              │
    │                           ├──(client refuse)──▶ refusee            │              │
    │                           └──(30 jours passés)──▶ expiree          │              │
    └──(artisane annule)──▶ annulee ◀──(client annule : remboursement)──┘              │
                                    ◀──(artisane rembourse)─────────────────────────────┘
```

- Les transitions sont **contrôlées par le service** (contrairement à la v1) : toute transition non
  prévue répond 409.
- L'expiration est **paresseuse** : pas de tâche planifiée ; une demande `devis_envoye` dont
  `expire_at` est passée est traitée et affichée comme `expiree` à la lecture, et enregistrée comme
  telle à ce moment-là.
- Un devis expiré peut être **renvoyé** par l'artisane (« Modifier et renvoyer »), ce qui le
  remet en `devis_envoye` avec une nouvelle expiration.

## 7. Paiement (Stripe)

- **Stripe Checkout (page hébergée)**. Le site ne voit jamais de donnée de carte.
- Quand le client clique sur « Accepter et payer » (devis valide, CGV cochées) : le backend
  enregistre `cgv_acceptees_at`/`cgv_version`, crée une session Checkout avec une ligne par pièce
  (`prix_final` × quantité) et une ligne « Livraison », en euros, **montants lus en base**,
  `metadata.demande_id`, `customer_email`, et une expiration de session au plus tard à
  `expire_at` du devis (dans la limite de Stripe). Il répond l'URL de la session ; le frontend y
  redirige.
- **Webhook** `POST /api/stripe/webhook` : signature vérifiée avec `STRIPE_WEBHOOK_SECRET` (sinon
  400). Sur `checkout.session.completed` avec paiement réussi : passer la demande en `payee`,
  enregistrer `stripe_payment_intent_id`, `montant_paye`, `payee_at`, `date_limite`, envoyer les
  e-mails. **Idempotent** : un même événement reçu deux fois ne fait rien la seconde fois.
  Si le montant payé ne correspond pas au total du devis, la demande n'est pas marquée payée et
  l'erreur est journalisée.
- **Remboursement** : `stripe.Refund.create(payment_intent=…)` pour la totalité ; statut `annulee`,
  `rembourse_at`, e-mails au client et à l'artisane. Déclenché par le client (statut `payee`
  seulement) ou par l'artisane (`payee` ou `en_fabrication`). En cas d'échec Stripe, le statut ne
  change pas et une erreur claire est affichée.
- Développement en **mode test** Stripe (cartes de test, Stripe CLI pour relayer le webhook en
  local). Passage aux clés réelles seulement à la mise en ligne, sur le compte Stripe **de
  l'artisane**.

## 8. E-mails

Envoyés en tâche de fond (mécanisme existant), via le SMTP de **Brevo** en production. Tous
contiennent le lien de la demande quand il existe.

| Événement | Client | Artisane |
|---|---|---|
| Demande reçue | accusé de réception | nouvelle demande n°X |
| Devis envoyé / renvoyé | votre devis, lien, date d'expiration | — |
| Paiement reçu | confirmation, date limite de livraison | commande n°X payée, à fabriquer avant le JJ/MM |
| Devis refusé | — | devis n°X refusé |
| Annulation par le client (remboursée) | confirmation du remboursement | commande n°X annulée et remboursée |
| Remboursement par l'artisane | confirmation du remboursement | — |
| Expédiée | votre commande est expédiée | — |

## 9. Pages légales

- `/cgv`, `/mentions-legales`, `/confidentialite`, liées depuis le pied de page.
- Contenu fourni par l'artisane ; en attendant, un texte modèle clairement marqué **« À faire
  valider par un professionnel »**, couvrant au minimum : fabrication sur commande, prix confirmé
  au devis, paiement total, délai de 15 jours sauf cas extrême, annulation et remboursement selon
  §3, hébergeur (Render), traitement des données (Stripe, Brevo, Cloudinary).
- La version des CGV acceptée est enregistrée avec la demande (`cgv_version`, une constante de
  configuration).
- Pas de cookie de mesure d'audience, donc pas de bandeau cookies (le stockage local ne sert qu'à
  la demande en cours et au jeton admin).

## 10. Sécurité

- Jeton de demande aléatoire et long ; aucune route publique n'accepte un `id` de demande.
- Limite de requêtes par IP sur les routes publiques d'écriture (`POST` de demande, de projet
  libre, de paiement, d'annulation) et sur la connexion admin, réponse 429 (corrige B26).
- Montants toujours relus en base ; jamais acceptés depuis le navigateur.
- Webhook Stripe : signature obligatoire.
- Secrets uniquement dans les variables d'environnement de Render ; `JWT_SECRET` neuf et long en
  production.
- HTTPS partout (fourni par Render), CORS restreint au domaine du site.
- Validation Pydantic sur toutes les entrées nouvelles (longueurs, quantités, montants ≥ 0).

## 11. Mise en ligne (Render)

- **Base** : PostgreSQL géré Render, région Francfort, sauvegardes activées.
- **API** : service web Render (Python), `alembic upgrade head` avant le démarrage d'Uvicorn.
- **Site** : site statique Render (`npm run build`), avec réécriture de toutes les routes vers
  `index.html` (application à une page).
- Le frontend et l'API doivent fonctionner **sous le même domaine** ou avec CORS correctement
  réglé (choix laissé au constructeur, voir §13).
- **Photos** : `photo_service.upload_to_cloudinary` implémenté pour de vrai (le disque de Render est
  effacé à chaque déploiement). Les images des teintes et des univers passent par le même chemin.
- **E-mails** : Brevo (SMTP), adresse d'expédition au nom de Maison Guillard.
- **Domaine** : acheté par l'artisane, relié à Render.
- Déploiement automatique à chaque fusion sur `main`, décrit dans un fichier `render.yaml` versionné.
- `docs/deploiement.md` et le README sont mis à jour.

## 12. Maquettes validées

Dans `docs/specs/maquettes-v2/` (à ouvrir dans un navigateur) :
- `boutique-univers.html` — option **C** retenue (trois grandes images) ;
- `fiche-produit-teintes.html` — fiche produit (teintes + souhait) et page « Ma demande » ; ajouter
  sous les teintes : « Le prix final peut varier selon la finition et vos souhaits ; il est confirmé
  dans votre devis. » ;
- `devis-pdf-apercu.html` — aperçu et PDF du devis, validé tel quel (les valeurs surlignées en
  jaune viennent des réglages ; client et prix inventés).

Le style reste celui du site actuel (noir et blanc, Jost Light).

## 13. Laissé au constructeur

- Découpage en lots et ordre de construction (suggestion : B28 → catalogue (univers, catégories,
  visibilité, teintes) → demande/devis → paiement/annulation → pages légales et sécurité →
  Cloudinary, Brevo et Render).
- Bibliothèque de limitation de requêtes, valeurs des limites.
- Même domaine (réécriture `/api` vers le service API) ou deux sous-domaines avec CORS.
- Détail visuel des pages, dans le style existant.
- Nom exact des routes de l'API, dans la convention existante (`/api/...`, français).
- Remplacement éventuel de `python-jose` par `PyJWT` (B27) si cela ne complique rien.

## 14. Choix de conception à vérifier

Décidés pendant la rédaction, sans avoir été discutés ; à corriger si besoin :

- **Factures** : pas de génération de factures PDF en v2. Stripe envoie un reçu au client à chaque
  paiement ; l'artisane établit ses factures avec son outil habituel.
- **Mention de TVA** : réglée dans « Réglages du devis » (§5.7) ; affichée sur le devis et la page
  du devis.
- **Bibliothèque de génération du PDF** : au choix du constructeur, pourvu que l'aperçu et le PDF
  envoyé sortent du même rendu et qu'elle s'installe sur Render.
- **Images des univers** : des fichiers du site, remplaçables par le développeur ; pas d'écran
  d'administration pour elles.
- **Une seule adresse** par demande, utilisée pour la livraison.
- **E-mails obligatoires** : l'interrupteur actuel disparaît (§5.5).
- **Données de démonstration** : le seed couvre les trois univers et quelques teintes.

## 15. À fournir par l'artisane (ne bloque pas la construction)

Compte Stripe à son nom, nom de domaine, texte des CGV validé, identité légale et SIRET pour le
devis, frais de livraison par univers et règle pour les demandes mixtes, messages types, photos des teintes et des trois
univers, vrais produits et prix, coordonnées réelles. Plus tard : options de personnalisation,
réponse sur Rubio.
