// Bridge between the stored text of a post (light marks, see miseEnForme.js) and the document of the
// visual editor of the back-office (TipTap / ProseMirror JSON). The database keeps the light marks:
// the public site, the excerpts and the sitemap read them as before.
import { blocs } from './miseEnForme.js'

const LIEN_ACCEPTE = /^(https?:\/\/|mailto:)\S+$/

function texteVersNoeuds(morceaux) {
  const noeuds = []
  for (const m of morceaux) {
    const marques = []
    if (m.type === 'gras') marques.push({ type: 'bold' })
    if (m.type === 'italique') marques.push({ type: 'italic' })
    if (m.type === 'lien') marques.push({ type: 'link', attrs: { href: m.href } })
    // A line break inside a paragraph becomes a hard break of the editor.
    m.texte.split('\n').forEach((ligne, i) => {
      if (i > 0) noeuds.push({ type: 'hardBreak' })
      if (ligne) noeuds.push(marques.length ? { type: 'text', text: ligne, marks: marques } : { type: 'text', text: ligne })
    })
  }
  return noeuds
}

const paragraphe = (contenu) => (contenu.length ? { type: 'paragraph', content: contenu } : { type: 'paragraph' })

export function versDoc(contenu) {
  const content = blocs(contenu).map((b) => {
    if (b.type === 'titre') return { type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: b.texte }] }
    if (b.type === 'photo') return { type: 'photo', attrs: { numero: b.numero } }
    if (b.type === 'liste') {
      return { type: 'bulletList', content: b.points.map((p) => ({ type: 'listItem', content: [paragraphe(texteVersNoeuds(p))] })) }
    }
    return paragraphe(texteVersNoeuds(b.morceaux))
  })
  return { type: 'doc', content: content.length ? content : [{ type: 'paragraph' }] }
}

function noeudsVersTexte(noeuds = []) {
  return noeuds
    .map((n) => {
      if (n.type === 'hardBreak') return '\n'
      if (n.type !== 'text') return ''
      const marques = n.marks ?? []
      const lien = marques.find((m) => m.type === 'link')
      if (lien && LIEN_ACCEPTE.test(lien.attrs?.href ?? '')) return `[${n.text}](${lien.attrs.href})`
      // The site has no bold-and-italic at once: bold wins.
      if (marques.some((m) => m.type === 'bold')) return `**${n.text}**`
      if (marques.some((m) => m.type === 'italic')) return `*${n.text}*`
      return n.text
    })
    .join('')
}

// A line of a paragraph that would read as a heading, a list point or a photo is kept as text.
function proteger(ligne) {
  return /^(#{2,3}\s|[-*]\s|\[photo\s+\d+\]$)/i.test(ligne.trim()) ? `​${ligne}` : ligne
}

export function versTexte(doc) {
  const morceaux = []
  for (const bloc of doc?.content ?? []) {
    if (bloc.type === 'heading') {
      const titre = noeudsVersTexte(bloc.content).replace(/\n/g, ' ').trim()
      if (titre) morceaux.push(`## ${titre}`)
    } else if (bloc.type === 'photo') {
      morceaux.push(`[photo ${bloc.attrs.numero}]`)
    } else if (bloc.type === 'bulletList') {
      const points = (bloc.content ?? [])
        .map((item) => (item.content ?? []).map((p) => noeudsVersTexte(p.content)).join(' ').replace(/\n/g, ' ').trim())
        .filter((p) => p !== '')
      if (points.length) morceaux.push(points.map((p) => `- ${p}`).join('\n'))
    } else if (bloc.type === 'paragraph') {
      const texte = noeudsVersTexte(bloc.content)
      if (texte.trim()) morceaux.push(texte.split('\n').map(proteger).join('\n'))
    }
  }
  return morceaux.join('\n\n')
}
