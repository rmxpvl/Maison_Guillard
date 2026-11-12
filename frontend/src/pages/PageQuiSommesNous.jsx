import { Link } from 'react-router-dom'
import { useContenus } from '../hooks/useContenus.js'
import { paragraphes } from '../utils/contenus.js'

const ENGAGEMENTS = [1, 2, 3]

export default function PageQuiSommesNous() {
  const { texte, image } = useContenus()
  return (
    <div className="contenu">
      <header className="page-entete">
        <p className="surtitre">Qui sommes-nous</p>
        <h1>{texte('apropos.titre')}</h1>
        {paragraphes(texte('apropos.introduction')).map((p) => <p key={p} className="introduction">{p}</p>)}
      </header>

      <img src={image('apropos.bandeau_image')} alt="" className="image image--bandeau" />

      <ul className="engagements">
        {ENGAGEMENTS.map((n) => (
          <li key={n}>
            <h2>{texte(`apropos.engagement${n}_titre`)}</h2>
            <p>{texte(`apropos.engagement${n}_texte`)}</p>
          </li>
        ))}
      </ul>

      <section className="section deux-colonnes">
        <img src={image('apropos.demarche_image')} alt="" className="image image--carree" />
        <div className="texte-bloc">
          <p className="surtitre">Notre démarche</p>
          <h2>{texte('apropos.demarche_titre')}</h2>
          {paragraphes(texte('apropos.demarche_texte')).map((p) => <p key={p}>{p}</p>)}
          <Link to="/boutique" className="lien-fleche">Découvrir la boutique</Link>
        </div>
      </section>
    </div>
  )
}
