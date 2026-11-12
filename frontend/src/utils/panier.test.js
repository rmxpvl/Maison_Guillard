import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  ajouterLigne,
  changerQuantiteLigne,
  changerSouhaitLigne,
  changerTeinteLigne,
  compterArticles,
  lignesPourApi,
  lignesValides,
  retirerLigne,
  totalPanier,
} from './panier.js'

const naturel = { id: 7, nom: 'Naturel', image_url: 'https://x/n.svg', ordre: 0, active: true }
const charcoal = { id: 8, nom: 'Charcoal', image_url: 'https://x/c.svg', ordre: 1, active: true }
const inactive = { id: 9, nom: 'Vienna', image_url: 'https://x/v.svg', ordre: 2, active: false }
const table = {
  id: 1, nom: 'Table basse', prix: '199.99',
  photos: [{ id: 5, url: 'https://x/t.jpg', ordre: 0, principale: true }],
  teintes: [charcoal, naturel, inactive],
}
const lampe = { id: 2, nom: 'Lampe', prix: '80.00', photos: [] }

test('ajouterLigne adds a line with quantity 1, the main photo and the visible teintes', () => {
  const [ligne] = ajouterLigne([], table)
  assert.equal(ligne.produit_id, 1)
  assert.equal(ligne.quantite, 1)
  assert.equal(ligne.photo, 'https://x/t.jpg')
  assert.deepEqual(ligne.teintes.map((t) => t.id), [7, 8]) // active only, by ordre
  assert.equal(ligne.teinte_id, null)
  assert.equal(ligne.souhait, '')
  assert.equal(ajouterLigne([], lampe)[0].photo, null)
  assert.deepEqual(ajouterLigne([], lampe)[0].teintes, [])
})

test('ajouterLigne keeps the chosen teinte, if the produit offers it', () => {
  assert.equal(ajouterLigne([], table, 8)[0].teinte_id, 8)
  assert.equal(ajouterLigne([], table, 99)[0].teinte_id, null)
  assert.equal(ajouterLigne([], table, 9)[0].teinte_id, null) // inactive
})

test('ajouterLigne on a product already requested adds 1, capped at 10', () => {
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

test('changerTeinteLigne accepts an offered teinte or none, and refuses a stranger', () => {
  const lignes = ajouterLigne([], table)
  assert.equal(changerTeinteLigne(lignes, 1, '8')[0].teinte_id, 8)
  assert.equal(changerTeinteLigne(lignes, 1, '')[0].teinte_id, null)
  assert.equal(changerTeinteLigne(changerTeinteLigne(lignes, 1, 8), 1, 99)[0].teinte_id, null)
})

test('changerSouhaitLigne stores the wish, cut at 500 characters', () => {
  const lignes = ajouterLigne([], table)
  assert.equal(changerSouhaitLigne(lignes, 1, 'Plus haute')[0].souhait, 'Plus haute')
  assert.equal(changerSouhaitLigne(lignes, 1, 'x'.repeat(600))[0].souhait.length, 500)
})

test('retirerLigne, compterArticles and totalPanier', () => {
  let lignes = ajouterLigne(ajouterLigne([], table), lampe)
  lignes = changerQuantiteLigne(lignes, 1, 2)
  assert.equal(compterArticles(lignes), 3)
  assert.equal(totalPanier(lignes).toFixed(2), '479.98')
  assert.deepEqual(retirerLigne(lignes, 1).map((l) => l.produit_id), [2])
})

test('lignesValides turns anything unexpected from localStorage into an empty request', () => {
  assert.deepEqual(lignesValides(null), [])
  assert.deepEqual(lignesValides('texte'), [])
  assert.deepEqual(lignesValides({ produit_id: 1 }), [])
  assert.deepEqual(lignesValides([{ produit_id: 'x', quantite: 1 }]), [])
  // v1 cart format (no teintes list): dropped
  assert.deepEqual(lignesValides([{ produit_id: 1, quantite: 1, nom: 'Table', prix: '1', photo: null }]), [])
  const bon = ajouterLigne([], table)
  assert.deepEqual(lignesValides(bon), bon)
})

test('lignesPourApi sends produit, quantity, teinte and a trimmed wish (null when empty)', () => {
  let lignes = ajouterLigne([], table, 8)
  assert.deepEqual(lignesPourApi(lignes), [{ produit_id: 1, quantite: 1, teinte_id: 8, souhait: null }])
  lignes = changerSouhaitLigne(lignes, 1, '  Plus haute  ')
  assert.equal(lignesPourApi(lignes)[0].souhait, 'Plus haute')
})
