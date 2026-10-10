import { useSearchParams } from 'react-router-dom'
import { DISPONIBILITES, disponibiliteValide, libelleDisponibilite } from '../utils/produit.js'

export default function FiltreDisponibilite() {
  const [params, setParams] = useSearchParams()
  const valeur = disponibiliteValide(params.get('disponibilite')) ?? ''

  function changer(event) {
    const suivants = new URLSearchParams(params)
    if (event.target.value) suivants.set('disponibilite', event.target.value)
    else suivants.delete('disponibilite')
    setParams(suivants)
  }

  return (
    <label className="filtre-dispo">
      Disponibilité
      <select value={valeur} onChange={changer}>
        <option value="">Toutes</option>
        {DISPONIBILITES.map((d) => (
          <option key={d} value={d}>{libelleDisponibilite(d)}</option>
        ))}
      </select>
    </label>
  )
}
