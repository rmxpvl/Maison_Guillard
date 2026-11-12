import { test } from 'node:test'
import assert from 'node:assert/strict'
import { erreurMotDePasse, libelleStatutClient, totalAffiche } from './compte.js'

test('libelleStatutClient speaks to the customer, and falls back to the raw value', () => {
  assert.equal(libelleStatutClient('nouvelle'), 'Demande reçue')
  assert.equal(libelleStatutClient('devis_envoye'), 'Devis à examiner')
  assert.equal(libelleStatutClient('en_fabrication'), 'En fabrication')
  assert.equal(libelleStatutClient('inconnu'), 'inconnu')
})

test('erreurMotDePasse checks length, the 72-byte limit and the confirmation', () => {
  assert.equal(erreurMotDePasse('un-bon-mot-de-passe', 'un-bon-mot-de-passe'), null)
  assert.match(erreurMotDePasse('court', 'court'), /au moins 8/)
  assert.match(erreurMotDePasse('é'.repeat(40), 'é'.repeat(40)), /trop long/) // 80 bytes
  assert.equal(erreurMotDePasse('é'.repeat(36), 'é'.repeat(36)), null) // 72 bytes
  assert.match(erreurMotDePasse('un-bon-mot-de-passe', 'une-autre-chose'), /ne correspondent pas/)
})

test('totalAffiche shows the quoted total once there is one, else the indicative one', () => {
  assert.deepEqual(totalAffiche({ total_indicatif: '420.00', total_final: null }), { montant: '420.00', indicatif: true })
  assert.deepEqual(totalAffiche({ total_indicatif: '420.00', total_final: '540.00' }), { montant: '540.00', indicatif: false })
})
