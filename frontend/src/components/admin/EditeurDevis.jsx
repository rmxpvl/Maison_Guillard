import { useState } from 'react'
import { useAuth } from '../../hooks/useAuth.js'
import {
  devisPourApi,
  devisValide,
  editionDepuisDemande,
  insererMessageType,
  totalDevis,
} from '../../utils/admin.js'
import { messageErreurApi } from '../../utils/erreurs.js'
import { formatDate } from '../../utils/admin.js'
import { formatPrix } from '../../utils/produit.js'

// A quote can be (re)sent until the customer has paid.
const MODIFIABLES = ['nouvelle', 'devis_envoye', 'expiree']

// Opens a PDF in a new tab. The tab is opened right away (in the click) so the browser does not
// block it, then pointed at the file once it has been fetched.
async function ouvrirPdf(chargerBlob) {
  const onglet = window.open('', '_blank')
  try {
    const blob = await chargerBlob()
    const url = URL.createObjectURL(blob)
    if (onglet) onglet.location.href = url
    else window.location.href = url
  } catch (err) {
    onglet?.close()
    throw err
  }
}

export default function EditeurDevis({ demande, messagesTypes, apresEnvoi }) {
  const { appel } = useAuth()
  const [edition, setEdition] = useState(() => editionDepuisDemande(demande))
  const [ouvert, setOuvert] = useState(demande.numero_devis === null)
  const [message, setMessage] = useState(null)
  const [erreur, setErreur] = useState(null)
  const [envoi, setEnvoi] = useState(false)
  const [copie, setCopie] = useState(false)

  if (!MODIFIABLES.includes(demande.statut) && demande.numero_devis === null) return null

  const modifiable = MODIFIABLES.includes(demande.statut)
  const lecture = !ouvert || !modifiable
  const lien = `${window.location.origin}/devis/${demande.jeton}`
  const valide = devisValide(edition)

  function changerLigne(liste, index, champ, valeur) {
    setEdition({ ...edition, [liste]: edition[liste].map((l, i) => (i === index ? { ...l, [champ]: valeur } : l)) })
  }

  async function apercu() {
    setErreur(null)
    try {
      await ouvrirPdf(() =>
        appel(`/demandes/${demande.id}/devis/apercu`, { method: 'POST', body: devisPourApi(edition), blob: true }),
      )
    } catch (err) {
      setErreur(messageErreurApi(err))
    }
  }

  async function envoyer() {
    setErreur(null)
    setMessage(null)
    setEnvoi(true)
    try {
      const maj = await appel(`/demandes/${demande.id}/devis`, { method: 'POST', body: devisPourApi(edition) })
      setMessage(`Devis ${maj.numero_devis} envoyé à ${maj.email}.`)
      setOuvert(false)
      apresEnvoi()
    } catch (err) {
      setErreur(messageErreurApi(err))
    }
    setEnvoi(false)
  }

  async function copier() {
    try {
      await navigator.clipboard.writeText(lien)
      setCopie(true)
    } catch {
      setCopie(false)
    }
  }

  return (
    <section className="editeur-devis">
      <h3>
        Devis{demande.numero_devis && ` ${demande.numero_devis} (version ${demande.version_devis})`}
      </h3>
      {!modifiable && demande.numero_devis && (
        <p className="infos__note">Ce devis est payé ou terminé : il ne peut plus être modifié.</p>
      )}
      {demande.devis_envoye_at && (
        <p className="infos__note">
          Envoyé le {formatDate(demande.devis_envoye_at)}, valable jusqu'au {formatDate(demande.expire_at)}.
        </p>
      )}

      <table className="tableau">
        <thead>
          <tr><th>Pièce</th><th>Qté</th><th>Prix final (€)</th></tr>
        </thead>
        <tbody>
          {edition.lignes.map((l, i) => (
            <tr key={l.id}>
              <td>{l.libelle}</td>
              <td>{l.quantite}</td>
              <td>
                <input
                  aria-label={`Prix final de ${l.libelle}`}
                  inputMode="decimal"
                  value={l.prix}
                  disabled={lecture}
                  onChange={(e) => changerLigne('lignes', i, 'prix', e.target.value)}
                />
              </td>
            </tr>
          ))}
          {edition.libres.map((l, i) => (
            <tr key={`libre-${i}`}>
              <td>
                <input
                  aria-label="Libellé de la ligne libre"
                  value={l.libelle}
                  maxLength={200}
                  disabled={lecture}
                  onChange={(e) => changerLigne('libres', i, 'libelle', e.target.value)}
                />
              </td>
              <td>
                <input
                  aria-label="Quantité de la ligne libre"
                  type="number"
                  min="1"
                  max="10"
                  value={l.quantite}
                  disabled={lecture}
                  onChange={(e) => changerLigne('libres', i, 'quantite', Math.min(10, Math.max(1, Number(e.target.value) || 1)))}
                />
              </td>
              <td>
                <input
                  aria-label="Prix de la ligne libre"
                  inputMode="decimal"
                  value={l.prix}
                  disabled={lecture}
                  onChange={(e) => changerLigne('libres', i, 'prix', e.target.value)}
                />
                {!lecture && (
                  <button
                    type="button"
                    className="lien-bouton"
                    onClick={() => setEdition({ ...edition, libres: edition.libres.filter((_, k) => k !== i) })}
                  >
                    Retirer
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!lecture && (
        <button
          type="button"
          className="lien-bouton"
          onClick={() => setEdition({ ...edition, libres: [...edition.libres, { libelle: '', quantite: 1, prix: '' }] })}
        >
          Ajouter une ligne libre
        </button>
      )}

      <div className="formulaire">
        <label>
          Frais de livraison (€)
          <input
            inputMode="decimal"
            value={edition.frais}
            disabled={lecture}
            onChange={(e) => setEdition({ ...edition, frais: e.target.value })}
          />
        </label>
        <label>
          Message au client (facultatif)
          <textarea
            rows={4}
            maxLength={2000}
            value={edition.message}
            disabled={lecture}
            onChange={(e) => setEdition({ ...edition, message: e.target.value })}
          />
        </label>
        {!lecture && messagesTypes.length > 0 && (
          <label>
            Insérer un message type
            <select
              value=""
              onChange={(e) => {
                const type = messagesTypes.find((m) => String(m.id) === e.target.value)
                if (type) setEdition({ ...edition, message: insererMessageType(edition.message, type.texte) })
              }}
            >
              <option value="">Choisir…</option>
              {messagesTypes.map((m) => <option key={m.id} value={m.id}>{m.titre}</option>)}
            </select>
          </label>
        )}
      </div>

      <p className="panier__total">Total du devis : <strong>{formatPrix(totalDevis(edition))}</strong></p>
      {erreur && <p className="message-erreur" role="alert">{erreur}</p>}
      {message && <p className="onglet__message" role="status">{message}</p>}

      <div className="detail__statut">
        {modifiable && ouvert && (
          <>
            <button type="button" className="bouton" onClick={apercu} disabled={!valide}>Aperçu</button>
            <button type="button" className="bouton bouton--principal" onClick={envoyer} disabled={!valide || envoi}>
              {envoi ? 'Envoi…' : demande.numero_devis ? 'Renvoyer le devis' : 'Envoyer le devis'}
            </button>
          </>
        )}
        {modifiable && !ouvert && (
          <button type="button" className="bouton" onClick={() => setOuvert(true)}>Modifier et renvoyer le devis</button>
        )}
        {demande.numero_devis && (
          <button
            type="button"
            className="bouton"
            onClick={() => ouvrirPdf(() => appel(`/demandes/${demande.id}/devis.pdf`, { blob: true })).catch((err) => setErreur(messageErreurApi(err)))}
          >
            Télécharger le PDF
          </button>
        )}
      </div>
      {demande.numero_devis && (
        <p className="infos__note">
          Lien du client : <a href={lien}>{lien}</a>{' '}
          <button type="button" className="lien-bouton" onClick={copier}>{copie ? 'Copié' : 'Copier'}</button>
        </p>
      )}
    </section>
  )
}
