import { Link } from 'react-router-dom'
import imageDetail from '../assets/vitrine/detail.webp'
import imageMatiere from '../assets/vitrine/matiere.webp'

const ENGAGEMENTS = [
  {
    titre: 'Bois massif',
    texte: 'Frêne, chêne, noyer : des essences choisies pour leur solidité et la beauté de leur veinage.',
  },
  {
    titre: 'Fait à la main',
    texte: "Chaque pièce est débitée, assemblée et finie à l'atelier, à l'unité ou en petite série.",
  },
  {
    titre: 'Pensé pour durer',
    texte: 'Des lignes sobres et des assemblages robustes, pour des meubles qui traversent les années.',
  },
]

export default function PageQuiSommesNous() {
  return (
    <div className="contenu">
      <header className="page-entete">
        <p className="surtitre">Qui sommes-nous</p>
        <h1>Une maison, un atelier, le bois</h1>
        <p className="introduction">
          Maison Guillard dessine et fabrique à la main des meubles en bois massif : tables,
          assises, luminaires. Des pièces simples, pensées pour le quotidien et pour durer.
        </p>
      </header>

      <img src={imageMatiere} alt="" className="image image--bandeau" />

      <ul className="engagements">
        {ENGAGEMENTS.map((e) => (
          <li key={e.titre}>
            <h2>{e.titre}</h2>
            <p>{e.texte}</p>
          </li>
        ))}
      </ul>

      <section className="section deux-colonnes">
        <img src={imageDetail} alt="" className="image image--carree" />
        <div className="texte-bloc">
          <p className="surtitre">Sur mesure</p>
          <h2>Une pièce à votre mesure</h2>
          <p>
            Adapter un modèle du catalogue ou imaginer un projet ensemble : chaque demande est
            étudiée avec soin.
          </p>
          <Link to="/contact" className="lien-fleche">Nous contacter</Link>
        </div>
      </section>
    </div>
  )
}
