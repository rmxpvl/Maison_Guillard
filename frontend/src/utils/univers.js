// The three fixed univers of the shop. Images live in PageBoutique (node tests cannot load .webp).
export const UNIVERS = [
  { code: 'meubles', nom: 'Meubles' },
  { code: 'ceramique', nom: 'Céramique' },
  { code: 'papeterie', nom: 'Papeterie' },
]

// Key of the photo of each univers in the site contents (« Pages du site » > Boutique).
export const CLE_IMAGE_UNIVERS = {
  meubles: 'boutique.meubles_image',
  ceramique: 'boutique.ceramique_image',
  papeterie: 'boutique.papeterie_image',
}

export function universParCode(code) {
  return UNIVERS.find((u) => u.code === code) ?? null
}

export function categoriesDeLUnivers(categories, code) {
  return categories.filter((c) => c.univers === code)
}

export const messageUniversVide = 'Bientôt disponible : les pièces de cet univers arrivent.'
