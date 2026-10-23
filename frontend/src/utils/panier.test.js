import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  ajouterLigne,
  changerQuantiteLigne,
  compterArticles,
  lignesPourApi,
  lignesValides,
  retirerLigne,
  totalPanier,
} from './panier.js'

const table = { id: 1, nom: 'Table basse', prix: '199.99', photos: [{ id: 5, url: 'https://x/t.jpg', ordre: 0, principale: true }] }
const lampe = { id: 2, nom: 'Lampe', prix: '80.00', photos: [] }

test('ajouterLigne adds a new line with quantity 1 and the main photo', () => {
  assert.deepEqual(ajouterLigne([], table), [
    { produit_id: 1, nom: 'Table basse', prix: '199.99', photo: 'https://x/t.jpg', quantite: 1 },
  ])
  assert.equal(ajouterLigne([], lampe)[0].photo, null)
})

test('ajouterLigne on a product already in the cart adds 1, capped at 10', () => {
  const une = ajouterLigne([], table)
  assert.equal(ajouterLigne(une, table)[0].quantite, 2)
  const dix = changerQuantiteLigne(une, 1, 10)
  assert.equal(ajouterLigne(dix, table)[0].quantite, 10)
})

test('changerQuantiteLigne keeps the quantity between 1 and 10', () => {
  const lignes = ajouterLigne([], table)
  assert.equal(changerQuantiteLigne(lignes, 1, 0)[0].quantite, 1)
  assert.equal(changerQuantiteLigne(lignes, 1, 42)[0].quantite, 10)
  assert.equal(changerQuantiteLigne(lignes, 1, '3')[0].quantite, 3)
})

test('retirerLigne, compterArticles and totalPanier', () => {
  let lignes = ajouterLigne(ajouterLigne([], table), lampe)
  lignes = changerQuantiteLigne(lignes, 1, 2)
  assert.equal(compterArticles(lignes), 3)
  assert.equal(totalPanier(lignes).toFixed(2), '479.98')
  assert.deepEqual(retirerLigne(lignes, 1).map((l) => l.produit_id), [2])
})

test('lignesValides turns anything unexpected from localStorage into an empty cart', () => {
  assert.deepEqual(lignesValides(null), [])
  assert.deepEqual(lignesValides('texte'), [])
  assert.deepEqual(lignesValides({ produit_id: 1 }), [])
  assert.deepEqual(lignesValides([{ produit_id: 'x', quantite: 1 }]), [])
  const bon = ajouterLigne([], table)
  assert.deepEqual(lignesValides(bon), bon)
})

test('lignesPourApi sends only produit_id and quantite', () => {
  assert.deepEqual(lignesPourApi(ajouterLigne([], table)), [{ produit_id: 1, quantite: 1 }])
})
