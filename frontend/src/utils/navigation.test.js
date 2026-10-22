import { test } from 'node:test'
import assert from 'node:assert/strict'
import { section, sensTransition } from './navigation.js'

test('section keeps only the first part of the path', () => {
  assert.equal(section('/'), '')
  assert.equal(section('/boutique'), 'boutique')
  assert.equal(section('/boutique/tables'), 'boutique')
  assert.equal(section('/produits/14'), 'produits')
  assert.equal(section('/commande/confirmation'), 'commande')
})

test('sensTransition is 1 when moving right in the menu order, -1 when moving left', () => {
  assert.equal(sensTransition('/', '/boutique'), 1)
  assert.equal(sensTransition('/boutique', '/produits/14'), 1)
  assert.equal(sensTransition('/contact', '/qui-sommes-nous'), -1)
  assert.equal(sensTransition('/produits/14', '/boutique/tables'), -1)
  assert.equal(sensTransition('/panier', '/commande'), 1)
})

test('sensTransition puts unknown pages (404) after every known section', () => {
  assert.equal(sensTransition('/commande', '/nimporte-quoi'), 1)
  assert.equal(sensTransition('/nimporte-quoi', '/'), -1)
})
