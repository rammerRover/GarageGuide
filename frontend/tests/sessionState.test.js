import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createSessionStore } from '../src/sessionState.js'

const now = Date.parse('2026-11-06T12:00:00Z')
const session = (id = 1) => ({
  user: { id, email: `synthetic-${id}@example.com`, created_at: '2026-11-06T11:00:00Z' },
  expires_at: '2026-11-06T12:30:00Z',
})
const success = (id) => ({ kind: 'success', session: session(id) })
function deferred() {
  let resolve
  const promise = new Promise((complete) => { resolve = complete })
  return { promise, resolve }
}
function fixture(overrides = {}) {
  const api = {
    getSession: async () => success(1), loginAccount: async () => success(2),
    logoutAccount: async () => ({ kind: 'success' }), ...overrides,
  }
  return createSessionStore(api, () => now)
}

test('startup gates unknown identity and retains only public session fields after restoration', async () => {
  const reply = deferred()
  const store = fixture({ getSession: () => reply.promise })
  const restoring = store.enter('startup', false)
  assert.equal(store.getSnapshot().status, 'loading')
  assert.equal(store.getSnapshot().user, null)
  reply.resolve(success(1))
  await restoring
  assert.equal(store.getSnapshot().status, 'authenticated')
  assert.equal(store.getSnapshot().checkedFor, 'startup')
  assert.deepEqual(store.getSnapshot().user, session(1).user)
  assert.deepEqual(Object.keys(store.getSnapshot().user), ['id', 'email', 'created_at'])
})

test('startup 401 means guest; unavailable is distinct and deliberate retry can recover', async () => {
  let response = { kind: 'guest' }
  const store = fixture({ getSession: async () => response })
  await store.enter('startup', false)
  assert.equal(store.getSnapshot().status, 'guest')
  response = { kind: 'unavailable' }
  await store.enter('account', true)
  assert.equal(store.getSnapshot().status, 'unavailable')
  response = success(1)
  await store.recheck()
  assert.equal(store.getSnapshot().status, 'authenticated')
})

test('protected navigation requires a fresh check before its identity can be displayed', async () => {
  const reply = deferred()
  let calls = 0
  const store = fixture({ getSession: () => ++calls === 1 ? Promise.resolve(success(1)) : reply.promise })
  await store.enter('public', false)
  const checking = store.enter('account', true)
  assert.equal(store.getSnapshot().status, 'loading')
  assert.equal(store.getSnapshot().checkedFor, null)
  reply.resolve(success(1))
  await checking
  assert.equal(store.getSnapshot().checkedFor, 'account')
})

test('navigation aborts and ignores late session responses for another identity', async () => {
  const old = deferred()
  const next = deferred()
  const signals = []
  const store = fixture({ getSession: (signal) => { signals.push(signal); return signals.length === 1 ? old.promise : next.promise } })
  const previous = store.enter('old', false)
  const current = store.enter('new', true)
  assert.equal(signals[0].aborted, true)
  next.resolve(success(2))
  await current
  old.resolve(success(1))
  assert.equal((await previous).kind, 'cancelled')
  assert.equal(store.getSnapshot().user.id, 2)
})

test('logout clears public identity and ignores a late earlier session response', async () => {
  const old = deferred()
  let calls = 0
  const store = fixture({ getSession: () => ++calls === 1 ? Promise.resolve(success(1)) : old.promise })
  await store.enter('account', true)
  const checking = store.recheck()
  await store.logout()
  assert.equal(store.getSnapshot().status, 'guest')
  assert.equal(store.getSnapshot().user, null)
  old.resolve(success(1))
  assert.equal((await checking).kind, 'cancelled')
  assert.equal(store.getSnapshot().user, null)
})

test('a login response arriving after navigation cannot restore identity', async () => {
  const reply = deferred()
  const store = fixture({ getSession: async () => ({ kind: 'guest' }), loginAccount: () => reply.promise })
  await store.enter('login', false)
  const login = store.login({ email: 'synthetic@example.com', password: String.fromCharCode(97).repeat(15) })
  await store.enter('registration', false)
  reply.resolve(success(2))
  assert.equal((await login).kind, 'cancelled')
  assert.equal(store.getSnapshot().status, 'guest')
})

for (const kind of ['invalid', 'network', 'unavailable', 'forbidden', 'unexpected']) {
  test(`failed login ${kind} preserves prior valid identity without retaining credentials`, async () => {
    const store = fixture({ loginAccount: async () => ({ kind }) })
    await store.enter('login', false)
    const password = String.fromCharCode(97).repeat(15)
    assert.equal((await store.login({ email: 'synthetic@example.com', password })).kind, kind)
    assert.equal(store.getSnapshot().status, 'authenticated')
    assert.equal(store.getSnapshot().user.id, 1)
    assert.equal(JSON.stringify(store.getSnapshot()).includes(password), false)
  })
}

for (const kind of ['network', 'unavailable', 'forbidden', 'unexpected']) {
  test(`failed logout ${kind} does not claim guest state`, async () => {
    const store = fixture({ logoutAccount: async () => ({ kind }) })
    await store.enter('account', true)
    assert.equal((await store.logout()).kind, kind)
    assert.equal(store.getSnapshot().status, 'authenticated')
    assert.equal(store.getSnapshot().user.id, 1)
  })
}

test('pending mutations prevent repeat submission', async () => {
  const reply = deferred()
  let calls = 0
  const store = fixture({ logoutAccount: () => { calls += 1; return reply.promise } })
  await store.enter('account', true)
  const logout = store.logout()
  assert.equal(store.getSnapshot().busy, 'logout')
  assert.equal((await store.logout()).kind, 'cancelled')
  assert.equal(calls, 1)
  reply.resolve({ kind: 'success' })
  await logout
  assert.equal(store.getSnapshot().busy, null)
})

test('visibility return gates identity and rechecks once without polling', async () => {
  let calls = 0
  const store = fixture({ getSession: async () => { calls += 1; return success(1) } })
  await store.enter('account', true)
  store.hide()
  assert.equal(store.getSnapshot().visible, false)
  assert.equal(store.getSnapshot().checkedFor, null)
  assert.equal(calls, 1)
  await store.resume()
  assert.equal(store.getSnapshot().visible, true)
  assert.equal(store.getSnapshot().checkedFor, 'account')
  assert.equal(calls, 2)
})

test('deferred visibility check still runs when hiding the account cancels logout', async () => {
  const reply = deferred()
  let calls = 0
  const store = fixture({
    getSession: async () => { calls += 1; return success(1) }, logoutAccount: () => reply.promise,
  })
  await store.enter('account', true)
  const controller = new AbortController()
  const pending = store.logout(controller.signal)
  store.hide()
  await store.resume()
  controller.abort()
  reply.resolve({ kind: 'network' })
  assert.equal((await pending).kind, 'cancelled')
  await Promise.resolve()
  assert.equal(calls, 2)
  assert.equal(store.getSnapshot().status, 'authenticated')
})

test('protected rejection discards private identity and uses only a safe in-memory notice', async () => {
  let result = success(1)
  const store = fixture({ getSession: async () => result })
  await store.enter('account', true)
  result = { kind: 'guest' }
  await store.recheck()
  assert.equal(store.getSnapshot().user, null)
  assert.equal(store.getSnapshot().expires_at, null)
  assert.equal(store.getSnapshot().notice, 'Your session has ended. Please sign in again.')
})

test('unavailable revalidation hides content while preserving potentially valid identity', async () => {
  let result = success(1)
  const store = fixture({ getSession: async () => result })
  await store.enter('account', true)
  result = { kind: 'unavailable' }
  await store.recheck()
  assert.equal(store.getSnapshot().status, 'unavailable')
  assert.equal(store.getSnapshot().user.id, 1)
})

test('an already-past response deadline fails unavailable instead of starting a renewal loop', async () => {
  let calls = 0
  const store = fixture({ getSession: async () => {
    calls += 1
    return { kind: 'success', session: { ...session(1), expires_at: '2026-11-06T11:59:59Z' } }
  } })
  await store.enter('account', true)
  assert.equal(store.getSnapshot().status, 'unavailable')
  assert.equal(calls, 1)
})

test('document departure cancels work and never accepts its late identity', async () => {
  const reply = deferred()
  const store = fixture({ getSession: () => reply.promise })
  const pending = store.enter('account', true)
  store.depart()
  reply.resolve(success(1))
  assert.equal((await pending).kind, 'cancelled')
  assert.equal(store.getSnapshot().visible, false)
  assert.equal(store.getSnapshot().checkedFor, null)
  assert.equal(store.getSnapshot().user, null)
})

test('a confirmed public guest response clears an earlier unavailable notice', async () => {
  let result = { kind: 'unavailable' }
  const store = fixture({ getSession: async () => result })
  await store.enter('login', false)
  assert.equal(store.getSnapshot().status, 'unavailable')
  result = { kind: 'guest' }
  await store.recheck()
  assert.equal(store.getSnapshot().status, 'guest')
  assert.equal(store.getSnapshot().notice, '')
})
