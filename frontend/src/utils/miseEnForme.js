// The light formatting of a news post, written by the artisane in a plain textarea:
//   ## Intertitre            a heading (### works too)
//   **gras**  *italique*     inside a line
//   [texte](https://…)       a link (http, https or mailto only)
//   - un point               a bulleted list (lines starting with - or *)
//   [photo 2]                alone on its line: photo n° 2 of the post at this place
// A blank line ends a paragraph or a list. The result is a list of plain objects that the page turns
// into React elements: the text never becomes HTML, so nothing typed here can inject a script.

const TITRE = /^#{2,3}\s+(.+)$/
const PHOTO = /^\[photo\s+(\d+)\]$/i
const POINT = /^[-*]\s+(.+)$/
const EN_LIGNE = /\*\*(.+?)\*\*|\*(.+?)\*|\[([^\]]+)\]\(((?:https?:\/\/|mailto:)[^\s)]+)\)/g

export function enLigne(texte) {
  const morceaux = []
  let reste = 0
  for (const m of texte.matchAll(EN_LIGNE)) {
    if (m.index > reste) morceaux.push({ type: 'texte', texte: texte.slice(reste, m.index) })
    if (m[1] !== undefined) morceaux.push({ type: 'gras', texte: m[1] })
    else if (m[2] !== undefined) morceaux.push({ type: 'italique', texte: m[2] })
    else morceaux.push({ type: 'lien', texte: m[3], href: m[4] })
    reste = m.index + m[0].length
  }
  if (reste < texte.length) morceaux.push({ type: 'texte', texte: texte.slice(reste) })
  return morceaux
}

export function blocs(contenu) {
  const resultat = []
  let paragraphe = null
  let liste = null
  const fermer = () => {
    if (paragraphe) resultat.push({ type: 'paragraphe', morceaux: enLigne(paragraphe.join('\n')) })
    if (liste) resultat.push({ type: 'liste', points: liste.map(enLigne) })
    paragraphe = null
    liste = null
  }
  for (const brute of (contenu ?? '').split(/\r?\n/)) {
    const ligne = brute.trim()
    let m
    if (ligne === '') {
      fermer()
    } else if ((m = ligne.match(TITRE))) {
      fermer()
      resultat.push({ type: 'titre', texte: m[1] })
    } else if ((m = ligne.match(PHOTO))) {
      fermer()
      resultat.push({ type: 'photo', numero: Number(m[1]) })
    } else if ((m = ligne.match(POINT))) {
      if (paragraphe) fermer()
      liste = [...(liste ?? []), m[1]]
    } else {
      if (liste) fermer()
      paragraphe = [...(paragraphe ?? []), ligne]
    }
  }
  fermer()
  return resultat
}

// Numbers (1 = first photo) placed in the text with [photo n]: the page shows those photos there and
// leaves them out of the gallery.
export function photosPlacees(contenu) {
  return new Set(blocs(contenu).filter((b) => b.type === 'photo').map((b) => b.numero))
}

// The text without its marks, for the preview of a post and the description given to search engines.
export function texteBrut(contenu) {
  const aPlat = (morceaux) => morceaux.map((m) => m.texte).join('')
  return blocs(contenu)
    .map((b) => {
      if (b.type === 'titre') return b.texte
      if (b.type === 'paragraphe') return aPlat(b.morceaux)
      if (b.type === 'liste') return b.points.map(aPlat).join(' ')
      return ''
    })
    .filter((t) => t !== '')
    .join('\n\n')
}

// The layouts a post can take (the artisane picks one in the back-office).
export const MODELES = [
  { code: 'classique', nom: 'Classique', description: 'La photo de couverture en grand au-dessus du texte, les autres photos après.' },
  { code: 'cote', nom: 'Côte à côte', description: 'La photo de couverture à gauche, le texte à droite, les autres photos en dessous.' },
  { code: 'galerie', nom: 'Galerie', description: 'Le texte d’abord, puis toutes les photos en galerie.' },
]
