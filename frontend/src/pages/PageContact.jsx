import imageContact from '../assets/vitrine/contact.webp'
import { COORDONNEES } from '../config/coordonnees.js'

export default function PageContact() {
  return (
    <div className="contenu section deux-colonnes">
      <img src={imageContact} alt="" className="image image--paysage" />
      <div className="texte-bloc">
        <p className="surtitre">Contact</p>
        <h1>Parlons de votre projet</h1>
        <p>
          Une question sur une pièce, une envie de sur-mesure : écrivez-nous ou appelez-nous,
          nous vous répondrons avec plaisir.
        </p>
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
  )
}
