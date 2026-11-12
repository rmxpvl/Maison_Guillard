// What is printed on a legal page when the artisane has not filled the information in yet.
export function valeurOuACompleter(valeur) {
  const texte = (valeur ?? '').trim()
  return texte === '' ? { texte: 'à compléter', manquant: true } : { texte, manquant: false }
}

// The legal pages, in the order of the footer.
export const LIENS_LEGAUX = [
  { to: '/cgv', libelle: 'Conditions générales de vente' },
  { to: '/mentions-legales', libelle: 'Mentions légales' },
  { to: '/confidentialite', libelle: 'Données personnelles' },
]
