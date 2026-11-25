import { test } from 'node:test'
import assert from 'node:assert/strict'
import { pageDe } from './pagination.js'

const vingt = Array.from({ length: 20 }, (_, i) => i + 1)

test('pageDe gives the elements of the page asked for', () => {
  assert.deepEqual(pageDe(vingt, '2', 9), { elements: [10, 11, 12, 13, 14, 15, 16, 17, 18], page: 2, nbPages: 3 })
  assert.deepEqual(pageDe(vingt, '3', 9).elements, [19, 20])
})

test('pageDe falls back to page 1 on a missing or odd number, and caps at the last page', () => {
  for (const page of [null, undefined, '', 'abc', '0', '-2']) assert.equal(pageDe(vingt, page, 9).page, 1)
  assert.equal(pageDe(vingt, '99', 9).page, 3)
})

test('pageDe on an empty list is one empty page', () => {
  assert.deepEqual(pageDe([], '1', 9), { elements: [], page: 1, nbPages: 1 })
  assert.deepEqual(pageDe(undefined, '1', 9), { elements: [], page: 1, nbPages: 1 })
})
