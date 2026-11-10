// Radiogroup of finishes (square images with the name below). Renders nothing for an empty list.
export default function ChoixTeinte({ teintes, valeur, onChange }) {
  if (teintes.length === 0) return null

  function toucheClavier(e, index) {
    const delta = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key]
    if (delta === undefined) return
    e.preventDefault()
    onChange(teintes[(index + delta + teintes.length) % teintes.length].id)
  }

  return (
    <div className="teintes" role="radiogroup" aria-label="Finition">
      {teintes.map((t, i) => {
        const choisie = t.id === valeur
        return (
          <button
            key={t.id}
            type="button"
            role="radio"
            aria-checked={choisie}
            tabIndex={choisie || (valeur === null && i === 0) ? 0 : -1}
            className={`teinte${choisie ? ' teinte--choisie' : ''}`}
            onClick={() => onChange(t.id)}
            onKeyDown={(e) => toucheClavier(e, i)}
          >
            <img src={t.image_url} alt="" className="teinte__image" />
            <span className="teinte__nom">{t.nom}</span>
          </button>
        )
      })}
    </div>
  )
}
