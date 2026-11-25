// Photos uploaded in production live on Cloudinary, which resizes and compresses an image on the fly
// when the URL asks for it: f_auto (WebP/AVIF when the browser takes it), q_auto (quality), c_limit +
// w_N (at most N px wide, never enlarged). Any other address (local uploads, bundled photos) is kept.
const MARQUEUR = '/image/upload/'

export function imageOptimisee(url, largeur) {
  if (!url || !url.startsWith('https://res.cloudinary.com/')) return url
  const position = url.indexOf(MARQUEUR)
  if (position === -1) return url
  const debut = position + MARQUEUR.length
  // Already transformed (e.g. called twice): leave it alone.
  if (url.slice(debut).startsWith('f_auto')) return url
  return `${url.slice(0, debut)}f_auto,q_auto,c_limit,w_${largeur}/${url.slice(debut)}`
}

// Widths asked for, about twice the size shown (sharp on high-density screens).
export const LARGEURS = {
  miniature: 300,
  carte: 800,
  moyenne: 1200,
  grande: 2000,
}
