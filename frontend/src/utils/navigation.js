// Sections of the site from left to right: decides which way pages slide.
const ORDRE = ['', 'boutique', 'produits', 'qui-sommes-nous', 'contact', 'panier', 'commande']

// "/boutique/tables" → "boutique", "/" → "".
export function section(pathname) {
  return pathname.split('/')[1] ?? ''
}

// Unknown sections (404 page) count as the last one.
function rang(pathname) {
  const index = ORDRE.indexOf(section(pathname))
  return index === -1 ? ORDRE.length : index
}

// 1: the new page is further right (old page leaves to the left), -1: the other way.
export function sensTransition(depuis, vers) {
  return rang(vers) >= rang(depuis) ? 1 : -1
}
