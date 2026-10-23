import { photoPrincipale } from './produit.js'

export const QUANTITE_MAX = 10

// Any input (text from a <select>, a number, garbage) becomes an integer between 1 and 10.
function borner(quantite) {
  const n = Math.trunc(Number(quantite))
  if (!Number.isFinite(n) || n < 1) return 1
  return Math.min(n, QUANTITE_MAX)
}

// nom, prix and photo are only for display: the API recomputes the price.
function ligneDepuisProduit(produit) {
  return {
    produit_id: produit.id,
    nom: produit.nom,
    prix: produit.prix,
    photo: photoPrincipale(produit.photos)?.url ?? null,
    quantite: 1,
  }
}

export function ajouterLigne(lignes, produit) {
  if (lignes.some((l) => l.produit_id === produit.id)) {
    return lignes.map((l) => (l.produit_id === produit.id ? { ...l, quantite: borner(l.quantite + 1) } : l))
  }
  return [...lignes, ligneDepuisProduit(produit)]
}

export function changerQuantiteLigne(lignes, produitId, quantite) {
  return lignes.map((l) => (l.produit_id === produitId ? { ...l, quantite: borner(quantite) } : l))
}

export function retirerLigne(lignes, produitId) {
  return lignes.filter((l) => l.produit_id !== produitId)
}

export function compterArticles(lignes) {
  return lignes.reduce((somme, l) => somme + l.quantite, 0)
}

export function totalPanier(lignes) {
  return lignes.reduce((somme, l) => somme + Number(l.prix) * l.quantite, 0)
}

// localStorage can hold anything (old format, hand edits): keep it only if it looks right.
export function lignesValides(valeur) {
  if (!Array.isArray(valeur)) return []
  const ok = valeur.every(
    (l) => l && Number.isInteger(l.produit_id) && Number.isInteger(l.quantite) && typeof l.nom === 'string',
  )
  return ok ? valeur : []
}

export function lignesPourApi(lignes) {
  return lignes.map((l) => ({ produit_id: l.produit_id, quantite: l.quantite }))
}
