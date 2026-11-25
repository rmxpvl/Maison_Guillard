import { useEffect } from 'react'

const NOM = 'Maison Guillard'
const TITRE_ACCUEIL = `${NOM} · Mobilier artisanal en bois massif`
const DESCRIPTION_PAR_DEFAUT =
  'Maison Guillard, artisane menuisière : meubles, céramique et papeterie fabriqués à la main, sur commande.'

// Sets the tab title and the meta description of the page (what Google shows in its results).
// No title: the home page's. `noindex` asks search engines to skip the page (secret links,
// account, back-office). The page's own values are removed when it leaves.
export function useTitre(titre, description, { noindex = false } = {}) {
  useEffect(() => {
    document.title = titre ? `${titre} · ${NOM}` : TITRE_ACCUEIL
    const balise = document.querySelector('meta[name="description"]')
    balise?.setAttribute('content', description ?? DESCRIPTION_PAR_DEFAUT)

    if (!noindex) return undefined
    const robots = document.createElement('meta')
    robots.name = 'robots'
    robots.content = 'noindex'
    document.head.appendChild(robots)
    return () => robots.remove()
  }, [titre, description, noindex])
}
