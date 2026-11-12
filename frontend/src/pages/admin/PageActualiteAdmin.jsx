import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import EtatChargement from '../../components/EtatChargement.jsx'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'
import { aujourdhui, dateVersIso, isoVersDate } from '../../utils/contenus.js'
import { messageErreurApi } from '../../utils/erreurs.js'
import { parseIdProduit } from '../../utils/produit.js'

// Photos of a post: the first is the cover, shown large on the post and in the list.
function PhotosActualite({ actualite, apresChangement, signaler }) {
  const { appel } = useAuth()
  const [envoi, setEnvoi] = useState(false)

  async function agir(requete, succes) {
    signaler(null)
    try {
      await requete()
      if (succes) signaler({ ok: true, texte: succes })
      apresChangement()
    } catch (err) {
      signaler({ ok: false, texte: messageErreurApi(err) })
    }
  }

  async function ajouter(e) {
    const fichiers = [...e.target.files]
    e.target.value = ''
    if (fichiers.length === 0) return
    setEnvoi(true)
    signaler(null)
    let ajoutees = 0
    for (const fichier of fichiers) {
      const formulaire = new FormData()
      formulaire.append('fichier', fichier)
      try {
        await appel(`/actualites/${actualite.id}/photos`, { method: 'POST', formulaire })
        ajoutees += 1
      } catch (err) {
        signaler({ ok: false, texte: `« ${fichier.name} » : ${messageErreurApi(err)}` })
        break
      }
    }
    if (ajoutees > 0) signaler({ ok: true, texte: ajoutees > 1 ? `${ajoutees} photos ajoutées.` : 'Photo ajoutée.' })
    setEnvoi(false)
    apresChangement()
  }

  return (
    <section className="photos-actu">
      <h2>Photos</h2>
      <p className="page-admin__intro">
        La première photo est la couverture : elle s’affiche en grand sur l’actualité et dans la liste.
        Vous pouvez en ajouter plusieurs à la fois (JPG, PNG, WebP ou GIF, 8 Mo au plus chacune).
      </p>
      <ul className="photos-actu__liste">
        {actualite.photos.map((p, i) => (
          <li key={p.id} className="photos-actu__photo">
            <img src={p.url} alt="" />
            {i === 0 && <span className="badge badge--ok">Couverture</span>}
            <input
              aria-label="Légende de la photo"
              placeholder="Légende (facultatif)"
              defaultValue={p.legende ?? ''}
              maxLength={200}
              onBlur={(e) => {
                if (e.target.value.trim() !== (p.legende ?? '')) {
                  agir(() => appel(`/actualites/photos/${p.id}`, { method: 'PATCH', body: { legende: e.target.value } }), 'Légende enregistrée.')
                }
              }}
            />
            <span className="photos-actu__actions">
              {i > 0 && (
                <button type="button" className="lien-bouton" onClick={() => agir(() => appel(`/actualites/photos/${p.id}/couverture`, { method: 'PATCH' }), 'Nouvelle couverture choisie.')}>
                  Mettre en couverture
                </button>
              )}
              <button
                type="button"
                className="lien-bouton lien-bouton--danger"
                onClick={() => window.confirm('Retirer cette photo ?') && agir(() => appel(`/actualites/photos/${p.id}`, { method: 'DELETE' }), 'Photo retirée.')}
              >
                Retirer
              </button>
            </span>
          </li>
        ))}
      </ul>

      <label className="bouton">
        {envoi ? 'Envoi en cours…' : 'Ajouter des photos'}
        <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" multiple hidden disabled={envoi} onChange={ajouter} />
      </label>
    </section>
  )
}

function FormulaireActualite({ actualite, apresEnregistrement, apresSuppression, signaler }) {
  const { appel } = useAuth()
  const creation = actualite === null
  const [champs, setChamps] = useState({
    titre: actualite?.titre ?? '',
    contenu: actualite?.contenu ?? '',
    publiee: actualite?.publiee ?? false,
    date: actualite ? isoVersDate(actualite.date_publication) : aujourdhui(),
  })
  const [envoi, setEnvoi] = useState(false)

  async function enregistrer(e) {
    e.preventDefault()
    setEnvoi(true)
    signaler(null)
    const corps = {
      titre: champs.titre,
      contenu: champs.contenu,
      publiee: champs.publiee,
      date_publication: dateVersIso(champs.date),
    }
    try {
      const resultat = creation
        ? await appel('/actualites', { method: 'POST', body: corps })
        : await appel(`/actualites/${actualite.id}`, { method: 'PUT', body: corps })
      if (!creation) signaler({ ok: true, texte: 'Modifications enregistrées.' })
      apresEnregistrement(resultat)
    } catch (err) {
      signaler({ ok: false, texte: messageErreurApi(err) })
    }
    setEnvoi(false)
  }

  async function supprimer() {
    if (!window.confirm(`Supprimer « ${actualite.titre} » et ses photos ? Cette action est définitive.`)) return
    try {
      await appel(`/actualites/${actualite.id}`, { method: 'DELETE' })
      apresSuppression()
    } catch (err) {
      signaler({ ok: false, texte: messageErreurApi(err) })
    }
  }

  return (
    <form className="formulaire" onSubmit={enregistrer}>
      <label>
        Titre
        <input value={champs.titre} onChange={(e) => setChamps({ ...champs, titre: e.target.value })} required maxLength={150} />
      </label>
      <label>
        Texte
        <span className="aide">Écrivez comme vous voulez. Pour séparer deux paragraphes, laissez une ligne vide.</span>
        <textarea rows={14} value={champs.contenu} onChange={(e) => setChamps({ ...champs, contenu: e.target.value })} required maxLength={20000} />
      </label>
      <label>
        Date affichée
        <input type="date" value={champs.date} onChange={(e) => setChamps({ ...champs, date: e.target.value })} required />
      </label>
      <label className="case">
        <input type="checkbox" checked={champs.publiee} onChange={(e) => setChamps({ ...champs, publiee: e.target.checked })} />
        Publier sur le site
      </label>
      <p className="aide">Décochée, l’actualité reste un brouillon : vous seule la voyez, elle n’apparaît pas sur le site.</p>

      <div className="detail__statut">
        <button type="submit" className="bouton bouton--principal" disabled={envoi}>
          {envoi ? 'Enregistrement…' : creation ? 'Créer l’actualité' : 'Enregistrer'}
        </button>
        {!creation && actualite.publiee && (
          <Link to={`/actualites/${actualite.slug}`} target="_blank" rel="noreferrer" className="bouton">Voir sur le site</Link>
        )}
        {!creation && (
          <button type="button" className="bouton bouton--danger" onClick={supprimer}>Supprimer l’actualité</button>
        )}
      </div>
    </form>
  )
}

// /admin/actualites/nouveau writes a new post; /admin/actualites/<id> edits one.
export default function PageActualiteAdmin() {
  const { id } = useParams()
  const creation = id === undefined
  const actualiteId = creation ? null : parseIdProduit(id)
  const { appel } = useAuth()
  const navigate = useNavigate()
  const [version, setVersion] = useState(0)
  // Messages live here, above the form: reloading the post after a save must not erase them.
  const [retour, setRetour] = useState(null)
  const actualite = useApi(
    () => (actualiteId === null ? Promise.resolve(null) : appel(`/actualites/admin/${actualiteId}`)),
    [actualiteId, version, appel],
  )

  if (!creation && (actualiteId === null || actualite.erreur?.status === 404)) {
    return (
      <section className="page-admin etat">
        <h1>Actualité introuvable</h1>
        <Link to="/admin?onglet=actualites">Retour aux actualités</Link>
      </section>
    )
  }

  return (
    <section className="page-admin">
      <Link to="/admin?onglet=actualites" className="retour">← Retour aux actualités</Link>
      <h1>{creation ? 'Nouvelle actualité' : actualite.data?.titre ?? 'Actualité'}</h1>
      {retour && <p className={retour.ok ? 'onglet__message' : 'message-erreur'} role={retour.ok ? 'status' : 'alert'}>{retour.texte}</p>}
      <EtatChargement statut={creation ? 'ok' : actualite.statut} reessayer={actualite.reessayer}>
        {(creation || actualite.data) && (
          <div className="produit-admin__colonnes">
            <FormulaireActualite
              key={actualite.data?.id ?? 'nouvelle'}
              actualite={creation ? null : actualite.data}
              // After creating, go to the edit page: photos can be added right away.
              apresEnregistrement={(a) => (creation ? navigate(`/admin/actualites/${a.id}`, { replace: true }) : setVersion((v) => v + 1))}
              apresSuppression={() => navigate('/admin?onglet=actualites', { replace: true })}
              signaler={setRetour}
            />
            {creation ? (
              <p className="page-admin__intro">Enregistrez d’abord l’actualité : vous pourrez ensuite y ajouter des photos.</p>
            ) : (
              <PhotosActualite actualite={actualite.data} apresChangement={() => setVersion((v) => v + 1)} signaler={setRetour} />
            )}
          </div>
        )}
      </EtatChargement>
    </section>
  )
}
