import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createMemoryRouter, matchRoutes } from 'react-router-dom'
import { createSessionStore } from '../src/sessionState.js'
import { protectedRoutes, vehiclesRoute, newVehicleRoute } from '../src/vehicleRoutes.js'

const now = Date.parse('2026-11-13T12:00:00Z')
const minute = 60_000
const session = (id = 1, deadline = now + 30 * minute) => ({
  user: { id, email: `synthetic-${id}@example.com`, created_at: '2026-11-13T11:00:00Z' }, expires_at: new Date(deadline).toISOString(),
})
const success = (id) => ({ kind: 'success', session: session(id) })
const vehicles = (deadline = now + 31 * minute) => ({ kind: 'success', vehicles: [{ id: 7 }], deadline: new Date(deadline).toISOString() })
function deferred() { let resolve; const promise = new Promise((done) => { resolve = done }); return { promise, resolve } }
function fixture(api = {}, clock = () => now) {
  let calls = 0
  const store = createSessionStore({ getSession: async () => { calls += 1; return success(1) }, loginAccount: async () => success(1), logoutAccount: async () => ({ kind: 'success' }), ...api }, clock)
  return { store, calls: () => calls }
}

const variants = ['/vehicles', '/vehicles/', '/VEHICLES', '/%76ehicles', '/veh%69cles',
  '/vehicles/new', '/vehicles/new/', '/VEHICLES/NEW', '/%76ehicles/%6Eew']
for (const path of variants) {
  test(`real route matching gates direct, refresh and protected navigation for ${path}`, async () => {
    const reply = deferred()
    let calls = 0
    const store = fixture({ getSession: () => ++calls === 1 ? Promise.resolve(success(1)) : reply.promise }).store
    const real = matchRoutes([vehiclesRoute, newVehicleRoute], { pathname: path })
    assert.ok(real)
    await store.enter('direct', path)
    const navigation = store.enter('refresh', path)
    assert.equal(store.getSnapshot().status, 'loading')
    assert.equal(store.getSnapshot().checkedFor, null)
    reply.resolve(success(1))
    await navigation
    assert.equal(store.getSnapshot().checkedFor, 'refresh')
    assert.equal(calls, 2)
  })
  for (const kind of ['guest', 'unavailable']) {
    test(`${path} rejected or unavailable validation gates old identity: ${kind}`, async () => {
      let calls = 0
      const store = fixture({ getSession: async () => ++calls === 1 ? success(1) : { kind } }).store
      await store.enter('public', '/')
      await store.enter('private', path)
      assert.equal(store.getSnapshot().status, kind)
      assert.equal(store.getSnapshot().checkedFor, 'private')
      assert.notEqual(store.getSnapshot().status, 'authenticated')
    })
  }
}

for (const path of ['/vehicles/1', '/vehicles/new/other', '/vehiclesx', '/vehicle', '/%76ehiclesx', '/%zz', '/vehicles/%zz', '/vehicles/ne%']) {
  test(`unrelated or malformed route is not classified as a vehicle page: ${path}`, async (t) => {
    t.mock.method(console, 'warn', () => {})
    assert.equal(matchRoutes([vehiclesRoute, newVehicleRoute], { pathname: path }), null)
    const { store, calls } = fixture()
    await store.enter('initial', '/')
    await store.enter('other', path)
    assert.equal(calls(), 1)
  })
}

test('successful vehicle activity accepts only the committed deadline without extra session traffic', async () => {
  const { store, calls } = fixture()
  await store.enter('garage', '/vehicles')
  assert.equal((await store.authenticatedRequest(async () => vehicles())).kind, 'success')
  assert.equal(store.getSnapshot().expires_at, new Date(now + 31 * minute).toISOString())
  assert.equal(calls(), 1)
})

for (const deadline of [null, 'garbage', '2026-11-13T13:00:00', new Date(now + 29 * minute).toISOString()]) {
  test('missing, malformed or regressing vehicle metadata cannot update identity or deadline', async () => {
    const { store } = fixture()
    await store.enter('garage', '/vehicles')
    const before = store.getSnapshot().expires_at
    assert.equal((await store.authenticatedRequest(async () => ({ ...vehicles(), deadline }))).kind, 'unexpected')
    assert.equal(store.getSnapshot().expires_at, before)
    assert.equal(store.getSnapshot().user.id, 1)
  })
}

test('request generation rejects older response and newer-looking stale metadata', async () => {
  const { store } = fixture()
  await store.enter('garage', '/vehicles')
  const old = deferred()
  let signal
  const first = store.authenticatedRequest((value) => { signal = value; return old.promise })
  await store.authenticatedRequest(async () => vehicles(now + 32 * minute))
  assert.equal(signal.aborted, true)
  old.resolve(vehicles(now + 40 * minute))
  assert.equal((await first).kind, 'cancelled')
  assert.equal(store.getSnapshot().expires_at, new Date(now + 32 * minute).toISOString())
})

for (const action of ['logout', 'same-user-login', 'different-user-login', 'navigation', 'revalidation', 'visibility']) {
  test(`authentication/navigation generation cancels private work after ${action}`, async () => {
    const { store } = fixture({ loginAccount: async () => success(action === 'different-user-login' ? 2 : 1) })
    await store.enter('garage', '/vehicles')
    const reply = deferred()
    const previous = store.getSnapshot().generation
    const pending = store.authenticatedRequest(() => reply.promise)
    if (action === 'logout') await store.logout()
    else if (action.endsWith('login')) await store.login({})
    else if (action === 'navigation') await store.enter('create', '/vehicles/new')
    else if (action === 'revalidation') await store.recheck()
    else { store.hide(); await store.resume() }
    reply.resolve(vehicles())
    assert.equal((await pending).kind, 'cancelled')
    assert.ok(store.getSnapshot().generation > previous)
    assert.notEqual(store.getSnapshot().expires_at, vehicles().deadline)
    if (action === 'logout') assert.equal(store.getSnapshot().user, null)
  })
}

test('401 clears identity; auth 503 gates and clears it; vehicle 503 preserves shell without extending deadline', async () => {
  for (const kind of ['guest', 'authentication-unavailable', 'unavailable']) {
    const { store, calls } = fixture()
    await store.enter('garage', '/vehicles')
    const before = store.getSnapshot().expires_at
    await store.authenticatedRequest(async () => ({ kind, message: 'Safe feedback' }))
    assert.equal(store.getSnapshot().status, kind === 'guest' ? 'guest' : kind === 'authentication-unavailable' ? 'unavailable' : 'authenticated')
    if (kind === 'unavailable') assert.equal(store.getSnapshot().expires_at, before)
    else assert.equal(store.getSnapshot().user, null)
    assert.equal(calls(), 1)
  }
})

for (const offset of [0, 5 * minute, -5 * minute]) {
  test(`local expiration clears identity and aborts late vehicles with clock offset ${offset}`, async (t) => {
    t.mock.timers.enable({ apis: ['Date', 'setTimeout'], now: now + offset })
    const { store, calls } = fixture({}, Date.now)
    await store.enter('garage', '/vehicles')
    const reply = deferred()
    const pending = store.authenticatedRequest(() => reply.promise)
    const stop = store.watchExpiry()
    t.after(stop)
    t.mock.timers.tick(30 * minute - offset)
    assert.equal(store.getSnapshot().user, null)
    reply.resolve(vehicles(now + 60 * minute))
    assert.equal((await pending).kind, 'cancelled')
    t.mock.timers.tick(8 * 60 * minute)
    assert.equal(calls(), 1)
    assert.equal(store.getSnapshot().expires_at, null)
  })
}

test('deadline equality or expired response ends session with no automatic validation', async () => {
  const { store, calls } = fixture()
  await store.enter('garage', '/vehicles')
  assert.equal((await store.authenticatedRequest(async () => vehicles(now))).kind, 'guest')
  assert.equal(store.getSnapshot().user, null)
  assert.equal(calls(), 1)
  let sent = false
  assert.equal((await store.authenticatedRequest(async () => { sent = true; return vehicles() })).kind, 'cancelled')
  assert.equal(sent, false)
})

test('renewed timer uses accepted deadline without an expiry request or idle extension loop', async (t) => {
  t.mock.timers.enable({ apis: ['Date', 'setTimeout'], now })
  const { store, calls } = fixture({}, Date.now)
  await store.enter('garage', '/vehicles')
  const stopOld = store.watchExpiry()
  t.mock.timers.tick(10 * minute)
  await store.authenticatedRequest(async () => vehicles(now + 40 * minute))
  stopOld()
  const stop = store.watchExpiry()
  t.after(stop)
  t.mock.timers.tick(20 * minute)
  assert.equal(store.getSnapshot().status, 'authenticated')
  t.mock.timers.tick(10 * minute)
  assert.equal(store.getSnapshot().status, 'guest')
  assert.equal(calls(), 1)
})

test('Back/Forward reusing history keys requires fresh checks and invalidates prior vehicle results', async () => {
  const { store, calls } = fixture()
  const router = createMemoryRouter([{ path: '/' }, ...protectedRoutes], { initialEntries: ['/'] })
  let checking = store.enter(router.state.location.key, router.state.location.pathname)
  let previous = router.state.location.key
  const unsubscribe = router.subscribe(({ location }) => {
    if (location.key === previous) return
    previous = location.key
    checking = store.enter(location.key, location.pathname)
  })
  try {
    await checking
    await router.navigate('/%76ehicles')
    await checking
    const reply = deferred()
    const stale = store.authenticatedRequest(() => reply.promise)
    await router.navigate('/VEHICLES/NEW/')
    await checking
    await router.navigate(-1)
    await checking
    reply.resolve(vehicles())
    assert.equal((await stale).kind, 'cancelled')
    await router.navigate(1)
    await checking
    assert.equal(calls(), 5)
    assert.equal(store.getSnapshot().checkedFor, router.state.location.key)
  } finally { unsubscribe(); router.dispose(); store.dispose() }
})

test('a delayed expiry timer cannot let a late vehicle response revive identity', async () => {
  let currentTime = now
  const { store, calls } = fixture({}, () => currentTime)
  await store.enter('garage', '/vehicles')
  const reply = deferred()
  const pending = store.authenticatedRequest(() => reply.promise)
  currentTime = now + 30 * minute
  reply.resolve(vehicles(now + 60 * minute))
  assert.equal((await pending).kind, 'guest')
  assert.equal(store.getSnapshot().user, null)
  assert.equal(store.getSnapshot().expires_at, null)
  assert.equal(calls(), 1)
})

for (const action of ['navigation', 'visibility', 'retry']) {
  test(`after local vehicle-page expiration only deliberate ${action} can validate again`, async (t) => {
    t.mock.timers.enable({ apis: ['Date', 'setTimeout'], now })
    let calls = 0
    const store = createSessionStore({ getSession: async () => { calls += 1; return calls === 1 ? success(1) : { kind: 'guest' } } })
    await store.enter('garage', '/vehicles')
    const stop = store.watchExpiry()
    t.after(stop)
    t.mock.timers.tick(30 * minute)
    assert.equal(calls, 1)
    assert.equal(store.getSnapshot().user, null)
    if (action === 'navigation') await store.enter('create', '/%76ehicles/%6Eew')
    else if (action === 'visibility') { store.hide(); await store.resume() }
    else await store.recheck()
    assert.equal(calls, 2)
    assert.equal(store.getSnapshot().user, null)
    t.mock.timers.tick(60 * minute)
    assert.equal(calls, 2)
  })
}
