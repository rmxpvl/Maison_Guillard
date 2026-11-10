// Values and French labels of a demande's status.
export const STATUTS_DEMANDE = [
  ['nouvelle', 'Nouvelle'],
  ['devis_envoye', 'Devis envoyé'],
  ['payee', 'Payée'],
  ['en_fabrication', 'En fabrication'],
  ['expediee', 'Expédiée'],
  ['livree', 'Livrée'],
  ['refusee', 'Refusée'],
  ['expiree', 'Expirée'],
  ['annulee', 'Annulée'],
]

// Moves the artisane can make by hand; the API enforces the same table (409 otherwise).
const TRANSITIONS = {
  nouvelle: ['annulee'],
  devis_envoye: ['annulee'],
  payee: ['en_fabrication'],
  en_fabrication: ['expediee'],
  expediee: ['livree'],
}

export function transitionsPossibles(statut) {
  return TRANSITIONS[statut] ?? []
}

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
  visible: true,
  teinte_ids: [],
}

// Form inputs hold strings: API numbers are converted on the way in and out.
export function formulaireDepuisProduit(produit) {
  return {
    nom: produit.nom,
    description: produit.description,
    categorie_id: String(produit.categorie_id),
    prix: String(produit.prix),
    dimensions: produit.dimensions,
    visible: produit.visible,
    teinte_ids: (produit.teintes ?? []).map((t) => t.id),
  }
}

export function produitPourApi(formulaire) {
  return {
    nom: formulaire.nom.trim(),
    description: formulaire.description.trim(),
    categorie_id: Number(formulaire.categorie_id),
    prix: String(formulaire.prix).trim().replace(',', '.'),
    dimensions: formulaire.dimensions.trim(),
    visible: Boolean(formulaire.visible),
    teinte_ids: formulaire.teinte_ids.map(Number),
  }
}

// « Bols & Tasses » -> « bols-tasses »: lowercase, no accents, dashes between words.
export function slugDepuisNom(nom) {
  return nom
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}
