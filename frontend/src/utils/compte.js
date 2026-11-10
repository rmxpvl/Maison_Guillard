// Customer-facing wording of a request's status (the back-office has its own, in admin.js).
const STATUTS_CLIENT = {
  nouvelle: 'Demande reçue',
  devis_envoye: 'Devis à examiner',
  payee: 'Payée',
  en_fabrication: 'En fabrication',
  expediee: 'Expédiée',
  livree: 'Livrée',
  refusee: 'Devis refusé',
  expiree: 'Devis expiré',
  annulee: 'Annulée',
}

export function libelleStatutClient(statut) {
  return STATUTS_CLIENT[statut] ?? statut
}

// Same rules as the API: at least 8 characters, and bcrypt reads 72 bytes only.
export function erreurMotDePasse(motDePasse, confirmation) {
  if (motDePasse.length < 8) return 'Le mot de passe doit contenir au moins 8 caractères.'
  if (new TextEncoder().encode(motDePasse).length > 72) return 'Le mot de passe est trop long (72 caractères au plus).'
  if (motDePasse !== confirmation) return 'Les deux mots de passe ne correspondent pas.'
  return null
}

// The quoted total once the quote exists, the « from » total before.
export function totalAffiche(demande) {
  return demande.total_final != null
    ? { montant: demande.total_final, indicatif: false }
    : { montant: demande.total_indicatif, indicatif: true }
}
