import { test } from 'node:test'
import assert from 'node:assert/strict'
import { imageOptimisee } from './images.js'

const CLOUDINARY = 'https://res.cloudinary.com/demo/image/upload/v1712/maison-guillard/abc.png'

test('imageOptimisee asks Cloudinary for a resized, compressed image', () => {
  assert.equal(
    imageOptimisee(CLOUDINARY, 800),
    'https://res.cloudinary.com/demo/image/upload/f_auto,q_auto,c_limit,w_800/v1712/maison-guillard/abc.png',
  )
})

test('imageOptimisee never transforms the same URL twice', () => {
  const une = imageOptimisee(CLOUDINARY, 800)
  assert.equal(imageOptimisee(une, 300), une)
})

test('imageOptimisee keeps other addresses unchanged', () => {
  assert.equal(imageOptimisee('http://localhost:3000/uploads/abc.webp', 800), 'http://localhost:3000/uploads/abc.webp')
  assert.equal(imageOptimisee('/assets/accueil-12ab.webp', 800), '/assets/accueil-12ab.webp')
  assert.equal(imageOptimisee('https://exemple.fr/image/upload/x.png', 800), 'https://exemple.fr/image/upload/x.png')
})

test('imageOptimisee tolerates a missing URL', () => {
  assert.equal(imageOptimisee(undefined, 800), undefined)
  assert.equal(imageOptimisee(null, 800), null)
})
