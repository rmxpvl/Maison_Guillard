import { photoPrincipale, teintesVisibles } from './produit.js'

export const QUANTITE_MAX = 10
export const SOUHAIT_MAX = 500

// Any input (text from a <select>, a number, garbage) becomes an integer between 1 and 10.
function borner(quantite) {
  const n = Math.trunc(Number(quantite))
  if (!Number.isFinite(n) || n < 1) return 1
  return Math.min(n, QUANTITE_MAX)
}

// nom, prix, photo and teintes are only for display: the API checks and recomputes everything.
function ligneDepuisProduit(produit, teinteId) {
  const teintes = teintesVisibles(produit).map(({ id, nom, image_url }) => ({ id, nom, image_url }))
  return {
    produit_id: produit.id,
    nom: produit.nom,
    prix: produit.prix,
    photo: photoPrincipale(produit.photos)?.url ?? null,
    quantite: 1,
    teintes,
    teinte_id: teintes.some((t) => t.id === teinteId) ? teinteId : null,
    souhait: '',
  }
}

export function ajouterLigne(lignes, produit, teinteId = null) {
  if (lignes.some((l) => l.produit_id === produit.id)) {
    return lignes.map((l) => (l.produit_id === produit.id ? { ...l, quantite: borner(l.quantite + 1) } : l))
  }
  return [...lignes, ligneDepuisProduit(produit, teinteId)]
}

export function changerQuantiteLigne(lignes, produitId, quantite) {
  return lignes.map((l) => (l.produit_id === produitId ? { ...l, quantite: borner(quantite) } : l))
}

// '' or an id that the produit does not offer means « no particular finish ».
export function changerTeinteLigne(lignes, produitId, teinteId) {
  return lignes.map((l) => {
    if (l.produit_id !== produitId) return l
    const id = Number(teinteId)
    return { ...l, teinte_id: l.teintes.some((t) => t.id === id) ? id : null }
  })
}

export function changerSouhaitLigne(lignes, produitId, souhait) {
  return lignes.map((l) => (l.produit_id === produitId ? { ...l, souhait: souhait.slice(0, SOUHAIT_MAX) } : l))
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
    (l) =>
      l &&
      Number.isInteger(l.produit_id) &&
      Number.isInteger(l.quantite) &&
      typeof l.nom === 'string' &&
      Array.isArray(l.teintes) &&
      typeof l.souhait === 'string',
  )
  return ok ? valeur : []
}

export function lignesPourApi(lignes) {
  return lignes.map((l) => ({
    produit_id: l.produit_id,
    quantite: l.quantite,
    teinte_id: l.teinte_id,
    souhait: l.souhait.trim() || null,
  }))
}
