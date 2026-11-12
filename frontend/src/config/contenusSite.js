// The texts and photos of the public pages that the artisane can change from the back-office
// (« Pages du site »). `defaut` is the original text, shown until she changes it; photos have no
// default here, their original is an asset (see imagesParDefaut.js).
// Keep the keys in sync with CLES in backend/app/services/contenu_service.py: a test checks it.

export const PAGES_EDITABLES = [
  { code: 'accueil', titre: 'Page d’accueil', chemin: '/', aide: 'La première page que voient vos visiteurs.' },
  { code: 'boutique', titre: 'Boutique', chemin: '/boutique', aide: 'Les trois photos des rayons : Meubles, Céramique et Papeterie.' },
  { code: 'actualites', titre: 'Actualités', chemin: '/actualites', aide: 'Le titre et l’introduction de la page. Les articles se gèrent dans « Actualités ».' },
  { code: 'apropos', titre: 'Qui sommes-nous', chemin: '/qui-sommes-nous', aide: 'Présentez-vous et présentez votre atelier.' },
  { code: 'contact', titre: 'Contact', chemin: '/contact', aide: 'Le texte et la photo au-dessus du formulaire.' },
]

export const CHAMPS = [
  // ----- accueil
  { cle: 'accueil.image', page: 'accueil', type: 'image', label: 'Grande photo du haut de page', aide: 'Photo large, en largeur de préférence.' },
  { cle: 'accueil.titre', page: 'accueil', type: 'texte', label: 'Titre principal', defaut: 'Mobilier artisanal en bois massif' },
  { cle: 'accueil.sous_titre', page: 'accueil', type: 'texte', label: 'Phrase sous le titre', defaut: 'Pièces dessinées et fabriquées à la main' },
  { cle: 'accueil.univers_titre', page: 'accueil', type: 'texte', label: 'Premier bloc : titre', defaut: 'Le bois, simplement' },
  {
    cle: 'accueil.univers_texte', page: 'accueil', type: 'texte_long', label: 'Premier bloc : texte',
    defaut: 'Des essences choisies pour leur veinage et leur solidité, des lignes épurées, des finitions naturelles. Chaque pièce est pensée pour le quotidien et fabriquée pour durer.',
  },
  { cle: 'accueil.univers_image', page: 'accueil', type: 'image', label: 'Premier bloc : photo', aide: 'Photo en hauteur.' },
  { cle: 'accueil.savoir_faire_titre', page: 'accueil', type: 'texte', label: 'Second bloc : titre', defaut: 'Chaque pièce porte la trace de la main' },
  {
    cle: 'accueil.savoir_faire_texte', page: 'accueil', type: 'texte_long', label: 'Second bloc : texte',
    defaut: 'Débit, assemblage, ponçage, finition : tout se fait à l’atelier, à l’unité ou en petite série, avec le temps qu’il faut.',
  },
  { cle: 'accueil.savoir_faire_image', page: 'accueil', type: 'image', label: 'Second bloc : photo', aide: 'Photo carrée.' },

  // ----- boutique
  { cle: 'boutique.meubles_image', page: 'boutique', type: 'image', label: 'Photo du rayon Meubles', aide: 'Photo en hauteur (format portrait).' },
  { cle: 'boutique.ceramique_image', page: 'boutique', type: 'image', label: 'Photo du rayon Céramique', aide: 'Photo en hauteur (format portrait).' },
  { cle: 'boutique.papeterie_image', page: 'boutique', type: 'image', label: 'Photo du rayon Papeterie', aide: 'Photo en hauteur (format portrait).' },

  // ----- actualités
  { cle: 'actualites.titre', page: 'actualites', type: 'texte', label: 'Titre de la page', defaut: 'Actualités' },
  {
    cle: 'actualites.intro', page: 'actualites', type: 'texte_long', label: 'Introduction',
    defaut: 'Les nouvelles de l’atelier : nouvelles pièces, coulisses de fabrication, rendez-vous.',
  },

  // ----- qui sommes-nous
  { cle: 'apropos.titre', page: 'apropos', type: 'texte', label: 'Titre de la page', defaut: 'Une maison, un atelier, le bois' },
  {
    cle: 'apropos.introduction', page: 'apropos', type: 'texte_long', label: 'Introduction',
    defaut: 'Maison Guillard dessine et fabrique à la main des meubles en bois massif : tables, assises, luminaires. Des pièces simples, pensées pour le quotidien et pour durer.',
  },
  { cle: 'apropos.bandeau_image', page: 'apropos', type: 'image', label: 'Photo en bandeau', aide: 'Photo large, en largeur.' },
  { cle: 'apropos.engagement1_titre', page: 'apropos', type: 'texte', label: 'Engagement 1 : titre', defaut: 'Bois massif' },
  {
    cle: 'apropos.engagement1_texte', page: 'apropos', type: 'texte_long', label: 'Engagement 1 : texte',
    defaut: 'Frêne, chêne, noyer : des essences choisies pour leur solidité et la beauté de leur veinage.',
  },
  { cle: 'apropos.engagement2_titre', page: 'apropos', type: 'texte', label: 'Engagement 2 : titre', defaut: 'Fait à la main' },
  {
    cle: 'apropos.engagement2_texte', page: 'apropos', type: 'texte_long', label: 'Engagement 2 : texte',
    defaut: 'Chaque pièce est débitée, assemblée et finie à l’atelier, à l’unité ou en petite série.',
  },
  { cle: 'apropos.engagement3_titre', page: 'apropos', type: 'texte', label: 'Engagement 3 : titre', defaut: 'Pensé pour durer' },
  {
    cle: 'apropos.engagement3_texte', page: 'apropos', type: 'texte_long', label: 'Engagement 3 : texte',
    defaut: 'Des lignes sobres et des assemblages robustes, pour des meubles qui traversent les années.',
  },
  { cle: 'apropos.demarche_titre', page: 'apropos', type: 'texte', label: 'Notre démarche : titre', defaut: 'Peu de pièces, faites pour durer' },
  {
    cle: 'apropos.demarche_texte', page: 'apropos', type: 'texte_long', label: 'Notre démarche : texte',
    defaut: 'Plutôt que de produire beaucoup, nous prenons le temps de choisir chaque planche, d’ajuster chaque assemblage et de finir chaque surface à la main.',
  },
  { cle: 'apropos.demarche_image', page: 'apropos', type: 'image', label: 'Notre démarche : photo', aide: 'Photo carrée.' },

  // ----- contact
  { cle: 'contact.image', page: 'contact', type: 'image', label: 'Photo', aide: 'Photo en largeur.' },
  { cle: 'contact.titre', page: 'contact', type: 'texte', label: 'Titre', defaut: 'Parlons de votre projet' },
  { cle: 'contact.introduction', page: 'contact', type: 'texte', label: 'Phrase d’accroche', defaut: 'Une pièce du catalogue à adapter, ou un projet à imaginer ensemble.' },
  {
    cle: 'contact.texte', page: 'contact', type: 'texte_long', label: 'Texte',
    defaut: 'Une question sur une pièce, une demande sur mesure : écrivez-nous ou appelez-nous, nous vous répondrons avec plaisir.',
  },
]
