import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  STATUTS_DEMANDE,
  formatDate,
  formulaireDepuisProduit,
  libelleStatut,
  produitPourApi,
  slugDepuisNom,
  devisPourApi,
  devisValide,
  editionDepuisDemande,
  insererMessageType,
  totalDevis,
  transitionsPossibles,
  versCentimes,
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

test('versCentimes reads a euro amount typed by hand, comma included', () => {
  assert.equal(versCentimes('250'), 25000)
  assert.equal(versCentimes('250,5'), 25050)
  assert.equal(versCentimes(' 19.99 '), 1999)
  assert.equal(versCentimes('0'), 0)
  assert.equal(versCentimes('-3'), null)
  assert.equal(versCentimes('abc'), null)
  assert.equal(versCentimes(''), null)
})

const demandeCatalogue = {
  lignes: [
    { id: 1, produit_id: 10, libelle: 'Table', quantite: 2, prix_indicatif: '200.00', prix_final: null },
    { id: 2, produit_id: null, libelle: 'Ponçage', quantite: 1, prix_indicatif: null, prix_final: '30.00' },
  ],
  frais_livraison: null,
  frais_livraison_suggere: '60.00',
  message_artisane: null,
}

test('editionDepuisDemande prefills prices, free lines, delivery fees and message', () => {
  assert.deepEqual(editionDepuisDemande(demandeCatalogue), {
    lignes: [{ id: 1, libelle: 'Table', quantite: 2, prix: '200.00' }],
    libres: [{ libelle: 'Ponçage', quantite: 1, prix: '30.00' }],
    frais: '60.00',
    message: '',
  })
  const envoyee = { ...demandeCatalogue, frais_livraison: '40.00', message_artisane: 'Merci' }
  envoyee.lignes[0] = { ...envoyee.lignes[0], prix_final: '250.00' }
  const e = editionDepuisDemande(envoyee)
  assert.equal(e.lignes[0].prix, '250.00')
  assert.equal(e.frais, '40.00')
  assert.equal(e.message, 'Merci')
})

test('totalDevis adds lines, free lines and delivery, in euros', () => {
  const e = {
    lignes: [{ id: 1, libelle: 'Table', quantite: 2, prix: '250,50' }],
    libres: [{ libelle: 'Ponçage', quantite: 1, prix: '30' }],
    frais: '40',
    message: '',
  }
  assert.equal(totalDevis(e), 571)
})

test('devisValide needs a price everywhere, valid fees and at least one line', () => {
  const bon = { lignes: [{ id: 1, libelle: 'T', quantite: 1, prix: '10' }], libres: [], frais: '0', message: '' }
  assert.equal(devisValide(bon), true)
  assert.equal(devisValide({ ...bon, lignes: [{ ...bon.lignes[0], prix: '' }] }), false)
  assert.equal(devisValide({ ...bon, frais: 'x' }), false)
  assert.equal(devisValide({ ...bon, libres: [{ libelle: '  ', quantite: 1, prix: '5' }] }), false)
  assert.equal(devisValide({ lignes: [], libres: [], frais: '0', message: '' }), false)
  assert.equal(devisValide({ lignes: [], libres: [{ libelle: 'Table', quantite: 1, prix: '900' }], frais: '0', message: '' }), true)
})

test('devisPourApi builds the payload with decimal strings', () => {
  const e = {
    lignes: [{ id: 1, libelle: 'Table', quantite: 2, prix: '250,5' }],
    libres: [{ libelle: ' Ponçage ', quantite: 1, prix: '30' }],
    frais: '40',
    message: '  Merci  ',
  }
  assert.deepEqual(devisPourApi(e), {
    lignes: [{ id: 1, prix_final: '250.50' }],
    lignes_libres: [{ libelle: 'Ponçage', quantite: 1, prix: '30.00' }],
    frais_livraison: '40.00',
    message_artisane: 'Merci',
  })
  assert.equal(devisPourApi({ ...e, message: '   ' }).message_artisane, null)
})

test('insererMessageType appends the template after a blank line', () => {
  assert.equal(insererMessageType('', 'Sous 15 jours.'), 'Sous 15 jours.')
  assert.equal(insererMessageType('Bonjour,', 'Sous 15 jours.'), 'Bonjour,\n\nSous 15 jours.')
})
