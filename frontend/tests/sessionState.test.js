import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createMemoryRouter, matchRoutes } from 'react-router-dom'
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
  const restoring = store.enter('startup', '/')
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
  await store.enter('startup', '/')
  assert.equal(store.getSnapshot().status, 'guest')
  response = { kind: 'unavailable' }
  await store.enter('account', '/account')
  assert.equal(store.getSnapshot().status, 'unavailable')
  response = success(1)
  await store.recheck()
  assert.equal(store.getSnapshot().status, 'authenticated')
})

test('protected navigation requires a fresh check before its identity can be displayed', async () => {
  const reply = deferred()
  let calls = 0
  const store = fixture({ getSession: () => ++calls === 1 ? Promise.resolve(success(1)) : reply.promise })
  await store.enter('public', '/')
  const checking = store.enter('account', '/account')
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
  const previous = store.enter('old', '/')
  const current = store.enter('new', '/account')
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
  await store.enter('account', '/account')
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
  await store.enter('login', '/')
  const login = store.login({ email: 'synthetic@example.com', password: String.fromCharCode(97).repeat(15) })
  await store.enter('registration', '/')
  reply.resolve(success(2))
  assert.equal((await login).kind, 'cancelled')
  assert.equal(store.getSnapshot().status, 'guest')
})

for (const kind of ['invalid', 'network', 'unavailable', 'forbidden', 'unexpected']) {
  test(`failed login ${kind} preserves prior valid identity without retaining credentials`, async () => {
    const store = fixture({ loginAccount: async () => ({ kind }) })
    await store.enter('login', '/')
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
    await store.enter('account', '/account')
    assert.equal((await store.logout()).kind, kind)
    assert.equal(store.getSnapshot().status, 'authenticated')
    assert.equal(store.getSnapshot().user.id, 1)
  })
}

test('pending mutations prevent repeat submission', async () => {
  const reply = deferred()
  let calls = 0
  const store = fixture({ logoutAccount: () => { calls += 1; return reply.promise } })
  await store.enter('account', '/account')
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
  await store.enter('account', '/account')
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
  await store.enter('account', '/account')
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
  await store.enter('account', '/account')
  result = { kind: 'guest' }
  await store.recheck()
  assert.equal(store.getSnapshot().user, null)
  assert.equal(store.getSnapshot().expires_at, null)
  assert.equal(store.getSnapshot().notice, 'Your session has ended. Please sign in again.')
})

test('unavailable revalidation hides content while preserving potentially valid identity', async () => {
  let result = success(1)
  const store = fixture({ getSession: async () => result })
  await store.enter('account', '/account')
  result = { kind: 'unavailable' }
  await store.recheck()
  assert.equal(store.getSnapshot().status, 'unavailable')
  assert.equal(store.getSnapshot().user.id, 1)
})

test('an already-past response deadline clears identity without starting a renewal loop', async () => {
  let calls = 0
  const store = fixture({ getSession: async () => {
    calls += 1
    return { kind: 'success', session: { ...session(1), expires_at: '2026-11-06T11:59:59Z' } }
  } })
  await store.enter('account', '/account')
  assert.equal(store.getSnapshot().status, 'guest')
  assert.equal(store.getSnapshot().user, null)
  assert.equal(store.getSnapshot().expires_at, null)
  assert.equal(calls, 1)
})

test('document departure cancels work and never accepts its late identity', async () => {
  const reply = deferred()
  const store = fixture({ getSession: () => reply.promise })
  const pending = store.enter('account', '/account')
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
  await store.enter('login', '/')
  assert.equal(store.getSnapshot().status, 'unavailable')
  result = { kind: 'guest' }
  await store.recheck()
  assert.equal(store.getSnapshot().status, 'guest')
  assert.equal(store.getSnapshot().notice, '')
})

const accountPaths = ['/account', '/account/', '/ACCOUNT', '/AcCoUnT/']
const routes = [{ path: '/', id: 'public' }, { path: '/account', id: 'account' }]

for (const pathname of accountPaths) {
  for (const kind of ['success', 'guest', 'unavailable']) {
    test(`${pathname} gates cached identity until router-matched revalidation returns ${kind}`, async () => {
      assert.equal(matchRoutes(routes, pathname).at(-1).route.id, 'account')
      const reply = deferred()
      let calls = 0
      const store = fixture({ getSession: () => ++calls === 1 ? Promise.resolve(success(1)) : reply.promise })
      await store.enter('public', '/')
      const checking = store.enter('protected', pathname)
      assert.equal(calls, 2)
      assert.equal(store.getSnapshot().status, 'loading')
      assert.equal(store.getSnapshot().checkedFor, null)
      reply.resolve(kind === 'success' ? success(2) : { kind })
      await checking
      assert.equal(store.getSnapshot().checkedFor, 'protected')
      assert.equal(store.getSnapshot().status, kind === 'success' ? 'authenticated' : kind)
      if (kind === 'success') assert.equal(store.getSnapshot().user.id, 2)
      if (kind === 'guest') assert.equal(store.getSnapshot().user, null)
    })
  }
}

for (const pathname of ['/accounting', '/accounts', '/account/settings', '/', '/login']) {
  test(`unrelated path ${pathname} does not trigger protected navigation`, async () => {
    const matched = matchRoutes(routes, pathname)
    assert.notEqual(matched?.at(-1).route.id, 'account')
    let calls = 0
    const store = fixture({ getSession: async () => { calls += 1; return success(1) } })
    await store.enter('startup', '/')
    await store.enter('unrelated', pathname)
    assert.equal(calls, 1)
    assert.equal(store.getSnapshot().checkedFor, 'unrelated')
  })
}

for (const kind of ['guest', 'unavailable']) {
  test(`late success cannot undo ${kind} on a different account-route variant`, async () => {
    const old = deferred()
    const next = deferred()
    let calls = 0
    const store = fixture({ getSession: () => {
      calls += 1
      return calls === 1 ? Promise.resolve(success(1)) : calls === 2 ? old.promise : next.promise
    } })
    await store.enter('public', '/')
    const previous = store.enter('first', '/account/')
    const current = store.enter('second', '/ACCOUNT')
    next.resolve({ kind })
    await current
    old.resolve(success(2))
    assert.equal((await previous).kind, 'cancelled')
    assert.equal(store.getSnapshot().status, kind)
    assert.equal(store.getSnapshot().checkedFor, 'second')
    assert.notEqual(store.getSnapshot().user?.id, 2)
  })
}

for (const pathname of accountPaths) {
  test(`router Back/Forward revalidates ${pathname} even when its location key is reused`, async (t) => {
    const router = createMemoryRouter(routes, { initialEntries: ['/', pathname, '/'], initialIndex: 0 })
    t.after(() => router.dispose())
    let result = success(1)
    let calls = 0
    const store = fixture({ getSession: async () => { calls += 1; return result } })
    let checking = store.enter(router.state.location.key, router.state.location.pathname)
    await checking
    let key = router.state.location.key
    const unsubscribe = router.subscribe(({ location }) => {
      if (location.key !== key) {
        key = location.key
        checking = store.enter(key, location.pathname)
      }
    })
    t.after(unsubscribe)
    await router.navigate(1)
    await checking
    assert.equal(router.state.matches.at(-1).route.id, 'account')
    const accountKey = key
    assert.equal(calls, 2)
    await router.navigate(1)
    await checking
    result = { kind: 'guest' }
    await router.navigate(-1)
    await checking
    assert.equal(key, accountKey)
    assert.equal(calls, 3)
    assert.equal(store.getSnapshot().status, 'guest')
    assert.equal(store.getSnapshot().user, null)
    await router.navigate(-1)
    await checking
    result = { kind: 'unavailable' }
    await router.navigate(1)
    await checking
    assert.equal(key, accountKey)
    assert.equal(calls, 4)
    assert.equal(store.getSnapshot().status, 'unavailable')
    assert.equal(store.getSnapshot().user, null)
  })
}

function watchDeadline(t, store) {
  let deadline
  let stopTimer
  const update = () => {
    const next = store.getSnapshot().expires_at
    if (next === deadline) return
    stopTimer?.()
    deadline = next
    stopTimer = store.watchExpiry()
  }
  const unsubscribe = store.subscribe(update)
  update()
  t.after(() => { unsubscribe(); stopTimer?.(); store.dispose() })
}

const minute = 60_000
for (const offset of [0, 5 * minute, -5 * minute]) {
  test(`idle deadline clears identity without renewal with device clock offset ${offset / minute} minutes`, async (t) => {
    t.mock.timers.enable({ apis: ['Date', 'setTimeout'], now: now + offset })
    let calls = 0
    const store = createSessionStore({ getSession: async () => {
      calls += 1
      return { kind: 'success', session: {
        ...session(1), expires_at: new Date(Date.now() - offset + 30 * minute).toISOString(),
      } }
    } })
    watchDeadline(t, store)
    await store.enter('account', '/account')
    const delay = 30 * minute - offset
    t.mock.timers.tick(delay - 1)
    assert.equal(store.getSnapshot().status, 'authenticated')
    t.mock.timers.tick(1)
    assert.equal(store.getSnapshot().status, 'guest')
    assert.equal(store.getSnapshot().user, null)
    assert.equal(store.getSnapshot().expires_at, null)
    assert.equal(store.getSnapshot().busy, null)
    assert.equal(store.getSnapshot().notice, 'Your session has ended. Please sign in again.')
    await Promise.resolve()
    assert.equal(calls, 1)
    t.mock.timers.tick(9 * 60 * minute)
    await Promise.resolve()
    assert.equal(calls, 1)
    assert.equal(store.getSnapshot().user, null)
  })
}

test('a response at deadline equality clears identity without requesting again', async (t) => {
  t.mock.timers.enable({ apis: ['Date', 'setTimeout'], now })
  let calls = 0
  const store = createSessionStore({ getSession: async () => {
    calls += 1
    return { kind: 'success', session: { ...session(1), expires_at: new Date(now).toISOString() } }
  } })
  watchDeadline(t, store)
  await store.enter('account', '/account')
  t.mock.timers.tick(60 * minute)
  assert.equal(store.getSnapshot().status, 'guest')
  assert.equal(store.getSnapshot().user, null)
  assert.equal(store.getSnapshot().expires_at, null)
  assert.equal(calls, 1)
})

for (const action of ['navigation', 'visibility', 'retry']) {
  for (const kind of ['success', 'guest', 'unavailable']) {
    test(`${action} after local expiry revalidates deliberately and handles ${kind} without stale identity`, async (t) => {
      t.mock.timers.enable({ apis: ['Date', 'setTimeout'], now })
      let calls = 0
      const reply = deferred()
      const store = createSessionStore({ getSession: () => ++calls === 1 ? Promise.resolve(success(1)) : reply.promise })
      watchDeadline(t, store)
      await store.enter('account', '/account')
      if (action === 'visibility') store.hide()
      t.mock.timers.tick(30 * minute)
      assert.equal(store.getSnapshot().user, null)
      assert.equal(calls, 1)
      const checking = action === 'navigation' ? store.enter('next', '/ACCOUNT/') :
        action === 'visibility' ? store.resume() : store.recheck()
      assert.equal(calls, 2)
      assert.equal(store.getSnapshot().status, 'loading')
      assert.equal(store.getSnapshot().user, null)
      assert.equal(store.getSnapshot().checkedFor, null)
      reply.resolve(kind === 'success' ? {
        kind, session: { ...session(2), expires_at: new Date(Date.now() + 30 * minute).toISOString() },
      } : { kind })
      await checking
      assert.equal(store.getSnapshot().status, kind === 'success' ? 'authenticated' : kind)
      assert.equal(store.getSnapshot().user?.id ?? null, kind === 'success' ? 2 : null)
      t.mock.timers.tick(60 * minute)
      await Promise.resolve()
      assert.equal(store.getSnapshot().user, null)
      assert.equal(calls, 2)
    })
  }
}

for (const kind of ['session', 'login', 'logout']) {
  test(`deadline aborts pending ${kind} and its late success cannot restore identity or trigger deferred checks`, async (t) => {
    t.mock.timers.enable({ apis: ['Date', 'setTimeout'], now })
    const reply = deferred()
    let calls = 0
    let pendingSignal
    const pending = (signal) => { pendingSignal = signal; return reply.promise }
    const store = createSessionStore({
      getSession: (signal) => ++calls === 1 ? Promise.resolve(success(1)) : pending(signal),
      loginAccount: (details, signal) => pending(signal), logoutAccount: pending,
    })
    watchDeadline(t, store)
    await store.enter('account', '/account')
    const checking = kind === 'session' ? store.recheck() : kind === 'login' ? store.login({}) : store.logout()
    store.hide()
    if (kind !== 'session') await store.resume()
    const callsBeforeExpiry = calls
    t.mock.timers.tick(30 * minute)
    assert.equal(pendingSignal.aborted, true)
    assert.equal(store.getSnapshot().status, 'guest')
    assert.equal(store.getSnapshot().user, null)
    reply.resolve({ kind: 'success', session: { ...session(2), expires_at: new Date(Date.now() + 30 * minute).toISOString() } })
    assert.equal((await checking).kind, 'cancelled')
    assert.equal(store.getSnapshot().user, null)
    assert.equal(store.getSnapshot().expires_at, null)
    t.mock.timers.tick(60 * minute)
    await Promise.resolve()
    assert.equal(calls, callsBeforeExpiry)
  })
}

test('an obsolete deadline cannot clear a session renewed by deliberate navigation', async (t) => {
  t.mock.timers.enable({ apis: ['Date', 'setTimeout'], now })
  let calls = 0
  const store = createSessionStore({ getSession: async () => {
    calls += 1
    return { kind: 'success', session: { ...session(1), expires_at: new Date(Date.now() + 30 * minute).toISOString() } }
  } })
  watchDeadline(t, store)
  await store.enter('first', '/account')
  t.mock.timers.tick(10 * minute)
  await store.enter('second', '/ACCOUNT')
  t.mock.timers.tick(20 * minute)
  assert.equal(store.getSnapshot().status, 'authenticated')
  t.mock.timers.tick(10 * minute)
  assert.equal(store.getSnapshot().status, 'guest')
  assert.equal(store.getSnapshot().user, null)
  assert.equal(calls, 2)
})
