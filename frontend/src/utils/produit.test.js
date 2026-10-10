import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  actionsFiche,
  disponibiliteValide,
  formatPrix,
  libelleDisponibilite,
  parseIdProduit,
  photoPrincipale,
  piecesChoisies,
  prixAffiche,
} from './produit.js'

// Intl inserts non-breaking spaces; normalise them to compare.
const espaces = (s) => s.replace(/\s/g, ' ')

test('formatPrix formats a decimal string in euros, French style', () => {
  assert.equal(espaces(formatPrix('199.99')), '199,99 €')
  assert.equal(espaces(formatPrix('1200.00')), '1 200,00 €')
})

test('prixAffiche prefixes sur_commande prices with "À partir de"', () => {
  assert.equal(espaces(prixAffiche({ prix: '240.00', disponibilite: 'sur_commande' })), 'À partir de 240,00 €')
  assert.equal(espaces(prixAffiche({ prix: '240.00', disponibilite: 'disponible' })), '240,00 €')
})

test('libelleDisponibilite shows rupture as "Vendu"', () => {
  assert.equal(libelleDisponibilite('disponible'), 'Disponible')
  assert.equal(libelleDisponibilite('sur_commande'), 'Sur commande')
  assert.equal(libelleDisponibilite('rupture'), 'Vendu')
})

test('disponibiliteValide keeps known values and drops anything else', () => {
  assert.equal(disponibiliteValide('rupture'), 'rupture')
  assert.equal(disponibiliteValide('foo'), null)
  assert.equal(disponibiliteValide(null), null)
})

test('photoPrincipale prefers principale, then lowest ordre, else null', () => {
  const a = { id: 1, ordre: 2, principale: false }
  const b = { id: 2, ordre: 0, principale: false }
  const c = { id: 3, ordre: 1, principale: true }
  assert.equal(photoPrincipale([a, b, c]), c)
  assert.equal(photoPrincipale([a, b]), b)
  assert.equal(photoPrincipale([]), null)
})

test('parseIdProduit accepts positive integers only', () => {
  assert.equal(parseIdProduit('12'), 12)
  assert.equal(parseIdProduit('abc'), null)
  assert.equal(parseIdProduit('0'), null)
  assert.equal(parseIdProduit('-3'), null)
  assert.equal(parseIdProduit('1.5'), null)
})

test('actionsFiche never offers the cart for sur_commande or rupture', () => {
  const libelles = (d) => actionsFiche(d).map((a) => a.libelle)
  assert.deepEqual(libelles('disponible'), ['Ajouter au panier', 'Personnaliser ce modèle'])
  assert.deepEqual(libelles('sur_commande'), ['Demander un devis'])
  assert.deepEqual(libelles('rupture'), ['Demander un modèle similaire'])
})

test('piecesChoisies keeps produits with photos, disponible first, at most n', () => {
  const photos = [{ id: 1, ordre: 0, principale: true }]
  const vendu = { id: 1, disponibilite: 'rupture', photos }
  const sansPhoto = { id: 2, disponibilite: 'disponible', photos: [] }
  const surCommande = { id: 3, disponibilite: 'sur_commande', photos }
  const dispoA = { id: 4, disponibilite: 'disponible', photos }
  const dispoB = { id: 5, disponibilite: 'disponible', photos }
  const tous = [vendu, sansPhoto, surCommande, dispoA, dispoB]

  assert.deepEqual(piecesChoisies(tous, 3).map((p) => p.id), [4, 5, 3])
  assert.deepEqual(piecesChoisies(tous, 10).map((p) => p.id), [4, 5, 3, 1])
})

test('piecesChoisies returns an empty list when nothing qualifies', () => {
  assert.deepEqual(piecesChoisies([], 3), [])
  assert.deepEqual(piecesChoisies([{ id: 1, disponibilite: 'disponible', photos: [] }], 3), [])
})
