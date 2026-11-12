import { Link, useParams } from 'react-router-dom'
import CarteActualite from '../components/CarteActualite.jsx'
import EtatChargement from '../components/EtatChargement.jsx'
import PageIntrouvable from './PageIntrouvable.jsx'
import { getActualite, getActualites } from '../api/actualites.js'
import { useApi } from '../hooks/useApi.js'
import { useContenus } from '../hooks/useContenus.js'
import { dateActu, paragraphes } from '../utils/contenus.js'

// /actualites: the latest news first, each with its cover photo and the start of the text.
export function PageActualites() {
  const { texte } = useContenus()
  const actualites = useApi(getActualites, [])
  return (
    <section className="contenu section">
      <header className="page-entete">
        <p className="surtitre">Actualités</p>
        <h1>{texte('actualites.titre')}</h1>
        {paragraphes(texte('actualites.intro')).map((p) => <p key={p} className="introduction">{p}</p>)}
      </header>
      <EtatChargement
        statut={actualites.statut}
        reessayer={actualites.reessayer}
        vide={actualites.data?.length === 0}
        messageVide="Pas encore d’actualité : revenez bientôt !"
      >
        <ul className="actus">
          {actualites.data?.map((a) => (
            <li key={a.id}><CarteActualite actualite={a} /></li>
          ))}
        </ul>
      </EtatChargement>
    </section>
  )
}

// /actualites/<adresse>: the whole post, with all its photos.
export function PageActualite() {
  const { slug } = useParams()
  const actualite = useApi(() => getActualite(slug), [slug])

  if (actualite.erreur?.status === 404) return <PageIntrouvable />

  const a = actualite.data
  return (
    <section className="contenu section">
      <div className="actu">
      <Link to="/actualites" className="retour">← Toutes les actualités</Link>
      <EtatChargement statut={actualite.statut} reessayer={actualite.reessayer}>
        {a && (
          <article>
            <p className="actu__date">{dateActu(a.date_publication)}</p>
            <h1>{a.titre}</h1>
            {a.photos.length > 0 && (
              <div className={`actu__galerie${a.photos.length === 1 ? ' actu__galerie--seule' : ''}`}>
                {a.photos.map((p, i) => (
                  <figure key={p.id} className={i === 0 ? 'actu__photo actu__photo--couverture' : 'actu__photo'}>
                    <img src={p.url} alt={p.legende ?? a.titre} loading={i === 0 ? 'eager' : 'lazy'} />
                    {p.legende && <figcaption>{p.legende}</figcaption>}
                  </figure>
                ))}
              </div>
            )}
            <div className="actu__texte">
              {paragraphes(a.contenu).map((p) => <p key={p}>{p}</p>)}
            </div>
          </article>
        )}
      </EtatChargement>
      </div>
    </section>
  )
}
