import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { CHAMPS, PAGES_EDITABLES } from '../config/contenusSite.js'
import { aujourdhui, champsDeLaPage, dateActu, dateVersIso, extrait, isoVersDate, paragraphes, valeurTexte } from './contenus.js'

test('every editable field has a unique key, a known type and a label', () => {
  const cles = CHAMPS.map((c) => c.cle)
  assert.equal(new Set(cles).size, cles.length)
  for (const c of CHAMPS) {
    assert.ok(['texte', 'texte_long', 'image'].includes(c.type), c.cle)
    assert.ok(c.label.length > 0, c.cle)
    assert.ok(PAGES_EDITABLES.some((p) => p.code === c.page), `${c.cle}: unknown page ${c.page}`)
    if (c.type === 'image') assert.equal(c.defaut, undefined, `${c.cle}: an image default is an asset, see imagesParDefaut.js`)
    else assert.ok(c.defaut.length > 0, `${c.cle}: the original text is the default`)
  }
})

test('the front list of editable fields is the same as the one the API accepts', () => {
  // The API refuses any key it does not know: the two lists must not drift apart.
  const source = fs.readFileSync(new URL('../../../backend/app/services/contenu_service.py', import.meta.url), 'utf8')
  const api = Object.fromEntries([...source.matchAll(/"([a-z0-9_.]+)": (TEXTE|IMAGE)/g)].map((m) => [m[1], m[2]]))
  const front = Object.fromEntries(CHAMPS.map((c) => [c.cle, c.type === 'image' ? 'IMAGE' : 'TEXTE']))
  assert.deepEqual(front, api)
})

test('champsDeLaPage keeps the order of the list', () => {
  const accueil = champsDeLaPage('accueil')
  assert.ok(accueil.length >= 6 && accueil.every((c) => c.page === 'accueil'))
  assert.deepEqual(champsDeLaPage('inconnue'), [])
})

test('valeurTexte gives the artisane text, or the original one', () => {
  const contenus = { 'accueil.titre': { texte: 'Mon titre', image_url: null } }
  assert.equal(valeurTexte(contenus, 'accueil.titre'), 'Mon titre')
  assert.equal(valeurTexte(contenus, 'accueil.sous_titre'), 'Pièces dessinées et fabriquées à la main')
  assert.equal(valeurTexte({ 'accueil.titre': { texte: null, image_url: 'x' } }, 'accueil.titre'), 'Mobilier artisanal en bois massif')
  assert.equal(valeurTexte(null, 'accueil.titre'), 'Mobilier artisanal en bois massif')
})

test('paragraphes splits a text on blank lines and drops empty ones', () => {
  assert.deepEqual(paragraphes('Un.\n\nDeux.\n\n\n  \nTrois.'), ['Un.', 'Deux.', 'Trois.'])
  assert.deepEqual(paragraphes('Une ligne\nsuite de la ligne'), ['Une ligne\nsuite de la ligne'])
  assert.deepEqual(paragraphes('   '), [])
  assert.deepEqual(paragraphes(undefined), [])
})

test('extrait cuts a long text at a word and adds an ellipsis', () => {
  assert.equal(extrait('Court texte.', 50), 'Court texte.')
  const long = 'Nous avons ouvert les portes de l’atelier pour présenter la nouvelle collection de tabourets'
  const e = extrait(long, 40)
  assert.ok(e.endsWith('…') && e.length <= 41 && !e.includes('  '))
  assert.ok(long.startsWith(e.slice(0, -1).trimEnd()))
  assert.equal(extrait('Un.\n\nDeux.', 50), 'Un. Deux.')
})

test('dateActu writes a date in French, in Paris time', () => {
  assert.equal(dateActu('2026-11-12T10:00:00Z'), '12 novembre 2026')
  assert.equal(dateActu('2026-01-01T00:30:00Z'), '1 janvier 2026')
})

test('the date field of the post form round-trips, at midday so no time zone moves the day', () => {
  assert.equal(isoVersDate(dateVersIso('2026-11-12')), '2026-11-12')
  assert.equal(isoVersDate(dateVersIso('2026-01-01')), '2026-01-01')
  assert.equal(isoVersDate('2026-11-12T12:00:00Z'), '2026-11-12')
  assert.match(dateVersIso('2026-11-12'), /^2026-11-12T\d\d:00:00\.000Z$/)
})

test('aujourdhui gives a date for the form field', () => {
  assert.match(aujourdhui(), /^\d{4}-\d{2}-\d{2}$/)
})
