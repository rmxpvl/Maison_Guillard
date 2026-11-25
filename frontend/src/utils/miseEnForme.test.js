import { test } from 'node:test'
import assert from 'node:assert/strict'
import { blocs, enLigne, entourer, insererBloc, photosPlacees, prefixerLignes, texteBrut } from './miseEnForme.js'

test('enLigne finds bold, italic and links inside a line', () => {
  assert.deepEqual(enLigne('Du **chêne** et du *frêne*, voir [le site](https://exemple.fr).'), [
    { type: 'texte', texte: 'Du ' },
    { type: 'gras', texte: 'chêne' },
    { type: 'texte', texte: ' et du ' },
    { type: 'italique', texte: 'frêne' },
    { type: 'texte', texte: ', voir ' },
    { type: 'lien', texte: 'le site', href: 'https://exemple.fr' },
    { type: 'texte', texte: '.' },
  ])
})

test('enLigne leaves a link that is not http, https or mailto as plain text', () => {
  assert.deepEqual(enLigne('[clic](javascript:alert(1))'), [{ type: 'texte', texte: '[clic](javascript:alert(1))' }])
  assert.deepEqual(enLigne('[écrire](mailto:a@b.fr)'), [{ type: 'lien', texte: 'écrire', href: 'mailto:a@b.fr' }])
})

test('blocs splits headings, paragraphs, lists and photos', () => {
  const texte = '## Le bois\nUne ligne\nla suite\n\n- chêne\n- *noyer*\n\n[photo 2]\nFin.'
  assert.deepEqual(blocs(texte), [
    { type: 'titre', texte: 'Le bois' },
    { type: 'paragraphe', morceaux: [{ type: 'texte', texte: 'Une ligne\nla suite' }] },
    { type: 'liste', points: [[{ type: 'texte', texte: 'chêne' }], [{ type: 'italique', texte: 'noyer' }]] },
    { type: 'photo', numero: 2 },
    { type: 'paragraphe', morceaux: [{ type: 'texte', texte: 'Fin.' }] },
  ])
})

test('blocs keeps the old plain-text posts as paragraphs', () => {
  assert.deepEqual(blocs('Un.\n\nDeux.').map((b) => b.type), ['paragraphe', 'paragraphe'])
  assert.deepEqual(blocs(''), [])
  assert.deepEqual(blocs(undefined), [])
})

test('a list right after a paragraph line starts its own block', () => {
  assert.deepEqual(blocs('Les essences :\n- chêne').map((b) => b.type), ['paragraphe', 'liste'])
})

test('photosPlacees lists the photo numbers used in the text', () => {
  assert.deepEqual([...photosPlacees('[photo 1]\ntexte\n[Photo 3]')], [1, 3])
  assert.deepEqual([...photosPlacees('pas de photo [photo 2] dans la ligne')], [])
})

test('texteBrut drops the marks and the photo lines', () => {
  assert.equal(texteBrut('## Titre\n**Gras** et [lien](https://a.fr)\n\n[photo 1]\n- un\n- deux'), 'Titre\n\nGras et lien\n\nun deux')
})

test('entourer wraps the selection, or a placeholder word', () => {
  assert.deepEqual(entourer('du chêne brut', 3, 8, '**', '**', 'texte'), { texte: 'du **chêne** brut', debut: 5, fin: 10 })
  assert.deepEqual(entourer('ab', 1, 1, '*', '*', 'texte'), { texte: 'a*texte*b', debut: 2, fin: 7 })
})

test('prefixerLignes marks every selected line once', () => {
  assert.equal(prefixerLignes('intro\nchêne\nnoyer', 8, 15, '- ').texte, 'intro\n- chêne\n- noyer')
  assert.equal(prefixerLignes('- chêne', 3, 3, '- ').texte, '- chêne')
  assert.equal(prefixerLignes('Le bois', 0, 0, '## ').texte, '## Le bois')
})

test('insererBloc puts the block alone between blank lines', () => {
  assert.equal(insererBloc('Un.\nDeux.', 4, '[photo 1]').texte, 'Un.\n\n[photo 1]\n\nDeux.')
  assert.equal(insererBloc('', 0, '[photo 2]').texte, '[photo 2]\n')
  assert.equal(insererBloc('Fin.', 4, '[photo 1]').texte, 'Fin.\n\n[photo 1]\n')
})
