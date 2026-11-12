import FormulaireDevis from '../components/FormulaireDevis.jsx'
import { COORDONNEES } from '../config/coordonnees.js'
import { useContenus } from '../hooks/useContenus.js'
import { paragraphes } from '../utils/contenus.js'

export default function PageContact() {
  const { texte, image } = useContenus()
  return (
    <>
      <div className="contenu section deux-colonnes">
        <img src={image('contact.image')} alt="" className="image image--paysage" />
        <div className="texte-bloc">
          <p className="surtitre">Contact</p>
          <h1>{texte('contact.titre')}</h1>
          <p className="introduction">{texte('contact.introduction')}</p>
          {paragraphes(texte('contact.texte')).map((p) => <p key={p}>{p}</p>)}
          <dl className="coordonnees">
            <dt>E-mail</dt>
            <dd><a href={`mailto:${COORDONNEES.email}`}>{COORDONNEES.email}</a></dd>
            <dt>Téléphone</dt>
            <dd><a href={`tel:${COORDONNEES.telephone.replace(/\s/g, '')}`}>{COORDONNEES.telephone}</a></dd>
            <dt>Atelier</dt>
            <dd>{COORDONNEES.zone}</dd>
          </dl>
        </div>
      </div>
      <section className="contenu section devis">
        <FormulaireDevis />
      </section>
    </>
  )
}
