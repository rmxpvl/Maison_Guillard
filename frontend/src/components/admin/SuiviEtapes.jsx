import { ETAPES_SUIVI, etapeActuelle } from '../../utils/admin.js'

// The six steps of an order, with the current one highlighted. Steps already done are filled.
export default function SuiviEtapes({ statut }) {
  const { index, arrete } = etapeActuelle(statut)
  return (
    <ol className={`suivi${arrete ? ' suivi--arrete' : ''}`} aria-label="Où en est cette commande">
      {ETAPES_SUIVI.map((libelle, i) => {
        const etat = index === null ? 'a-venir' : i < index ? 'fait' : i === index ? 'actuel' : 'a-venir'
        return (
          <li key={libelle} className={`suivi__etape suivi__etape--${etat}`} aria-current={etat === 'actuel' ? 'step' : undefined}>
            <span className="suivi__point" aria-hidden="true" />
            <span className="suivi__libelle">{libelle}</span>
          </li>
        )
      })}
    </ol>
  )
}
