import assert from 'node:assert/strict'
import { test } from 'node:test'
import { getSession, loginAccount, logoutAccount, registerAccount } from '../src/api.js'

const session = {
  user: { id: 7, email: 'synthetic@example.com', created_at: '2026-11-06T12:00:00Z' },
  expires_at: '2026-11-06T12:30:00Z',
}
const details = () => ({ email: session.user.email, password: String.fromCharCode(97).repeat(15) })
const actions = {
  login: (signal) => loginAccount(details(), signal),
  session: (signal) => getSession(signal),
  logout: (signal) => logoutAccount(signal),
}

function replaceFetch(t, replacement) {
  const original = globalThis.fetch
  globalThis.fetch = replacement
  t.after(() => { globalThis.fetch = original })
}

function response(status, body) {
  return status === 204 ? { status, text: async () => body ?? '' } :
    new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

for (const action of Object.keys(actions)) {
  test(`${action} uses only its relative same-origin contract`, async (t) => {
    let calls = 0
    replaceFetch(t, async (url, options) => {
      calls += 1
      assert.equal(url, `/api/auth/${action}`)
      assert.equal(options.credentials, 'same-origin')
      assert.ok(options.signal instanceof AbortSignal)
      assert.equal(Object.hasOwn(options.headers, 'Origin'), false)
      if (action === 'session') {
        assert.equal(options.method, 'GET')
        assert.equal(Object.hasOwn(options, 'body'), false)
        assert.equal(Object.hasOwn(options.headers, 'X-GarageGuide-CSRF'), false)
      } else {
        assert.equal(options.method, 'POST')
        assert.equal(options.headers['Content-Type'], 'application/json')
        assert.equal(options.headers['X-GarageGuide-CSRF'], '1')
        const correctBody = options.body === JSON.stringify(action === 'login' ? details() : {})
        assert.ok(correctBody)
      }
      return response(action === 'logout' ? 204 : 200, action === 'logout' ? '' : session)
    })
    assert.equal((await actions[action]()).kind, 'success')
    assert.equal(calls, 1)
  })
}

const outcomes = [
  ['login', 401, { detail: 'Invalid email or password.' }, 'invalid'],
  ['login', 422, { detail: [{ loc: ['body', 'password'], msg: 'Use between 15 and 128 characters.', type: 'value_error' }] }, 'invalid'],
  ['login', 403, { detail: 'Request not allowed.' }, 'forbidden'],
  ['login', 503, { detail: 'Authentication unavailable. Please try again.' }, 'unavailable'],
  ['login', 500, { detail: 'Internal server error' }, 'unexpected'],
  ['login', 200, { ...session, token: 'untrusted-private-marker' }, 'unexpected'],
  ['login', 200, { ...session, user: { ...session.user, password_hash: 'untrusted-private-marker' } }, 'unexpected'],
  ['login', 200, { ...session, user: { ...session.user, id: '7' } }, 'unexpected'],
  ['login', 200, { ...session, user: { ...session.user, email: 'UPPER@example.com' } }, 'unexpected'],
  ['login', 200, { ...session, user: { ...session.user, email: 'not-an-address' } }, 'unexpected'],
  ['login', 200, { ...session, expires_at: '2026-11-06T12:30:00' }, 'unexpected'],
  ['login', 422, { detail: [{ loc: ['body', 'password'], msg: 'untrusted-private-marker', type: 'value_error' }] }, 'unexpected'],
  ['login', 422, { detail: [{ loc: ['body', 'password'], msg: 'Enter a valid value.', type: 'value_error', input: 'untrusted-private-marker' }] }, 'unexpected'],
  ['login', 422, { detail: [{ loc: ['body', 'password_confirmation'], msg: 'Field required.', type: 'missing' }] }, 'unexpected'],
  ['session', 401, { detail: 'Not authenticated.' }, 'guest'],
  ['session', 401, { detail: 'untrusted-private-marker' }, 'unavailable'],
  ['session', 503, { detail: 'Authentication unavailable. Please try again.' }, 'unavailable'],
  ['session', 500, { detail: 'Internal server error' }, 'unavailable'],
  ['session', 200, { user: session.user }, 'unavailable'],
  ['logout', 204, '', 'success'],
  ['logout', 204, 'untrusted-private-marker', 'unexpected'],
  ['logout', 200, session, 'unexpected'],
  ['logout', 401, { detail: 'Not authenticated.' }, 'unexpected'],
  ['logout', 403, { detail: 'Request not allowed.' }, 'forbidden'],
  ['logout', 503, { detail: 'Authentication unavailable. Please try again.' }, 'unavailable'],
]
for (const [index, [action, status, body, expected]] of outcomes.entries()) {
  test(`${action} classifies response case ${index + 1} safely`, async (t) => {
    replaceFetch(t, async () => response(status, body))
    const result = await actions[action]()
    assert.equal(result.kind, expected)
    assert.equal(JSON.stringify(result).includes('untrusted-private-marker'), false)
    if (result.kind === 'success' && action !== 'logout') {
      assert.deepEqual(result.session, session)
      assert.deepEqual(Object.keys(result.session.user), ['id', 'email', 'created_at'])
    }
  })
}

for (const action of Object.keys(actions)) {
  test(`${action} rejects malformed JSON with fixed feedback`, async (t) => {
    replaceFetch(t, async () => ({ status: 200, json: async () => { throw new SyntaxError('untrusted-private-marker') } }))
    const result = await actions[action]()
    assert.equal(result.kind, action === 'session' ? 'unavailable' : 'unexpected')
    assert.equal(JSON.stringify(result).includes('untrusted-private-marker'), false)
  })

  test(`${action} never retries a network failure`, async (t) => {
    let calls = 0
    replaceFetch(t, async () => { calls += 1; throw new TypeError('untrusted-private-marker') })
    const result = await actions[action]()
    assert.equal(result.kind, action === 'session' ? 'unavailable' : 'network')
    assert.equal(calls, 1)
    assert.equal(JSON.stringify(result).includes('untrusted-private-marker'), false)
  })

  test(`${action} respects caller cancellation without sending a pre-cancelled request`, async (t) => {
    let calls = 0
    replaceFetch(t, async () => { calls += 1; return response(200, session) })
    const controller = new AbortController()
    controller.abort()
    assert.equal((await actions[action](controller.signal)).kind, 'cancelled')
    assert.equal(calls, 0)
  })

  test(`${action} has a ten-second timeout covering response body consumption`, async (t) => {
    let timer
    let bodyStarted
    const started = new Promise((resolve) => { bodyStarted = resolve })
    const originalSet = globalThis.setTimeout
    const originalClear = globalThis.clearTimeout
    globalThis.setTimeout = (callback, delay) => { assert.equal(delay, 10000); timer = callback; return 1 }
    globalThis.clearTimeout = () => {}
    t.after(() => { globalThis.setTimeout = originalSet; globalThis.clearTimeout = originalClear })
    replaceFetch(t, async (_, options) => {
      const consume = () => new Promise((resolve, reject) => {
        bodyStarted()
        options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })
      })
      return { status: action === 'logout' ? 204 : 200, json: consume, text: consume }
    })
    const pending = actions[action]()
    await started
    timer()
    const result = await pending
    assert.equal(result.kind, action === 'session' ? 'unavailable' : 'network')
  })
}

for (const [status, body, expected] of [
  [201, session.user, 'success'],
  [409, { detail: 'An account with this email already exists.' }, 'invalid'],
  [422, { detail: [{ loc: ['body', 'email'], msg: 'Enter a valid email address.', type: 'value_error' }] }, 'invalid'],
  [503, { detail: 'Registration unavailable. Please try again.' }, 'unavailable'],
  [403, { detail: 'Request not allowed.' }, 'unexpected'],
  [500, { detail: 'Internal server error' }, 'unexpected'],
  [201, { ...session.user, token: 'untrusted-private-marker' }, 'unexpected'],
]) {
  test(`registration keeps its safe ${status}/${expected} contract and request headers`, async (t) => {
    let calls = 0
    replaceFetch(t, async (url, options) => {
      calls += 1
      assert.equal(url, '/api/auth/register')
      assert.equal(options.method, 'POST')
      assert.equal(options.credentials, 'same-origin')
      assert.equal(options.headers['Content-Type'], 'application/json')
      assert.equal(options.headers['X-GarageGuide-CSRF'], '1')
      return response(status, body)
    })
    const result = await registerAccount({ ...details(), password_confirmation: details().password })
    assert.equal(result.kind, expected)
    assert.equal(calls, 1)
    assert.equal(JSON.stringify(result).includes('untrusted-private-marker'), false)
  })
}
