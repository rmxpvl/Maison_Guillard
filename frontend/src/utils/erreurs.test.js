import { test } from 'node:test'
import assert from 'node:assert/strict'
import { ApiError } from '../api/client.js'
import { messageErreurApi } from './erreurs.js'

test('messageErreurApi shows the API French message when there is one', () => {
  assert.equal(messageErreurApi(new ApiError(422, 'x', '« Lampe » n\'est plus disponible')), '« Lampe » n\'est plus disponible')
})

test('messageErreurApi turns a validation error without message into a hint', () => {
  assert.equal(messageErreurApi(new ApiError(422, 'x')), 'Vérifiez les informations saisies.')
})

test('messageErreurApi has a generic message for server errors', () => {
  assert.equal(messageErreurApi(new ApiError(500, 'x')), "L'envoi n'a pas abouti. Réessayez dans un instant.")
})

test('messageErreurApi reports a connection problem for anything else', () => {
  assert.equal(messageErreurApi(new TypeError('Failed to fetch')), 'Connexion impossible. Vérifiez votre connexion et réessayez.')
})
