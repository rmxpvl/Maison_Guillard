import { useState } from 'react'
import EtatChargement from '../EtatChargement.jsx'
import { useApi } from '../../hooks/useApi.js'
import { useAuth } from '../../hooks/useAuth.js'
import { messageErreurApi } from '../../utils/erreurs.js'

const IDENTITE = [
  ['nom_commercial', 'Nom commercial'],
  ['nom_legal', 'Nom légal (ex. EI Prénom Nom) *'],
  ['adresse', "Adresse de l'atelier *"],
  ['siret', 'SIRET *'],
  ['email', 'E-mail *'],
  ['telephone', 'Téléphone'],
  ['prenom_signature', 'Prénom de signature'],
  ['mention_tva', 'Mention de TVA (ex. TVA non applicable, art. 293 B du CGI)'],
]
const FRAIS = [
  ['frais_meubles', 'Meubles'],
  ['frais_ceramique', 'Céramique'],
  ['frais_papeterie', 'Papeterie'],
]
const CONDITIONS = [
  ['cond_paiement', 'Paiement'],
  ['cond_fabrication', 'Fabrication et livraison'],
  ['cond_annulation', 'Annulation'],
]

function FormulaireReglages({ initial, enregistrer }) {
  const [champs, setChamps] = useState(initial)
  const [envoi, setEnvoi] = useState(false)
  const manquants = IDENTITE.filter(([cle, libelle]) => libelle.endsWith('*') && !String(champs[cle]).trim())

  function changer(e) {
    setChamps({ ...champs, [e.target.name]: e.target.value })
  }

  async function envoyer(e) {
    e.preventDefault()
    setEnvoi(true)
    await enregistrer({ ...champs, validite_jours: Number(champs.validite_jours) })
    setEnvoi(false)
  }

  return (
    <form className="formulaire" onSubmit={envoyer}>
      <h3>Identité de l'entreprise</h3>
      <p className="infos__note">
        Imprimée sur chaque devis. Les champs marqués * sont obligatoires pour envoyer un devis
        {manquants.length > 0 && ` : à compléter (${manquants.map(([, l]) => l.replace(' *', '')).join(', ')})`}.
      </p>
      {IDENTITE.map(([cle, libelle]) => (
        <label key={cle}>
          {libelle}
          <input name={cle} value={champs[cle]} onChange={changer} maxLength={300} />
        </label>
      ))}

      <h3>Validité et livraison</h3>
      <label>
        Durée de validité d'un devis (jours)
        <input name="validite_jours" type="number" min="1" max="365" value={champs.validite_jours} onChange={changer} required />
      </label>
      <p className="infos__note">
        Frais de livraison pré-remplis. Pour une demande qui mélange plusieurs univers, on prend les
        frais les plus élevés (règle provisoire).
      </p>
      {FRAIS.map(([cle, libelle]) => (
        <label key={cle}>
          Frais de livraison, {libelle} (€)
          <input name={cle} type="number" min="0" step="0.01" value={champs[cle]} onChange={changer} required />
        </label>
      ))}

      <h3>Conditions affichées en bas du devis</h3>
      {CONDITIONS.map(([cle, libelle]) => (
        <label key={cle}>
          {libelle}
          <textarea name={cle} rows={3} maxLength={2000} value={champs[cle]} onChange={changer} required />
        </label>
      ))}

      <button type="submit" className="bouton bouton--principal" disabled={envoi}>
        {envoi ? 'Enregistrement…' : 'Enregistrer les réglages'}
      </button>
    </form>
  )
}

function MessagesTypes({ appel, signaler }) {
  const [version, setVersion] = useState(0)
  const messages = useApi(() => appel('/messages-types'), [appel, version])
  const [nouveau, setNouveau] = useState({ titre: '', texte: '' })
  const [edition, setEdition] = useState(null)

  async function agir(action, succes) {
    try {
      await action()
      signaler(succes)
      setVersion((v) => v + 1)
      return true
    } catch (err) {
      signaler(messageErreurApi(err))
      return false
    }
  }

  async function creer(e) {
    e.preventDefault()
    if (await agir(() => appel('/messages-types', { method: 'POST', body: nouveau }), 'Message type créé.')) {
      setNouveau({ titre: '', texte: '' })
    }
  }

  async function enregistrer(e) {
    e.preventDefault()
    const { id, ...corps } = edition
    if (await agir(() => appel(`/messages-types/${id}`, { method: 'PUT', body: corps }), 'Message type modifié.')) {
      setEdition(null)
    }
  }

  return (
    <div className="onglet__groupe">
      <h3>Messages types</h3>
      <p className="infos__note">Insérés en un clic dans le message d'un devis (le texte reste modifiable ensuite).</p>
      <form className="formulaire" onSubmit={creer}>
        <label>
          Titre
          <input value={nouveau.titre} onChange={(e) => setNouveau({ ...nouveau, titre: e.target.value })} required maxLength={60} />
        </label>
        <label>
          Texte
          <textarea rows={3} value={nouveau.texte} onChange={(e) => setNouveau({ ...nouveau, texte: e.target.value })} required maxLength={2000} />
        </label>
        <button type="submit" className="bouton">Ajouter</button>
      </form>
      <EtatChargement statut={messages.statut} reessayer={messages.reessayer}>
        <ul className="detail__lignes">
          {messages.data?.map((m) => (
            <li key={m.id}>
              {edition?.id === m.id ? (
                <form className="formulaire" onSubmit={enregistrer}>
                  <input aria-label="Titre" value={edition.titre} required maxLength={60}
                    onChange={(e) => setEdition({ ...edition, titre: e.target.value })} />
                  <textarea aria-label="Texte" rows={3} value={edition.texte} required maxLength={2000}
                    onChange={(e) => setEdition({ ...edition, texte: e.target.value })} />
                  <button type="submit" className="bouton bouton--principal">Enregistrer</button>
                  <button type="button" className="lien-bouton" onClick={() => setEdition(null)}>Annuler</button>
                </form>
              ) : (
                <>
                  <span><strong>{m.titre}</strong> : {m.texte}</span>
                  <span>
                    <button type="button" className="lien-bouton" onClick={() => setEdition(m)}>Modifier</button>
                    <button
                      type="button"
                      className="lien-bouton"
                      onClick={() => window.confirm(`Supprimer « ${m.titre} » ?`) && agir(() => appel(`/messages-types/${m.id}`, { method: 'DELETE' }), 'Message type supprimé.')}
                    >
                      Supprimer
                    </button>
                  </span>
                </>
              )}
            </li>
          ))}
        </ul>
      </EtatChargement>
    </div>
  )
}

export default function OngletReglages() {
  const { appel } = useAuth()
  const reglages = useApi(() => appel('/reglages-devis'), [appel])
  const [message, setMessage] = useState(null)

  async function enregistrer(champs) {
    setMessage(null)
    try {
      await appel('/reglages-devis', { method: 'PUT', body: champs })
      setMessage('Réglages enregistrés.')
    } catch (err) {
      setMessage(messageErreurApi(err))
    }
  }

  return (
    <div className="page-admin">
      <header className="page-admin__entete">
        <div>
          <h1>Informations du devis</h1>
          <p className="page-admin__intro">Ces informations apparaissent sur chaque devis envoyé à vos clients. Les champs marqués d’une étoile sont obligatoires pour pouvoir envoyer un devis.</p>
        </div>
      </header>
      {message && <p className="onglet__message" role="status">{message}</p>}
      <EtatChargement statut={reglages.statut} reessayer={reglages.reessayer}>
        {reglages.data && <FormulaireReglages initial={reglages.data} enregistrer={enregistrer} />}
      </EtatChargement>
      <MessagesTypes appel={appel} signaler={setMessage} />
    </div>
  )
}
