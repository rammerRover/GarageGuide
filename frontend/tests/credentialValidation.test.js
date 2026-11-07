import assert from 'node:assert/strict'
import { test } from 'node:test'
import { validateLoginFields, validateRegistrationFields } from '../src/credentialValidation.js'

for (const length of [14, 15, 128, 129]) {
  for (const codepoint of [0x20, 0x41, 0x1F697]) {
    test(`shared Unicode length boundary ${length}, code point ${codepoint}`, () => {
      const value = String.fromCodePoint(codepoint).repeat(length)
      const fields = { email: 'synthetic@example.com', password: value, password_confirmation: value }
      assert.equal(Boolean(validateLoginFields(fields).password), length < 15 || length > 128)
      assert.equal(Boolean(validateRegistrationFields(fields).password), length < 15 || length > 128)
      assert.equal(Boolean(validateRegistrationFields(fields).password_confirmation), length < 15 || length > 128)
    })
  }
}

test('shared normalization preserves registration NFC matching without modifying input', () => {
  const fields = {
    email: 'synthetic@example.com', password: (String.fromCodePoint(0x65, 0x301)).repeat(15),
    password_confirmation: String.fromCodePoint(0xE9).repeat(15),
  }
  assert.deepEqual(validateLoginFields(fields), {})
  assert.deepEqual(validateRegistrationFields(fields), {})
  const unchanged = fields.password !== fields.password_confirmation
  assert.ok(unchanged)
})

test('NFC length precedes validation and lone surrogates are rejected', () => {
  for (const value of [String.fromCodePoint(0x65, 0x301).repeat(14), String.fromCharCode(0xD800).repeat(15)]) {
    const fields = { email: 'synthetic@example.com', password: value, password_confirmation: value }
    assert.equal(Boolean(validateLoginFields(fields).password), true)
    assert.equal(Boolean(validateRegistrationFields(fields).password_confirmation), true)
  }
})

test('email presence and confirmation case/space behavior remain unchanged', () => {
  const fields = { email: ' \t', password: String.fromCharCode(97).repeat(15), password_confirmation: String.fromCharCode(65).repeat(15) }
  assert.equal(validateLoginFields(fields).email, 'Enter your email address.')
  assert.equal(validateRegistrationFields(fields).password_confirmation, 'Passwords must match.')
  fields.email = 'User@EXAMPLE.COM'
  assert.equal(validateLoginFields(fields).email, undefined)
})
