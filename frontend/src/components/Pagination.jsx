import { Link } from 'react-router-dom'

// « ← Précédentes · 1 2 3 · Suivantes → » under a list. Page 1 has no ?page= so its address stays clean.
export default function Pagination({ page, nbPages, chemin }) {
  if (nbPages <= 1) return null
  const lien = (n) => (n === 1 ? chemin : `${chemin}?page=${n}`)
  return (
    <nav className="pagination" aria-label="Pages">
      {page > 1 ? <Link to={lien(page - 1)} className="pagination__fleche">← Précédentes</Link> : <span />}
      <ol className="pagination__numeros">
        {Array.from({ length: nbPages }, (_, i) => i + 1).map((n) => (
          <li key={n}>
            {n === page
              ? <span aria-current="page" className="pagination__numero pagination__numero--active">{n}</span>
              : <Link to={lien(n)} className="pagination__numero">{n}</Link>}
          </li>
        ))}
      </ol>
      {page < nbPages ? <Link to={lien(page + 1)} className="pagination__fleche">Suivantes →</Link> : <span />}
    </nav>
  )
}
