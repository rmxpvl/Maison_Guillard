import { useState } from 'react'
import { DISPONIBILITES, libelleDisponibilite } from '../../utils/produit.js'

// Product fields only. The parent decides what to do on submit (create or update).
export default function FormulaireProduit({ initial, categories, libelleBouton, enregistrer }) {
  const [champs, setChamps] = useState(initial)
  const [envoi, setEnvoi] = useState(false)

  function changer(e) {
    setChamps({ ...champs, [e.target.name]: e.target.value })
  }

  async function envoyer(e) {
    e.preventDefault()
    setEnvoi(true)
    await enregistrer(champs)
    setEnvoi(false)
  }

  return (
    <form className="formulaire" onSubmit={envoyer}>
      <label>
        Nom
        <input name="nom" value={champs.nom} onChange={changer} required maxLength={120} />
      </label>
      <label>
        Description
        <textarea name="description" value={champs.description} onChange={changer} required rows={5} />
      </label>
      <label>
        Catégorie
        <select name="categorie_id" value={champs.categorie_id} onChange={changer} required>
          <option value="" disabled>Choisir…</option>
          {categories.map((c) => <option key={c.id} value={c.id}>{c.nom}</option>)}
        </select>
      </label>
      <label>
        Prix (€)
        <input name="prix" type="number" min="0.01" step="0.01" value={champs.prix} onChange={changer} required />
      </label>
      <label>
        Dimensions
        <input name="dimensions" value={champs.dimensions} onChange={changer} required placeholder="120 x 60 x 45 cm" />
      </label>
      <label>
        Disponibilité
        <select name="disponibilite" value={champs.disponibilite} onChange={changer}>
          {DISPONIBILITES.map((d) => <option key={d} value={d}>{libelleDisponibilite(d)}</option>)}
        </select>
      </label>
      <button type="submit" className="bouton bouton--principal" disabled={envoi}>
        {envoi ? 'Enregistrement…' : libelleBouton}
      </button>
    </form>
  )
}
