import assert from 'node:assert/strict'
import test from 'node:test'
import { now, record, stamp, success, fixture, loaded, deferred, input } from './serviceFixtures.js'
import { matchRoutes } from 'react-router-dom'
import { protectedRoutes, newVehicleRoute, serviceHistoryRoute, serviceRecordRoute } from '../src/vehicleRoutes.js'
import { isServiceId } from '../src/serviceValidation.js'

for (const prefix of ['/vehicles/7/services', '/VEHICLES/7/SERVICES', '/%76ehicles/%37/serv%69ces']) {
  for (const suffix of ['', '/', '/8', '/%38', '/8/']) test(`shared protected service descriptors match ${prefix + suffix}`, async () => {
    const matches = matchRoutes(protectedRoutes, { pathname: prefix + suffix })
    const matched = matches.at(-1)
    assert.equal(matched.route, suffix.replaceAll('/', '') ? serviceRecordRoute : serviceHistoryRoute)
    assert.equal(matched.params.vehicleId, '7')
    if (matched.route === serviceRecordRoute) assert.equal(matched.params.serviceId, '8')
    const f = await fixture()
    const checks = f.calls.session
    const pending = f.session.enter('services', prefix + suffix)
    assert.equal(f.session.getSnapshot().status, 'loading')
    await pending
    assert.equal(f.calls.session, checks + 1)
    f.store.dispose()
  })
}
for (const path of ['/vehicles/7/services-extra', '/vehicles/7/services/8/edit', '/vehicles/7/services/8/parts', '/vehicles/7/service']) test(`unrelated service paths do not match: ${path}`, () => {
  assert.equal(matchRoutes(protectedRoutes, { pathname: path }), null)
})
test('static new-vehicle route retains precedence, including decoded forms', () => {
  for (const pathname of ['/vehicles/new', '/VEHICLES/NEW/', '/vehicles/%6Eew']) assert.equal(matchRoutes(protectedRoutes, { pathname }).at(-1).route, newVehicleRoute)
})
for (const id of ['01', '0', '+7', '2147483648', '7.0', '%EF%BC%97']) test(`matching a route does not authorize an invalid decoded ID: ${id}`, async () => {
  const matched = matchRoutes(protectedRoutes, { pathname: `/vehicles/${id}/services/8` }).at(-1)
  assert.equal(isServiceId(matched.params.vehicleId), false)
  const f = await fixture()
  await f.store.load(matched.params.vehicleId, '8')
  assert.equal(f.calls.detail.length, 0)
  assert.equal(f.store.getSnapshot().record, null)
  f.store.dispose()
})

for (const operation of ['load', 'create', 'update', 'remove']) {
  for (const event of ['navigation', 'back-forward', 'hidden', 'departure', 'dispose', 'logout', 'account-change', 'same-account-login', 'expiration']) {
    test(`${operation}: ${event} blocks late private results and deadline changes`, async () => {
      let clock = now
      const reply = deferred(), mode = operation === 'create' ? 'history' : 'record'
      const overrides = operation === 'load' ? { getService: () => reply.promise } : { [`${operation}Service`]: () => reply.promise }
      const f = operation === 'load' ? await fixture(mode, overrides, () => clock) : await loaded(mode, overrides, () => clock)
      if (operation === 'create') for (const [key, value] of Object.entries(input)) f.store.edit(key, value)
      if (operation === 'update') { f.store.beginEdit(); f.store.edit('notes', 'Draft') }
      if (operation === 'remove') f.store.requestRemoval()
      const pending = operation === 'load' ? f.store.load('7', '8') : operation === 'remove' ? f.store.confirmRemoval() : f.store.submit()
      if (event === 'navigation') await f.session.enter('other', '/vehicles')
      if (event === 'back-forward') { await f.session.enter('back', '/account'); await f.session.enter('forward', '/vehicles/7') }
      if (event === 'hidden') f.session.hide()
      if (event === 'departure') f.store.depart()
      if (event === 'dispose') f.store.dispose()
      if (event === 'logout') await f.session.logout()
      if (event === 'account-change') await f.session.login({ id: 2 })
      if (event === 'same-account-login') await f.session.login({ id: 1 })
      if (event === 'expiration') { clock = Date.parse(f.session.getSnapshot().expires_at); await f.session.authenticatedRequest(async () => assert.fail('expired session requested data')) }
      const deadline = f.session.getSnapshot().expires_at
      reply.resolve(operation === 'remove' ? { kind: 'success', removed: { id: 8, vehicle_id: 7, deleted: true }, deadline: stamp(60) } : success({ notes: 'Obsolete' }, stamp(60)))
      assert.equal((await pending).kind, 'cancelled')
      assert.equal(f.store.getSnapshot().record, null)
      assert.deepEqual(f.store.getSnapshot().records, [])
      assert.equal(f.store.getSnapshot().draft.description, '')
      assert.equal(f.session.getSnapshot().expires_at, deadline)
      assert.equal(f.calls[operation === 'load' ? 'detail' : operation].length, 1)
      f.store.dispose()
    })
  }
}
for (const kind of ['guest', 'authentication-unavailable']) test(`${kind} gates saved records and drafts`, async () => {
  const f = await loaded('record', { updateService: async () => ({ kind }) })
  f.store.beginEdit(); f.store.edit('notes', 'Private draft'); await f.store.submit()
  assert.equal(f.store.getSnapshot().record, null)
  assert.equal(f.store.getSnapshot().draft.notes, '')
  assert.notEqual(f.session.getSnapshot().status, 'authenticated')
  f.store.dispose()
})
for (const deadline of [undefined, 'malformed', stamp(-1), stamp(30), stamp(31), stamp(29)]) test(`current safe response preserves newer deadline: ${deadline}`, async () => {
  const f = await loaded('record', { getService: async () => ({ kind: 'success', record, deadline }) })
  assert.equal(f.store.getSnapshot().status, 'ready')
  assert.equal(f.session.getSnapshot().expires_at, deadline === stamp(31) ? stamp(31) : stamp(30))
  assert.equal(f.calls.session, 1)
  f.store.dispose()
})
test('deadline equality clears identity without session/data requests, polling, or automatic retry', async (t) => {
  t.mock.timers.enable({ apis: ['setTimeout'] })
  let clock = now
  const f = await loaded('record', {}, () => clock)
  const stop = f.session.watchExpiry()
  const count = f.calls.session
  clock = Date.parse(f.session.getSnapshot().expires_at)
  t.mock.timers.tick(clock - now)
  assert.equal(f.session.getSnapshot().user, null)
  assert.equal(f.store.getSnapshot().record, null)
  assert.equal(f.store.getSnapshot().draft.description, '')
  t.mock.timers.tick(8 * 60 * 60000)
  assert.equal(f.calls.session, count)
  assert.equal(f.calls.detail.length, 1)
  assert.equal(f.calls.update.length, 0)
  stop(); f.store.dispose()
})
for (const kind of ['conflict', 'invalid', 'unavailable', 'uncertain']) test(`late ${kind} cannot overwrite a new draft or deadline`, async () => {
  const reply = deferred()
  const f = await loaded('record', { updateService: () => reply.promise })
  f.store.beginEdit(); f.store.edit('notes', 'Old draft'); const pending = f.store.submit()
  f.store.depart(); await f.store.load('7', '9'); f.store.beginEdit(); f.store.edit('notes', 'New draft')
  reply.resolve({ kind, deadline: stamp(60), message: 'Old error', errors: { notes: 'Old error' } })
  assert.equal((await pending).kind, 'cancelled')
  assert.equal(f.store.getSnapshot().record.id, 9)
  assert.equal(f.store.getSnapshot().draft.notes, 'New draft')
  assert.equal(f.session.getSnapshot().expires_at, stamp())
  f.store.dispose()
})
test('mismatched successful identity is rejected before session-deadline attachment', async () => {
  const f = await loaded('record', { getService: async () => success({ vehicle_id: 999 }, stamp(60)) })
  assert.equal(f.store.getSnapshot().record, null)
  assert.equal(f.session.getSnapshot().expires_at, stamp(30))
  f.store.dispose()
})
