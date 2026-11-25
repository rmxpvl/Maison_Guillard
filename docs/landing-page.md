# Landing page du projet portfolio

La page de présentation du projet (exigée par Holberton) est dans le dossier `landing/` : du HTML, du
CSS et un tout petit JavaScript, sans outil de construction. Elle est publiée avec **GitHub Pages**.

## Ce que l'énoncé demande, et où le trouver

| Exigence | Où |
|---|---|
| Grande image de couverture, nom du projet, phrase d'accroche | Bandeau du haut (`#projet`) |
| Navigation vers au moins 2 sections | Menu : Le projet, Fonctionnalités, Sous le capot, À propos |
| Bouton vers l'application déployée | « Essayer l'application » / « Voir l'application » (en-tête et bandeau) |
| 3 fonctionnalités : image, nom, description | Section `#fonctionnalites` : boutique sur commande, devis et paiement, gestion de l'artisane |
| À propos : histoire personnelle, liens GitHub / LinkedIn / Twitter, lien du dépôt | Section `#apropos` |

## Publier la page (une seule fois)

1. Fusionner la branche sur `main` : le fichier `.github/workflows/landing-pages.yml` publie alors le
   dossier `landing/` à chaque modification.
2. Sur GitHub : **Settings > Pages > Build and deployment > Source : « GitHub Actions »**.
3. Dans l'onglet **Actions**, ouvrir « Landing page » : l'adresse publiée s'affiche en fin de
   déploiement. Elle sera de la forme `https://rmxpvl.github.io/Maison_Guillard/`. C'est cette
   adresse à rendre comme « Landing Page URL ».

Pour republier à la main : Actions > « Landing page » > « Run workflow ».

## Ce qu'il reste à renseigner : `landing/config.js`

Un seul fichier à modifier, rien dans le HTML :

```js
window.LANDING = {
  urlApplication: '',  // l'adresse du site déployé, dès qu'elle existe
  linkedin: '',        // ton profil LinkedIn
  twitter: '',         // ton compte Twitter / X
}
```

- **`urlApplication`** : tant qu'elle est vide, les boutons s'appellent « Essayer l'application » et
  mènent aux instructions d'installation du dépôt. Une fois l'adresse renseignée, ils s'appellent
  « Voir l'application » et ouvrent le site. **L'énoncé demande un bouton vers l'application
  déployée : à remplir avant le rendu.**
- **`linkedin` et `twitter`** : le lien n'apparaît dans « À propos » que s'il est renseigné. L'énoncé
  demande les trois profils (LinkedIn, GitHub, Twitter) : à compléter avant le rendu.

## Version anglaise

`landing/en/index.html` est la traduction de la page : elle réutilise le même `style.css`, `script.js`,
`config.js` et le dossier `assets/`. Elle est publiée à `https://rmxpvl.github.io/Maison_Guillard/en/`.
Un bouton FR / EN dans l'en-tête permet de passer de l'une à l'autre. Quand tu modifies un texte dans
`landing/index.html`, répète la modification dans `landing/en/index.html`.

## Modifier le contenu

- Les textes sont dans `landing/index.html` (l'histoire de la section « À propos » est à relire et à
  corriger avec tes mots).
- Les images sont dans `landing/assets/`. Les captures des fonctionnalités viennent du vrai site, avec des
  données fictives. Pour les refaire : lancer le site en local, ouvrir la page à capturer, et remplacer
  le fichier `fonctionnalite-*.webp` (même nom, format WebP, moins de 100 Ko si possible).
- Pour tester en local : ouvrir `landing/index.html` dans un navigateur, sans serveur.

## Ta vidéo de démonstration (YouTube)

Durée visée : 3 minutes. Prépare avant : le site et le backend lancés en local, Stripe en mode test
(avec `stripe listen`), quelques demandes fictives dans la gestion, et **aucune clé ni mot de passe
visible à l'écran** (ne montre pas le fichier `.env`).

| Temps | Ce qui est à l'écran | Ce que tu dis |
|---|---|---|
| 0:00 – 0:20 | La landing page, puis le site | Ta cousine, son atelier, le besoin : un site qui vend des pièces faites sur commande |
| 0:20 – 1:00 | La boutique, une fiche produit, le choix d'une finition, « Ajouter à ma demande », l'envoi de la demande | Pas de stock, prix « à partir de », le client écrit son souhait |
| 1:00 – 1:40 | La gestion : « Aujourd'hui », la demande reçue, la saisie du prix final, le PDF en aperçu, l'envoi du devis | L'artisane fixe le prix et envoie un devis en PDF |
| 1:40 – 2:15 | L'e-mail reçu, le lien du devis, « Accepter et payer », la page Stripe (carte de test `4242 4242 4242 4242`), « Paiement reçu » | Le client accepte et paie en ligne, sans compte obligatoire |
| 2:15 – 2:40 | La demande payée passe en fabrication ; sur la page du client, « Annuler ma commande » | Suivi en six étapes, remboursement en un clic avant fabrication |
| 2:40 – 3:00 | Les actualités et « Pages du site » : écrire une actualité, changer une photo de la boutique | L'artisane gère son site seule, sans toucher au code. Conclusion : ce que tu as appris, et la suite (mise en ligne) |

Conseils : enregistrer avec OBS Studio ou l'enregistreur de Windows (Win + G), parler lentement, ne pas
cliquer trop vite, zoomer le navigateur à 110 % pour la lisibilité. Sur YouTube, mettre la vidéo en
« Non répertoriée » ou « Publique » (pas « Privée ») pour que les correcteurs puissent l'ouvrir.

## Liste des livrables

- [ ] Landing page publiée, adresse notée (`https://rmxpvl.github.io/Maison_Guillard/`)
- [ ] `urlApplication`, `linkedin` et `twitter` renseignés dans `landing/config.js`
- [ ] Histoire de la section « À propos » relue
- [ ] Vidéo de démonstration sur YouTube, adresse notée
- [ ] Relecture demandée à un pair (ou à un membre de l'équipe pédagogique) avant la date limite
