import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  compterGroupes,
  etapeActuelle,
  filtrerDemandes,
  groupeDemande,
  nombreEtMot,
  prochaineEtape,
  resumeTaches,
  tonStatut,
} from './suiviDemandes.js'

const JOUR = 24 * 3600 * 1000
const maintenant = new Date('2026-11-20T10:00:00Z')
const dans = (jours) => new Date(maintenant.getTime() + jours * JOUR).toISOString()
const d = (statut, extra = {}) => ({ statut, date_limite: null, messages_non_lus: 0, ...extra })

test('groupeDemande sorts the statuses into what the artisane has to do', () => {
  assert.equal(groupeDemande('nouvelle'), 'afaire')
  assert.equal(groupeDemande('payee'), 'afaire')
  assert.equal(groupeDemande('devis_envoye'), 'attente')
  assert.equal(groupeDemande('expiree'), 'attente')
  assert.equal(groupeDemande('en_fabrication'), 'cours')
  assert.equal(groupeDemande('expediee'), 'cours')
  for (const fini of ['livree', 'refusee', 'annulee', 'inconnu']) assert.equal(groupeDemande(fini), 'terminees')
})

test('tonStatut gives each status a colour family', () => {
  assert.equal(tonStatut('nouvelle'), 'attention')
  assert.equal(tonStatut('payee'), 'attention')
  assert.equal(tonStatut('devis_envoye'), 'attente')
  assert.equal(tonStatut('en_fabrication'), 'cours')
  assert.equal(tonStatut('livree'), 'ok')
  assert.equal(tonStatut('annulee'), 'neutre')
  assert.equal(tonStatut('inconnu'), 'neutre')
})

test('prochaineEtape tells in plain words what to do next', () => {
  assert.match(prochaineEtape('nouvelle'), /devis/)
  assert.match(prochaineEtape('devis_envoye'), /client/)
  assert.match(prochaineEtape('payee'), /fabrication/)
  assert.match(prochaineEtape('en_fabrication'), /expédi/)
  assert.match(prochaineEtape('expediee'), /livr/)
  assert.equal(prochaineEtape('livree'), null)
  assert.equal(prochaineEtape('annulee'), null)
})

test('etapeActuelle places a request on the six-step path, and says when it stopped', () => {
  assert.deepEqual(etapeActuelle('nouvelle'), { index: 0, arrete: false })
  assert.deepEqual(etapeActuelle('devis_envoye'), { index: 1, arrete: false })
  assert.deepEqual(etapeActuelle('payee'), { index: 2, arrete: false })
  assert.deepEqual(etapeActuelle('en_fabrication'), { index: 3, arrete: false })
  assert.deepEqual(etapeActuelle('expediee'), { index: 4, arrete: false })
  assert.deepEqual(etapeActuelle('livree'), { index: 5, arrete: false })
  assert.deepEqual(etapeActuelle('refusee'), { index: 1, arrete: true })
  assert.deepEqual(etapeActuelle('expiree'), { index: 1, arrete: true })
  assert.deepEqual(etapeActuelle('annulee'), { index: null, arrete: true })
})

test('resumeTaches counts what needs the artisane today', () => {
  const demandes = [
    d('nouvelle'),
    d('nouvelle', { messages_non_lus: 2 }),
    d('devis_envoye'),
    d('payee', { date_limite: dans(2) }),
    d('en_fabrication', { date_limite: dans(9) }),
    d('en_fabrication', { date_limite: dans(-1) }),
    d('livree', { date_limite: dans(-5) }),
    d('refusee', { messages_non_lus: 1 }),
  ]

  assert.deepEqual(resumeTaches(demandes, maintenant), {
    aChiffrer: 2,
    aLancer: 1,
    aExpedier: 2,
    attente: 1,
    messages: 3,
    livraisonsProches: 1,
    livraisonsEnRetard: 1,
  })
})

test('resumeTaches on an empty list is all zeros', () => {
  assert.deepEqual(Object.values(resumeTaches([], maintenant)), [0, 0, 0, 0, 0, 0, 0])
})

test('filtrerDemandes filters by group, by status, or by unread messages', () => {
  const liste = [d('nouvelle'), d('payee'), d('devis_envoye'), d('livree', { messages_non_lus: 1 })]
  assert.equal(filtrerDemandes(liste, 'toutes').length, 4)
  assert.equal(filtrerDemandes(liste, 'afaire').length, 2)
  assert.equal(filtrerDemandes(liste, 'attente').length, 1)
  assert.equal(filtrerDemandes(liste, 'payee').length, 1)
  assert.equal(filtrerDemandes(liste, 'messages').length, 1)
  assert.equal(filtrerDemandes(liste, undefined).length, 4)
})

test('compterGroupes gives the number shown on each filter', () => {
  const liste = [d('nouvelle'), d('payee'), d('devis_envoye'), d('en_fabrication'), d('livree')]
  assert.deepEqual(compterGroupes(liste), { afaire: 2, attente: 1, cours: 1, terminees: 1, toutes: 5 })
})

test('nombreEtMot agrees the noun with the number', () => {
  assert.equal(nombreEtMot(0, 'demande'), '0 demande')
  assert.equal(nombreEtMot(1, 'demande'), '1 demande')
  assert.equal(nombreEtMot(3, 'demande'), '3 demandes')
  assert.equal(nombreEtMot(2, 'livraison en retard', 'livraisons en retard'), '2 livraisons en retard')
})
