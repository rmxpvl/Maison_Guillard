import { useState } from 'react'
import EtatChargement from '../EtatChargement.jsx'
import { getCategories } from '../../api/categories.js'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'
import { slugDepuisNom } from '../../utils/admin.js'
import { messageErreurApi } from '../../utils/erreurs.js'
import { UNIVERS } from '../../utils/univers.js'

const VIDE = { nom: '', slug: '', univers: 'meubles' }

export default function OngletCategories() {
  const { appel } = useAuth()
  const [version, setVersion] = useState(0)
  const categories = useApi(getCategories, [version])
  const [message, setMessage] = useState(null)
  const [nouvelle, setNouvelle] = useState(VIDE)
  const [slugModifie, setSlugModifie] = useState(false)
  const [edition, setEdition] = useState(null) // { id, nom, slug, univers }

  function changerNouvelle(e) {
    const { name, value } = e.target
    if (name === 'slug') {
      setSlugModifie(true)
      setNouvelle({ ...nouvelle, slug: value })
    } else if (name === 'nom') {
      setNouvelle({ ...nouvelle, nom: value, slug: slugModifie ? nouvelle.slug : slugDepuisNom(value) })
    } else {
      setNouvelle({ ...nouvelle, [name]: value })
    }
  }

  async function agir(action, succes) {
    setMessage(null)
    try {
      await action()
      setMessage(succes)
      setVersion((v) => v + 1)
      return true
    } catch (err) {
      setMessage(messageErreurApi(err))
      return false
    }
  }

  async function creer(e) {
    e.preventDefault()
    const ok = await agir(
      () => appel('/categories', { method: 'POST', body: { ...nouvelle, nom: nouvelle.nom.trim() } }),
      `Catégorie « ${nouvelle.nom.trim()} » créée.`,
    )
    if (ok) {
      setNouvelle(VIDE)
      setSlugModifie(false)
    }
  }

  async function enregistrer(e) {
    e.preventDefault()
    const { id, ...corps } = edition
    const ok = await agir(
      () => appel(`/categories/${id}`, { method: 'PUT', body: { ...corps, nom: corps.nom.trim() } }),
      'Catégorie modifiée.',
    )
    if (ok) setEdition(null)
  }

  async function supprimer(c) {
    if (!window.confirm(`Supprimer la catégorie « ${c.nom} » ?`)) return
    await agir(() => appel(`/categories/${c.id}`, { method: 'DELETE' }), `« ${c.nom} » supprimée.`)
  }

  return (
    <div className="onglet">
      <div className="onglet__entete"><h2>Catégories</h2></div>
      {message && <p className="onglet__message" role="status">{message}</p>}

      <form className="formulaire formulaire--ligne" onSubmit={creer}>
        <label>
          Nom
          <input name="nom" value={nouvelle.nom} onChange={changerNouvelle} required maxLength={60} />
        </label>
        <label>
          Univers
          <select name="univers" value={nouvelle.univers} onChange={changerNouvelle}>
            {UNIVERS.map((u) => <option key={u.code} value={u.code}>{u.nom}</option>)}
          </select>
        </label>
        <label>
          Adresse (slug)
          <input name="slug" value={nouvelle.slug} onChange={changerNouvelle} required maxLength={60} pattern="[a-z0-9\-]+" />
        </label>
        <button type="submit" className="bouton bouton--principal">Ajouter</button>
      </form>

      <EtatChargement statut={categories.statut} reessayer={categories.reessayer}>
        {UNIVERS.map((u) => (
          <section key={u.code} className="onglet__groupe">
            <h3>{u.nom}</h3>
            <table className="tableau">
              <tbody>
                {(categories.data ?? []).filter((c) => c.univers === u.code).map((c) => (
                  <tr key={c.id}>
                    {edition?.id === c.id ? (
                      <td colSpan={3}>
                        <form className="formulaire formulaire--ligne" onSubmit={enregistrer}>
                          <input aria-label="Nom" value={edition.nom} required maxLength={60}
                            onChange={(e) => setEdition({ ...edition, nom: e.target.value })} />
                          <input aria-label="Slug" value={edition.slug} required maxLength={60} pattern="[a-z0-9\-]+"
                            onChange={(e) => setEdition({ ...edition, slug: e.target.value })} />
                          <select aria-label="Univers" value={edition.univers}
                            onChange={(e) => setEdition({ ...edition, univers: e.target.value })}>
                            {UNIVERS.map((x) => <option key={x.code} value={x.code}>{x.nom}</option>)}
                          </select>
                          <button type="submit" className="bouton bouton--principal">Enregistrer</button>
                          <button type="button" className="lien-bouton" onClick={() => setEdition(null)}>Annuler</button>
                        </form>
                      </td>
                    ) : (
                      <>
                        <td>{c.nom}</td>
                        <td>{c.slug}</td>
                        <td className="tableau__actions">
                          <button type="button" className="lien-bouton"
                            onClick={() => setEdition({ id: c.id, nom: c.nom, slug: c.slug, univers: c.univers })}>
                            Modifier
                          </button>
                          <button type="button" className="lien-bouton" onClick={() => supprimer(c)}>Supprimer</button>
                        </td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        ))}
      </EtatChargement>
    </div>
  )
}
