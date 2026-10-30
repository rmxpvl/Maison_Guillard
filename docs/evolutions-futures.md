# Maison Guillard — Évolutions futures

Liste des améliorations envisagées après le MVP, regroupées par thème. Chaque point indique d'où il
vient (résumé de bloc, tests manuels, bible). Rien ici n'est nécessaire au fonctionnement actuel :
ce sont les prochaines étapes, pas des bugs bloquants.

**À citer en priorité si on demande « et ensuite ? »** : la protection anti-abus, les comptes
clients, le paiement en ligne.

---

## Sécurité

1. **Protection anti-abus sur les formulaires publics.** `POST /api/commandes` et `POST /api/devis`
   sont publics : un script pourrait les appeler en boucle, polluer le back-office et envoyer du
   spam par les e-mails automatiques. Correction prévue : une limite de requêtes par adresse IP
   (`slowapi` côté FastAPI, ou Nginx en production), avec une réponse **429 Too Many Requests**
   au-delà ; éventuellement un champ piège (honeypot) ou un CAPTCHA.
   *Source : résumés S7 et S9.*
2. **HTTPS au déploiement.** En local, tout est en HTTP. En production, un certificat
   (Let's Encrypt) et une redirection de tout le trafic HTTP vers HTTPS.
3. **Rôles d'administration.** Un seul compte administrateur aujourd'hui, sans rôles.

## Validation des données

Constatées pendant les tests manuels (`docs/tests-api.md`), pas encore corrigées :

4. **Refuser un prix négatif ou nul** pour un produit (`Field(gt=0)` sur `prix`).
5. **Refuser un nom de produit vide** (`Field(min_length=1)` sur `nom`).
6. **Contrôler le format du slug** d'une catégorie (minuscules, chiffres et tirets seulement),
   puisqu'il sert dans l'URL `/boutique/<slug>`.

La correction tient dans les schémas Pydantic (`app/schemas/produit.py`, `app/schemas/categorie.py`),
sur le modèle de ce qui existe déjà pour les quantités (`Field(ge=1, le=10)`).

## Back-office

7. **Pagination et recherche** dans les listes. Tout est chargé d'un coup : l'affichage
   ralentirait au-delà de quelques milliers de lignes. La pagination s'ajoute sans rien casser.
   *Source : résumé S9.*
8. **Gestion des catégories dans l'interface.** Aujourd'hui, uniquement par Swagger.
   *Source : résumé S9.*
9. **Modification d'une catégorie** (`PUT /api/categories/{id}`) : seulement création et
   suppression aujourd'hui. *Source : récapitulatif S5.*

## Fonctionnalités pour les clients

10. **Comptes clients avec historique des commandes.** Recommandé par mon manager comme un plus ;
    gardé volontairement pour après le MVP afin de livrer un périmètre stable et testé.
    Ce que cela demande :
    - un modèle `Client` et sa migration Alembic ;
    - inscription et connexion, en réutilisant bcrypt et le JWT de l'admin (avec un rôle distinct) ;
    - une colonne `commande.client_id` **facultative**, pour que la commande sans compte reste
      possible ;
    - une route et une page « Mes commandes » ; le formulaire de commande pré-rempli ;
    - côté sécurité et RGPD : mot de passe oublié par e-mail, suppression du compte, limitation des
      tentatives de connexion.
11. **Champs supplémentaires dans le devis** : budget, délai, dimensions, photo d'inspiration,
    si l'artisane le souhaite. *Source : résumé S8.*
12. **Paiement en ligne**, si l'artisane le souhaite. Aujourd'hui, le paiement et la livraison se
    règlent directement avec elle.
13. **Prix à jour dans le panier.** Si l'artisane change un prix pendant qu'un client a le produit
    dans son panier, le panier affiche l'ancien prix (la commande et la confirmation, elles,
    utilisent le bon prix, relu en base). *Source : résumé S7.*

## Mise en ligne

14. **Brancher Cloudinary** pour les photos : une seule fonction à remplacer,
    `photo_service.upload_to_cloudinary`.
15. **Un `.env` de production** : nouveau `JWT_SECRET` long et aléatoire, SMTP de l'hébergeur,
    `EMAIL_ARTISAN` avec la vraie adresse. Aucun changement de code nécessaire.
16. **Base de production** : `alembic upgrade head` une fois, et des sauvegardes régulières.
17. **Le site construit** avec `npm run build` et servi avec l'API derrière un même domaine
    (Nginx), puisque le proxy de Vite n'existe qu'en développement.
18. **Vraies coordonnées** dans `frontend/src/config/coordonnees.js` et **vraies photos** des
    pièces, toujours prises dans le même décor (mur sombre, lumière latérale) avec le même réglage
    de retouche.
