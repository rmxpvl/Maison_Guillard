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
