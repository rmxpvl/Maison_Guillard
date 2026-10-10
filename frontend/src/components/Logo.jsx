// Monogram "G" (open between 1 and 3 o'clock) wrapped by growth rings.
// Drawn with currentColor: the surrounding CSS `color` decides its colour.
export function SymboleLogo({ className = '' }) {
  return (
    <svg
      viewBox="0 0 64 64"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      aria-hidden="true"
    >
      <path d="M 30 21.61 A 12 12 0 1 0 36 32 M 25 32 H 36" />
      <path d="M 21.05 15.26 A 17 17 0 0 1 35.38 44.63" />
      <path d="M 23.25 10.51 A 21.5 21.5 0 0 1 34.09 50.98" />
      <path d="M 16.83 7.01 A 26 26 0 0 1 32.03 56.73" />
      <path d="M 20.86 2.16 A 30 30 0 0 1 40.78 56.87" />
    </svg>
  )
}

export default function Logo({ className = '' }) {
  return (
    <span className={`logo ${className}`}>
      <SymboleLogo className="logo__symbole" />
      <span className="logo__texte">Maison Guillard</span>
    </span>
  )
}
