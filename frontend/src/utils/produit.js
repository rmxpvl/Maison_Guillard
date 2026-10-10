export const DISPONIBILITES = ['disponible', 'sur_commande', 'rupture']

const LIBELLES = {
  disponible: 'Disponible',
  sur_commande: 'Sur commande',
  rupture: 'Vendu',
}

export function libelleDisponibilite(disponibilite) {
  return LIBELLES[disponibilite] ?? disponibilite
}

// Anything typed by hand in the URL that the API wouldn't accept is ignored.
export function disponibiliteValide(valeur) {
  return DISPONIBILITES.includes(valeur) ? valeur : null
}

const formateurPrix = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' })

// The API sends prix as a decimal string ("199.99").
export function formatPrix(prix) {
  return formateurPrix.format(Number(prix))
}

export function prixAffiche(produit) {
  const prix = formatPrix(produit.prix)
  return produit.disponibilite === 'sur_commande' ? `À partir de ${prix}` : prix
}

export function photoPrincipale(photos) {
  if (!photos || photos.length === 0) return null
  return photos.find((p) => p.principale) ?? [...photos].sort((a, b) => a.ordre - b.ordre)[0]
}

export function parseIdProduit(valeur) {
  return /^[1-9]\d*$/.test(valeur ?? '') ? Number(valeur) : null
}

const ACTIONS = {
  disponible: [
    { libelle: 'Ajouter au panier', principale: true },
    { libelle: 'Personnaliser ce modèle', principale: false },
  ],
  sur_commande: [{ libelle: 'Demander un devis', principale: true }],
  rupture: [{ libelle: 'Demander un modèle similaire', principale: false }],
}

export function actionsFiche(disponibilite) {
  return ACTIONS[disponibilite] ?? []
}

const RANG_DISPONIBILITE = { disponible: 0, sur_commande: 1, rupture: 2 }

// Home page selection: only produits that have a photo, purchasable ones first.
// Array.prototype.sort is stable, so the API order is kept among equals.
export function piecesChoisies(produits, n) {
  return produits
    .filter((p) => p.photos?.length > 0)
    .sort((a, b) => (RANG_DISPONIBILITE[a.disponibilite] ?? 3) - (RANG_DISPONIBILITE[b.disponibilite] ?? 3))
    .slice(0, n)
}

// Shop order for a vitrine: produits with photos first, API order kept otherwise.
// Copies the array so the API data itself is never reordered.
export function avecPhotosDabord(produits) {
  const aUnePhoto = (p) => (p.photos?.length > 0 ? 0 : 1)
  return [...produits].sort((a, b) => aUnePhoto(a) - aUnePhoto(b))
}
