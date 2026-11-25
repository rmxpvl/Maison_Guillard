import { test } from 'node:test'
import assert from 'node:assert/strict'
import { versDoc, versTexte } from './editeurDoc.js'
import { blocs } from './miseEnForme.js'

const ARTICLE = [
  'Une **table en chêne** et du *frêne*, voir [le site](https://exemple.fr).',
  '## Le choix du bois',
  'Première ligne\nseconde ligne',
  '[photo 2]',
  '- débit\n- *finition* à l’huile',
].join('\n\n')

test('a stored post goes to the editor and back unchanged', () => {
  assert.equal(versTexte(versDoc(ARTICLE)), ARTICLE)
})

test('versDoc builds the editor nodes', () => {
  const doc = versDoc('## Titre\n\nDu **gras**\n\n[photo 1]\n\n- un')
  assert.deepEqual(doc.content.map((n) => n.type), ['heading', 'paragraph', 'photo', 'bulletList'])
  assert.deepEqual(doc.content[1].content[1], { type: 'text', text: 'gras', marks: [{ type: 'bold' }] })
  assert.deepEqual(doc.content[2].attrs, { numero: 1 })
})

test('an empty post is one empty paragraph in the editor, and an empty editor is an empty text', () => {
  assert.deepEqual(versDoc(''), { type: 'doc', content: [{ type: 'paragraph' }] })
  assert.equal(versTexte({ type: 'doc', content: [{ type: 'paragraph' }] }), '')
})

test('versTexte writes the marks the site reads', () => {
  const doc = {
    type: 'doc',
    content: [
      { type: 'paragraph', content: [
        { type: 'text', text: 'gras et italique', marks: [{ type: 'bold' }, { type: 'italic' }] },
        { type: 'text', text: ' ' },
        { type: 'text', text: 'lien', marks: [{ type: 'link', attrs: { href: 'https://a.fr' } }] },
        { type: 'text', text: ' ' },
        { type: 'text', text: 'piège', marks: [{ type: 'link', attrs: { href: 'javascript:alert(1)' } }] },
      ] },
    ],
  }
  assert.equal(versTexte(doc), '**gras et italique** [lien](https://a.fr) piège')
})

test('a paragraph that starts like a mark stays a paragraph on the site', () => {
  const doc = { type: 'doc', content: [{ type: 'paragraph', content: [{ type: 'text', text: '- pas une liste' }] }] }
  assert.deepEqual(blocs(versTexte(doc)).map((b) => b.type), ['paragraphe'])
})
