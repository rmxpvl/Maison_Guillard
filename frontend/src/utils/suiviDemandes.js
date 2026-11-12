import { urgenceDateLimite } from './devisEdition.js'

// How the back-office talks about requests, in the artisane's terms: what to do, what is waiting
// on the customer, what is being made, what is over.

export const GROUPES_DEMANDES = [
  { code: 'afaire', libelle: 'À faire' },
  { code: 'attente', libelle: 'En attente du client' },
  { code: 'cours', libelle: 'En fabrication' },
  { code: 'terminees', libelle: 'Terminées' },
]

const GROUPES = {
  nouvelle: 'afaire',
  payee: 'afaire',
  devis_envoye: 'attente',
  expiree: 'attente',
  en_fabrication: 'cours',
  expediee: 'cours',
}

export function groupeDemande(statut) {
  return GROUPES[statut] ?? 'terminees'
}

const TONS = {
  nouvelle: 'attention',
  payee: 'attention',
  devis_envoye: 'attente',
  en_fabrication: 'cours',
  expediee: 'cours',
  livree: 'ok',
}

// Colour family of a status badge (see .badge--* in admin.css).
export function tonStatut(statut) {
  return TONS[statut] ?? 'neutre'
}

const PROCHAINES_ETAPES = {
  nouvelle: 'Préparez et envoyez le devis.',
  devis_envoye: 'Le client doit répondre : il peut accepter, refuser ou poser une question.',
  expiree: 'Le devis a expiré. Vous pouvez le renvoyer si le client est toujours intéressé.',
  payee: 'Le paiement est reçu : lancez la fabrication.',
  en_fabrication: 'Quand la commande part, marquez-la expédiée.',
  expediee: 'À l’arrivée, marquez-la livrée.',
}

export function prochaineEtape(statut) {
  return PROCHAINES_ETAPES[statut] ?? null
}

export const ETAPES_SUIVI = ['Demande reçue', 'Devis envoyé', 'Payée', 'En fabrication', 'Expédiée', 'Livrée']

const ETAPES = { nouvelle: 0, devis_envoye: 1, payee: 2, en_fabrication: 3, expediee: 4, livree: 5 }

// Where a request is on the path above. A refused or expired quote stopped at the quote; a
// cancelled order could have stopped anywhere, so no step is highlighted.
export function etapeActuelle(statut) {
  if (statut === 'refusee' || statut === 'expiree') return { index: 1, arrete: true }
  if (statut === 'annulee') return { index: null, arrete: true }
  return { index: ETAPES[statut] ?? null, arrete: false }
}

// What waits for the artisane today.
export function resumeTaches(demandes, maintenant = new Date()) {
  const compte = (statut) => demandes.filter((d) => d.statut === statut).length
  const urgence = (niveau) => demandes.filter((d) => urgenceDateLimite(d.date_limite, d.statut, maintenant) === niveau).length
  return {
    aChiffrer: compte('nouvelle'),
    aLancer: compte('payee'),
    aExpedier: compte('en_fabrication'),
    attente: compte('devis_envoye'),
    messages: demandes.reduce((somme, d) => somme + (d.messages_non_lus ?? 0), 0),
    livraisonsProches: urgence('proche'),
    livraisonsEnRetard: urgence('depassee'),
  }
}

// `filtre`: a group, a precise status, « messages » (unread customer messages) or « toutes ».
export function filtrerDemandes(demandes, filtre = 'toutes') {
  if (filtre === 'toutes') return demandes
  if (filtre === 'messages') return demandes.filter((d) => d.messages_non_lus > 0)
  if (GROUPES_DEMANDES.some((g) => g.code === filtre)) return demandes.filter((d) => groupeDemande(d.statut) === filtre)
  return demandes.filter((d) => d.statut === filtre)
}

export function compterGroupes(demandes) {
  const compteurs = { afaire: 0, attente: 0, cours: 0, terminees: 0, toutes: demandes.length }
  for (const d of demandes) compteurs[groupeDemande(d.statut)] += 1
  return compteurs
}

export function nombreEtMot(n, singulier, pluriel = `${singulier}s`) {
  return `${n} ${n > 1 ? pluriel : singulier}`
}
