import { test } from 'node:test'
import assert from 'node:assert/strict'
import { UNIVERS, categoriesDeLUnivers, messageUniversVide, universParCode } from './univers.js'

test('UNIVERS lists the three fixed univers in shop order', () => {
  assert.deepEqual(UNIVERS.map((u) => u.code), ['meubles', 'ceramique', 'papeterie'])
  assert.deepEqual(UNIVERS.map((u) => u.nom), ['Meubles', 'Céramique', 'Papeterie'])
})

test('universParCode finds a known univers and returns null otherwise', () => {
  assert.equal(universParCode('ceramique').nom, 'Céramique')
  assert.equal(universParCode('jardin'), null)
  assert.equal(universParCode(undefined), null)
})

test('categoriesDeLUnivers keeps only the categories of that univers', () => {
  const categories = [
    { id: 1, slug: 'tables', univers: 'meubles' },
    { id: 2, slug: 'vases', univers: 'ceramique' },
    { id: 3, slug: 'chaises', univers: 'meubles' },
  ]
  assert.deepEqual(categoriesDeLUnivers(categories, 'meubles').map((c) => c.id), [1, 3])
  assert.deepEqual(categoriesDeLUnivers(categories, 'papeterie'), [])
})

test('messageUniversVide announces that the univers is coming soon', () => {
  assert.match(messageUniversVide, /Bientôt disponible/)
})
