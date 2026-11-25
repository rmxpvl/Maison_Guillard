import { lazy, Suspense, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import EtatChargement from '../../components/EtatChargement.jsx'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'
import { aujourdhui, dateVersIso, isoVersDate } from '../../utils/contenus.js'
import { messageErreurApi } from '../../utils/erreurs.js'
import { MODELES, photosPlacees } from '../../utils/miseEnForme.js'
import { parseIdProduit } from '../../utils/produit.js'

// The visual editor is heavy: it is downloaded only when a post is opened in the back-office.
const EditeurTexte = lazy(() => import('../../components/admin/EditeurTexte.jsx'))

// Photos of a post: the first is the cover, shown large on the post and in the list. Each has a number
// ([photo 2] in the text places it there) and a width: half or full.
function PhotosActualite({ actualite, apresChangement, signaler }) {
  const { appel } = useAuth()
  const [envoi, setEnvoi] = useState(false)
  const placees = photosPlacees(actualite.contenu)

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
        La première photo est la couverture : elle s’affiche dans la liste des actualités et, selon la mise en
        page, en tête de l’article. Pour placer une photo dans le texte, utilisez « Insérer une photo… » au-dessus du texte.
        Vous pouvez en ajouter plusieurs à la fois (JPG, PNG, WebP ou GIF, 8 Mo au plus chacune).
      </p>
      <ul className="photos-actu__liste">
        {actualite.photos.map((p, i) => (
          <li key={p.id} className="photos-actu__photo">
            <img src={p.url} alt="" />
            <span className="photos-actu__badges">
              <span className="badge">Photo {i + 1}</span>
              {i === 0 && <span className="badge badge--ok">Couverture</span>}
              {placees.has(i + 1) && <span className="badge">Dans le texte</span>}
            </span>
            <label className="photos-actu__disposition">
              Largeur
              <select
                value={p.disposition}
                onChange={(e) => agir(() => appel(`/actualites/photos/${p.id}`, { method: 'PATCH', body: { disposition: e.target.value } }), 'Largeur enregistrée.')}
              >
                <option value="demi">Demi-largeur</option>
                <option value="pleine">Pleine largeur</option>
              </select>
            </label>
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
    modele: actualite?.modele ?? 'classique',
  })
  const [envoi, setEnvoi] = useState(false)
  const photos = actualite?.photos ?? []

  async function enregistrer(e) {
    e.preventDefault()
    signaler(null)
    if (!champs.contenu.trim()) {
      signaler({ ok: false, texte: 'Écrivez le texte de l’actualité avant d’enregistrer.' })
      return
    }
    setEnvoi(true)
    const corps = {
      titre: champs.titre,
      contenu: champs.contenu,
      publiee: champs.publiee,
      date_publication: dateVersIso(champs.date),
      modele: champs.modele,
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
      <div className="editeur-texte">
        <span className="editeur-texte__titre">Texte</span>
        <span className="aide">
          Écrivez comme dans un traitement de texte. Sélectionnez des mots, puis cliquez sur un bouton pour les mettre en forme.
          Une photo insérée se déplace en la faisant glisser, et se retire avec la touche Suppr.
        </span>
        <Suspense fallback={<p className="aide">Chargement de l’éditeur…</p>}>
          <EditeurTexte
            valeur={champs.contenu}
            onChange={(texte) => setChamps((c) => ({ ...c, contenu: texte }))}
            photos={photos}
          />
        </Suspense>
      </div>
      <fieldset className="choix-modele">
        <legend>Mise en page</legend>
        {MODELES.map((m) => (
          <label key={m.code} className="choix-modele__option">
            <input type="radio" name="modele" value={m.code} checked={champs.modele === m.code} onChange={() => setChamps({ ...champs, modele: m.code })} />
            <span className={`choix-modele__schema choix-modele__schema--${m.code}`} aria-hidden="true"><i /><b /><b /><b /></span>
            <span className="choix-modele__texte"><strong>{m.nom}</strong><span className="aide">{m.description}</span></span>
          </label>
        ))}
      </fieldset>
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
