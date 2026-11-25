import { Fragment } from 'react'
import { blocs } from '../utils/miseEnForme.js'

function Morceaux({ morceaux }) {
  return morceaux.map((m, i) => {
    if (m.type === 'gras') return <strong key={i}>{m.texte}</strong>
    if (m.type === 'italique') return <em key={i}>{m.texte}</em>
    if (m.type === 'lien') {
      const externe = m.href.startsWith('http')
      return (
        <a key={i} href={m.href} {...(externe ? { target: '_blank', rel: 'noopener noreferrer' } : {})}>
          {m.texte}
        </a>
      )
    }
    return <Fragment key={i}>{m.texte}</Fragment>
  })
}

// A post's text with its formatting (utils/miseEnForme.js). `rendrePhoto(n)` draws photo n° n where the
// text says [photo n]; a number with no photo shows nothing.
export default function TexteMisEnForme({ contenu, rendrePhoto }) {
  return blocs(contenu).map((b, i) => {
    if (b.type === 'titre') return <h2 key={i}>{b.texte}</h2>
    if (b.type === 'liste') return <ul key={i}>{b.points.map((p, j) => <li key={j}><Morceaux morceaux={p} /></li>)}</ul>
    if (b.type === 'photo') return <Fragment key={i}>{rendrePhoto?.(b.numero) ?? null}</Fragment>
    return <p key={i}><Morceaux morceaux={b.morceaux} /></p>
  })
}
