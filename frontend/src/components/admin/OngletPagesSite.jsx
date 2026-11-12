import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { PAGES_EDITABLES } from '../../config/contenusSite.js'
import { useAuth } from '../../hooks/useAuth.js'
import { useContenus } from '../../hooks/useContenus.js'
import { champsDeLaPage } from '../../utils/contenus.js'
import { messageErreurApi } from '../../utils/erreurs.js'

// A photo of a page: the current one, a button to change it (sent right away), and one to put the
// original back.
function ChampImage({ champ, signaler }) {
  const { appel } = useAuth()
  const { contenus, image, recharger } = useContenus()
  const modifiee = Boolean(contenus[champ.cle]?.image_url)

  async function changer(e) {
    const fichier = e.target.files[0]
    e.target.value = ''
    if (!fichier) return
    const formulaire = new FormData()
    formulaire.append('fichier', fichier)
    try {
      await appel(`/contenus/${champ.cle}/image`, { method: 'POST', formulaire })
      recharger()
      signaler({ ok: true, texte: `Photo « ${champ.label.toLowerCase()} » changée : elle est déjà visible sur le site.` })
    } catch (err) {
      signaler({ ok: false, texte: messageErreurApi(err) })
    }
  }

  async function retablir() {
    try {
      await appel(`/contenus/${champ.cle}`, { method: 'DELETE' })
      recharger()
      signaler({ ok: true, texte: `Photo « ${champ.label.toLowerCase()} » : la photo d’origine est de retour.` })
    } catch (err) {
      signaler({ ok: false, texte: messageErreurApi(err) })
    }
  }

  return (
    <div className="champ-image">
      <img src={image(champ.cle)} alt="" className="champ-image__apercu" />
      <div className="champ-image__infos">
        <strong>{champ.label}</strong>
        {champ.aide && <span className="aide">{champ.aide}</span>}
        <span className="champ-image__actions">
          <label className="bouton">
            Changer la photo
            <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" hidden onChange={changer} />
          </label>
          {modifiee && <button type="button" className="lien-bouton" onClick={retablir}>Remettre la photo d’origine</button>}
        </span>
      </div>
    </div>
  )
}

// The texts of a page, saved together. A text equal to the original is put back to « original ».
function FormulaireTextes({ champs, signaler }) {
  const { appel } = useAuth()
  const { texte, contenus, recharger } = useContenus()
  const [brouillon, setBrouillon] = useState(() => Object.fromEntries(champs.map((c) => [c.cle, texte(c.cle)])))
  const [envoi, setEnvoi] = useState(false)
  const modifies = champs.filter((c) => brouillon[c.cle].trim() !== texte(c.cle).trim())

  async function enregistrer(e) {
    e.preventDefault()
    setEnvoi(true)
    try {
      for (const c of modifies) {
        const valeur = brouillon[c.cle].trim()
        if (valeur === '' || valeur === c.defaut) await appel(`/contenus/${c.cle}`, { method: 'DELETE' })
        else await appel(`/contenus/${c.cle}`, { method: 'PUT', body: { texte: valeur } })
      }
      recharger()
      signaler({ ok: true, texte: 'Modifications enregistrées : elles sont déjà visibles sur le site.' })
    } catch (err) {
      signaler({ ok: false, texte: messageErreurApi(err) })
    }
    setEnvoi(false)
  }

  if (champs.length === 0) return null
  return (
    <form className="formulaire" onSubmit={enregistrer}>
      {champs.map((c) => (
        <label key={c.cle}>
          {c.label}
          {c.type === 'texte_long'
            ? <textarea rows={4} maxLength={5000} value={brouillon[c.cle]} onChange={(e) => setBrouillon({ ...brouillon, [c.cle]: e.target.value })} />
            : <input maxLength={5000} value={brouillon[c.cle]} onChange={(e) => setBrouillon({ ...brouillon, [c.cle]: e.target.value })} />}
          {contenus[c.cle]?.texte && (
            <button
              type="button"
              className="lien-bouton"
              onClick={() => setBrouillon({ ...brouillon, [c.cle]: c.defaut })}
            >
              Remettre le texte d’origine
            </button>
          )}
        </label>
      ))}
      <button type="submit" className="bouton bouton--principal" disabled={envoi || modifies.length === 0}>
        {envoi ? 'Enregistrement…' : modifies.length === 0 ? 'Rien à enregistrer' : 'Enregistrer les textes'}
      </button>
    </form>
  )
}

export default function OngletPagesSite() {
  const [params, setParams] = useSearchParams()
  const [retour, setRetour] = useState(null)
  const page = PAGES_EDITABLES.find((p) => p.code === params.get('page')) ?? PAGES_EDITABLES[0]
  const champs = champsDeLaPage(page.code)
  const textes = champs.filter((c) => c.type !== 'image')
  const images = champs.filter((c) => c.type === 'image')

  return (
    <div className="page-admin">
      <header className="page-admin__entete">
        <div>
          <h1>Pages du site</h1>
          <p className="page-admin__intro">
            Changez les textes et les photos des pages de votre site. Chaque champ montre ce qui est affiché
            aujourd’hui : modifiez-le, puis cliquez sur « Enregistrer ». Les photos changent dès que vous
            les choisissez. Vous pouvez toujours remettre le texte ou la photo d’origine.
          </p>
        </div>
      </header>

      <nav className="filtres" aria-label="Choisir la page à modifier">
        {PAGES_EDITABLES.map((p) => (
          <button
            key={p.code}
            type="button"
            className={`filtre${p.code === page.code ? ' filtre--actif' : ''}`}
            aria-pressed={p.code === page.code}
            onClick={() => { setRetour(null); setParams({ onglet: 'pages', page: p.code }) }}
          >
            {p.titre}
          </button>
        ))}
      </nav>

      <section key={page.code} className="page-site">
        <div className="page-site__entete">
          <div>
            <h2>{page.titre}</h2>
            <p className="page-admin__intro">{page.aide}</p>
          </div>
          <Link to={page.chemin} target="_blank" rel="noreferrer" className="bouton">Voir la page</Link>
        </div>

        {retour && <p className={retour.ok ? 'onglet__message' : 'message-erreur'} role={retour.ok ? 'status' : 'alert'}>{retour.texte}</p>}

        {images.length > 0 && (
          <div className="page-site__images">
            {images.map((c) => <ChampImage key={c.cle} champ={c} signaler={setRetour} />)}
          </div>
        )}
        <FormulaireTextes champs={textes} signaler={setRetour} />
        {textes.length === 0 && images.length === 0 && <p className="page-admin__intro">Rien à modifier sur cette page.</p>}
      </section>
    </div>
  )
}
