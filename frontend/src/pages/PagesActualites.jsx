import { Link, useParams, useSearchParams } from 'react-router-dom'
import CarteActualite from '../components/CarteActualite.jsx'
import EtatChargement from '../components/EtatChargement.jsx'
import Pagination from '../components/Pagination.jsx'
import TexteMisEnForme from '../components/TexteMisEnForme.jsx'
import PageIntrouvable from './PageIntrouvable.jsx'
import { getActualite, getActualites } from '../api/actualites.js'
import { useApi } from '../hooks/useApi.js'
import { useContenus } from '../hooks/useContenus.js'
import { dateActu, extrait, paragraphes } from '../utils/contenus.js'
import { photosPlacees, texteBrut } from '../utils/miseEnForme.js'
import { pageDe } from '../utils/pagination.js'
import { useTitre } from '../hooks/useTitre.js'
import { imageOptimisee, LARGEURS } from '../utils/images.js'

const PAR_PAGE = 9

// /actualites (?page=2…): the latest news first, each with its cover photo and the start of the text.
export function PageActualites() {
  const { texte } = useContenus()
  const [parametres] = useSearchParams()
  const actualites = useApi(getActualites, [])
  const { elements, page, nbPages } = pageDe(actualites.data, parametres.get('page'), PAR_PAGE)
  useTitre(
    page > 1 ? `Actualités, page ${page}` : 'Actualités',
    'Les nouvelles de l’atelier Maison Guillard : créations, coulisses et événements.',
  )
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
          {elements.map((a) => (
            <li key={a.id}><CarteActualite actualite={a} /></li>
          ))}
        </ul>
        <Pagination page={page} nbPages={nbPages} chemin="/actualites" />
      </EtatChargement>
    </section>
  )
}

function Photo({ photo, titre, largeur, enTete = false }) {
  return (
    <figure className={`actu__photo actu__photo--${photo.disposition ?? 'demi'}`}>
      <img src={imageOptimisee(photo.url, largeur)} alt={photo.legende ?? titre} loading={enTete ? 'eager' : 'lazy'} />
      {photo.legende && <figcaption>{photo.legende}</figcaption>}
    </figure>
  )
}

// /actualites/<adresse>: the whole post, laid out with the template the artisane chose.
export function PageActualite() {
  const { slug } = useParams()
  const actualite = useApi(() => getActualite(slug), [slug])

  useTitre(actualite.data?.titre ?? 'Actualités', actualite.data ? extrait(texteBrut(actualite.data.contenu)) : undefined)

  if (actualite.erreur?.status === 404) return <PageIntrouvable />

  const a = actualite.data
  const modele = a?.modele ?? 'classique'
  // Photos are numbered from 1 in the back-office order. Those placed in the text stay out of the rest.
  const placees = a ? photosPlacees(a.contenu) : new Set()
  const libres = a ? a.photos.filter((_, i) => !placees.has(i + 1)) : []
  const enTete = modele !== 'galerie' ? libres[0] : undefined
  const galerie = enTete ? libres.slice(1) : libres

  const texte = a && (
    <div className="actu__texte">
      <TexteMisEnForme
        contenu={a.contenu}
        rendrePhoto={(n) => a.photos[n - 1] && <Photo photo={a.photos[n - 1]} titre={a.titre} largeur={LARGEURS.moyenne} />}
      />
    </div>
  )

  return (
    <section className="contenu section">
      <div className={`actu actu--${modele}`}>
        <Link to="/actualites" className="retour">← Toutes les actualités</Link>
        <EtatChargement statut={actualite.statut} reessayer={actualite.reessayer}>
          {a && (
            <article>
              <p className="actu__date">{dateActu(a.date_publication)}</p>
              <h1>{a.titre}</h1>
              {modele === 'cote' ? (
                <div className="actu__cote">
                  {enTete && <div className="actu__entete"><Photo photo={enTete} titre={a.titre} largeur={LARGEURS.moyenne} enTete /></div>}
                  {texte}
                </div>
              ) : (
                <>
                  {enTete && <div className="actu__entete"><Photo photo={enTete} titre={a.titre} largeur={LARGEURS.grande} enTete /></div>}
                  {texte}
                </>
              )}
              {galerie.length > 0 && (
                <div className={`actu__galerie${galerie.length === 1 ? ' actu__galerie--seule' : ''}`}>
                  {galerie.map((p) => <Photo key={p.id} photo={p} titre={a.titre} largeur={LARGEURS.moyenne} />)}
                </div>
              )}
            </article>
          )}
        </EtatChargement>
      </div>
    </section>
  )
}
