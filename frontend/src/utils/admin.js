// Values and French labels, in the order they appear in the status menus.
export const STATUTS_COMMANDE = [
  ['en_attente', 'En attente'],
  ['confirmee', 'Confirmée'],
  ['expediee', 'Expédiée'],
  ['livree', 'Livrée'],
  ['annulee', 'Annulée'],
]

export const STATUTS_DEVIS = [
  ['nouveau', 'Nouveau'],
  ['en_discussion', 'En discussion'],
  ['accepte', 'Accepté'],
  ['refuse', 'Refusé'],
]

export function libelleStatut(statuts, valeur) {
  return statuts.find(([v]) => v === valeur)?.[1] ?? valeur
}

const formateurDate = new Intl.DateTimeFormat('fr-FR', {
  dateStyle: 'short',
  timeStyle: 'short',
  timeZone: 'Europe/Paris',
})

// The API sends UTC dates ("2026-10-26T14:15:00Z"); the artisan reads Paris time.
export function formatDate(iso) {
  return formateurDate.format(new Date(iso))
}

export const PRODUIT_VIDE = {
  nom: '',
  description: '',
  categorie_id: '',
  prix: '',
  dimensions: '',
  disponibilite: 'disponible',
}

// Form inputs hold strings: API numbers are converted on the way in and out.
export function formulaireDepuisProduit(produit) {
  return {
    nom: produit.nom,
    description: produit.description,
    categorie_id: String(produit.categorie_id),
    prix: String(produit.prix),
    dimensions: produit.dimensions,
    disponibilite: produit.disponibilite,
  }
}

export function produitPourApi(formulaire) {
  return {
    nom: formulaire.nom.trim(),
    description: formulaire.description.trim(),
    categorie_id: Number(formulaire.categorie_id),
    prix: String(formulaire.prix).trim().replace(',', '.'),
    dimensions: formulaire.dimensions.trim(),
    disponibilite: formulaire.disponibilite,
  }
}
