import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  formatPrix,
  parseIdProduit,
  avecPhotosDabord,
  photoPrincipale,
  piecesChoisies,
  prixAffiche,
  teintesVisibles,
} from './produit.js'

// Intl inserts non-breaking spaces; normalise them to compare.
const espaces = (s) => s.replace(/\s/g, ' ')

test('formatPrix formats a decimal string in euros, French style', () => {
  assert.equal(espaces(formatPrix('199.99')), '199,99 €')
  assert.equal(espaces(formatPrix('1200.00')), '1 200,00 €')
})

test('prixAffiche always prefixes the price with "À partir de"', () => {
  assert.equal(espaces(prixAffiche({ prix: '240.00' })), 'À partir de 240,00 €')
  assert.equal(espaces(prixAffiche({ prix: '1200.00' })), 'À partir de 1 200,00 €')
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

test('piecesChoisies keeps produits with photos in API order, at most n', () => {
  const photos = [{ id: 1, ordre: 0, principale: true }]
  const a = { id: 1, photos }
  const sansPhoto = { id: 2, photos: [] }
  const b = { id: 3, photos }
  const c = { id: 4, photos }

  assert.deepEqual(piecesChoisies([a, sansPhoto, b, c], 2).map((p) => p.id), [1, 3])
  assert.deepEqual(piecesChoisies([a, sansPhoto, b, c], 10).map((p) => p.id), [1, 3, 4])
})

test('piecesChoisies returns an empty list when nothing qualifies', () => {
  assert.deepEqual(piecesChoisies([], 3), [])
  assert.deepEqual(piecesChoisies([{ id: 1, photos: [] }], 3), [])
})

test('teintesVisibles drops inactive teintes and sorts by ordre', () => {
  const produit = {
    teintes: [
      { id: 1, nom: 'B', ordre: 2, active: true },
      { id: 2, nom: 'X', ordre: 0, active: false },
      { id: 3, nom: 'A', ordre: 1, active: true },
    ],
  }
  assert.deepEqual(teintesVisibles(produit).map((t) => t.id), [3, 1])
  assert.deepEqual(teintesVisibles({}), [])
})
test('avecPhotosDabord puts produits with photos first and keeps the order otherwise', () => {
  const photos = [{ id: 1, ordre: 0, principale: true }]
  const liste = [
    { id: 1, photos: [] },
    { id: 2, photos },
    { id: 3, photos: [] },
    { id: 4, photos },
  ]
  assert.deepEqual(avecPhotosDabord(liste).map((p) => p.id), [2, 4, 1, 3])
  assert.deepEqual(liste.map((p) => p.id), [1, 2, 3, 4]) // input left untouched
})
