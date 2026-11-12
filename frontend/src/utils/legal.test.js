import { test } from 'node:test'
import assert from 'node:assert/strict'
import { LIENS_LEGAUX, valeurOuACompleter } from './legal.js'

test('valeurOuACompleter shows the value, or flags what the artisane still has to fill in', () => {
  assert.deepEqual(valeurOuACompleter('EI Camille Guillard'), { texte: 'EI Camille Guillard', manquant: false })
  assert.deepEqual(valeurOuACompleter('  123 456  '), { texte: '123 456', manquant: false })
  assert.deepEqual(valeurOuACompleter(''), { texte: 'à compléter', manquant: true })
  assert.deepEqual(valeurOuACompleter('   '), { texte: 'à compléter', manquant: true })
  assert.deepEqual(valeurOuACompleter(undefined), { texte: 'à compléter', manquant: true })
})

test('LIENS_LEGAUX lists the three legal pages with their routes', () => {
  assert.deepEqual(LIENS_LEGAUX.map((l) => l.to), ['/cgv', '/mentions-legales', '/confidentialite'])
  assert.ok(LIENS_LEGAUX.every((l) => l.libelle.length > 0))
})
