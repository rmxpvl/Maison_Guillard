const formateurPrix = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' })

// The API sends prix as a decimal string ("199.99").
export function formatPrix(prix) {
  return formateurPrix.format(Number(prix))
}

// Everything is made to order: the displayed price is always a starting price.
export function prixAffiche(produit) {
  return `À partir de ${formatPrix(produit.prix)}`
}

export function photoPrincipale(photos) {
  if (!photos || photos.length === 0) return null
  return photos.find((p) => p.principale) ?? [...photos].sort((a, b) => a.ordre - b.ordre)[0]
}

export function parseIdProduit(valeur) {
  return /^[1-9]\d*$/.test(valeur ?? '') ? Number(valeur) : null
}

// Home page selection: produits that have a photo, in API order.
export function piecesChoisies(produits, n) {
  return produits.filter((p) => p.photos?.length > 0).slice(0, n)
}

// Finishes shown to visitors: active ones only, in the artisan's order.
export function teintesVisibles(produit) {
  return (produit.teintes ?? []).filter((t) => t.active).sort((a, b) => a.ordre - b.ordre)
}

// Shop order for a vitrine: produits with photos first, API order kept otherwise.
// Copies the array so the API data itself is never reordered.
export function avecPhotosDabord(produits) {
  const aUnePhoto = (p) => (p.photos?.length > 0 ? 0 : 1)
  return [...produits].sort((a, b) => aUnePhoto(a) - aUnePhoto(b))
}
