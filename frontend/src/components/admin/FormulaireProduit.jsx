import { useState } from 'react'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'

// Product fields only. The parent decides what to do on submit (create or update).
export default function FormulaireProduit({ initial, categories, libelleBouton, enregistrer }) {
  const [champs, setChamps] = useState(initial)
  const [envoi, setEnvoi] = useState(false)
  const { appel } = useAuth()
  const teintes = useApi(() => appel('/teintes'), [appel])

  function changer(e) {
    setChamps({ ...champs, [e.target.name]: e.target.value })
  }

  function basculerTeinte(id) {
    const ids = champs.teinte_ids.includes(id)
      ? champs.teinte_ids.filter((x) => x !== id)
      : [...champs.teinte_ids, id]
    setChamps({ ...champs, teinte_ids: ids })
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
        Prix à partir de (€)
        <input name="prix" type="number" min="0.01" step="0.01" value={champs.prix} onChange={changer} required />
      </label>
      <label>
        Dimensions
        <input name="dimensions" value={champs.dimensions} onChange={changer} required placeholder="120 x 60 x 45 cm" />
      </label>
      <label className="case">
        <input
          type="checkbox"
          checked={champs.visible}
          onChange={(e) => setChamps({ ...champs, visible: e.target.checked })}
        />
        Visible sur le site
      </label>
      <fieldset className="case-groupe">
        <legend>Finitions proposées</legend>
        {(teintes.data ?? []).map((t) => (
          <label key={t.id} className="case">
            <input type="checkbox" checked={champs.teinte_ids.includes(t.id)} onChange={() => basculerTeinte(t.id)} />
            {t.nom}{t.active ? '' : ' (désactivée)'}
          </label>
        ))}
        {teintes.data?.length === 0 && <p>Aucune teinte : créez-en dans l'onglet Teintes.</p>}
      </fieldset>
      <button type="submit" className="bouton bouton--principal" disabled={envoi}>
        {envoi ? 'Enregistrement…' : libelleBouton}
      </button>
    </form>
  )
}
