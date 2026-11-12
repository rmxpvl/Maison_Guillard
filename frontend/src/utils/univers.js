// The three fixed univers of the shop. Images live in PageBoutique (node tests cannot load .webp).
export const UNIVERS = [
  { code: 'meubles', nom: 'Meubles' },
  { code: 'ceramique', nom: 'Céramique' },
  { code: 'papeterie', nom: 'Papeterie' },
]

export function universParCode(code) {
  return UNIVERS.find((u) => u.code === code) ?? null
}

export function categoriesDeLUnivers(categories, code) {
  return categories.filter((c) => c.univers === code)
}

export const messageUniversVide = 'Bientôt disponible : les pièces de cet univers arrivent.'
