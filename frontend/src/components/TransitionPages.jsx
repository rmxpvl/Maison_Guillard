import { useState } from 'react'
import { Routes, useLocation } from 'react-router-dom'
import { section, sensTransition } from '../utils/navigation.js'

// Page change in two steps: the old page slides out, then the new one slides in.
// <Routes location={affichee}> renders the page in `affichee` instead of the real URL,
// which keeps the old page on screen while it leaves.
export default function TransitionPages({ children }) {
  const location = useLocation()
  const [affichee, setAffichee] = useState(location)
  const [phase, setPhase] = useState('entree')
  const [sens, setSens] = useState(1)

  const changeDeSection = section(location.pathname) !== section(affichee.pathname)

  // Setting state during render is React's way to react to a change coming from outside
  // (here the URL); React re-renders right away, before painting.
  if (!changeDeSection && location !== affichee) {
    setAffichee(location) // same section (shop filters): no animation
  } else if (changeDeSection && phase === 'entree') {
    setSens(sensTransition(affichee.pathname, location.pathname))
    setPhase('sortie')
  }

  function finAnimation(event) {
    // Animations of child elements bubble up here too: only <main>'s own count.
    if (event.target !== event.currentTarget || phase !== 'sortie') return
    window.scrollTo(0, 0)
    setAffichee(location)
    setPhase('entree')
  }

  return (
    <main
      className={`page page--${phase} page--${sens > 0 ? 'avant' : 'arriere'}`}
      onAnimationEnd={finAnimation}
    >
      <Routes location={affichee}>{children}</Routes>
    </main>
  )
}
