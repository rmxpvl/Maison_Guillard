import { CHAMPS } from '../config/contenusSite.js'

export function champsDeLaPage(page) {
  return CHAMPS.filter((c) => c.page === page)
}

// The text of a block: the one the artisane wrote, else the original (« defaut »).
export function valeurTexte(contenus, cle) {
  const modifie = contenus?.[cle]?.texte
  if (modifie) return modifie
  return CHAMPS.find((c) => c.cle === cle)?.defaut ?? ''
}

// Plain text -> paragraphs: a blank line starts a new one, a single line break stays inside it.
export function paragraphes(texte) {
  return (texte ?? '')
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter((p) => p !== '')
}

// A short preview of a post for the list: whole words, one line, ending with « … » when cut.
export function extrait(texte, max = 160) {
  const a_plat = (texte ?? '').replace(/\s+/g, ' ').trim()
  if (a_plat.length <= max) return a_plat
  const coupe = a_plat.slice(0, max)
  const dernierEspace = coupe.lastIndexOf(' ')
  return `${(dernierEspace > max * 0.5 ? coupe.slice(0, dernierEspace) : coupe).trimEnd()}…`
}

const formateurDate = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Europe/Paris' })

export function dateActu(iso) {
  return formateurDate.format(new Date(iso))
}

// <input type="date"> value <-> the API's date. Midday, so a time zone never moves the day.
export function dateVersIso(jour) {
  return new Date(`${jour}T12:00:00`).toISOString()
}

export function isoVersDate(iso) {
  const d = new Date(iso)
  const deuxChiffres = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${deuxChiffres(d.getMonth() + 1)}-${deuxChiffres(d.getDate())}`
}

export function aujourdhui() {
  return isoVersDate(new Date().toISOString())
}

// The home page shows the latest posts. The API already sends them newest first.
export function dernieres(actualites, n = 3) {
  return (actualites ?? []).slice(0, n)
}
