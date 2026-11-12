import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  STATUTS_DEMANDE,
  formatDate,
  formulaireDepuisProduit,
  libelleStatut,
  produitPourApi,
  slugDepuisNom,
  transitionsPossibles,
} from './admin.js'

test('libelleStatut gives the French label, or the raw value if unknown', () => {
  assert.equal(libelleStatut(STATUTS_DEMANDE, 'en_fabrication'), 'En fabrication')
  assert.equal(libelleStatut(STATUTS_DEMANDE, 'devis_envoye'), 'Devis envoyé')
  assert.equal(libelleStatut(STATUTS_DEMANDE, 'autre'), 'autre')
})

test('transitionsPossibles mirrors the moves the API accepts', () => {
  assert.deepEqual(transitionsPossibles('nouvelle'), ['annulee'])
  assert.deepEqual(transitionsPossibles('devis_envoye'), ['annulee'])
  assert.deepEqual(transitionsPossibles('payee'), ['en_fabrication'])
  assert.deepEqual(transitionsPossibles('en_fabrication'), ['expediee'])
  assert.deepEqual(transitionsPossibles('expediee'), ['livree'])
  assert.deepEqual(transitionsPossibles('livree'), [])
  assert.deepEqual(transitionsPossibles('inconnu'), [])
})

test('formatDate shows a Paris date and time', () => {
  // Intl may use non-breaking spaces: normalise them.
  assert.equal(formatDate('2026-10-26T14:15:00Z').replace(/\s/g, ' '), '26/10/2026 15:15')
})

test('formulaireDepuisProduit turns API values into form values', () => {
  const produit = {
    nom: 'Table', description: 'Chêne', categorie_id: 2, prix: '199.99', dimensions: '120x60',
    visible: false, teintes: [{ id: 4 }, { id: 7 }],
  }
  assert.deepEqual(formulaireDepuisProduit(produit), {
    nom: 'Table', description: 'Chêne', categorie_id: '2', prix: '199.99', dimensions: '120x60',
    visible: false, teinte_ids: [4, 7],
  })
})

test('produitPourApi trims text, converts the category and accepts a comma in the price', () => {
  const formulaire = {
    nom: ' Table ', description: ' Chêne ', categorie_id: '2', prix: '199,99', dimensions: ' 120x60 ',
    visible: true, teinte_ids: [4, '7'],
  }
  assert.deepEqual(produitPourApi(formulaire), {
    nom: 'Table', description: 'Chêne', categorie_id: 2, prix: '199.99', dimensions: '120x60',
    visible: true, teinte_ids: [4, 7],
  })
})

test('slugDepuisNom builds a url-safe slug', () => {
  assert.equal(slugDepuisNom('Bols & Tasses'), 'bols-tasses')
  assert.equal(slugDepuisNom('Céramique'), 'ceramique')
  assert.equal(slugDepuisNom('  Été 2026 '), 'ete-2026')
})
