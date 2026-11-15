import assert from 'node:assert/strict'
import test from 'node:test'
import { createSessionStore } from '../src/sessionState.js'
import { createVehicleDetailStore, vehicleReloadWarning } from '../src/vehicleDetailState.js'
import { prepareVehiclePatch } from '../src/vehicleValidation.js'

const now = Date.parse('2026-11-14T12:00:00Z')
const minute = 60000
const timestamp = (time) => new Date(time).toISOString()
const vehicle = {
  id: 7, year: 2020, make: 'Honda', model: 'Synthetic', vehicle_type: 'Car', engine: null,
  mileage: '1000.0', operating_hours: '10.0', readings_updated_at: '2026-11-14T11:00:00Z', created_at: '2026-11-13T11:00:00Z',
}
const sessionResult = (id = 1) => ({ kind: 'success', session: {
  user: { id, email: `synthetic-${id}@example.com`, created_at: '2026-11-13T11:00:00Z' },
  expires_at: timestamp(now + 30 * minute),
} })
const result = (id = 7, changes = {}, deadline = now + 31 * minute) => ({
  kind: 'success', vehicle: { ...vehicle, id, ...changes }, deadline: timestamp(deadline),
})
const correction = { kind: 'confirmation-required', fields: ['mileage'], currentReadings: { mileage: '1000.0' } }
function deferred() { let resolve; const promise = new Promise((done) => { resolve = done }); return { promise, resolve } }

async function fixture(overrides = {}, clock = () => now) {
  const calls = { session: 0, get: [], update: [] }
  const session = createSessionStore({
    getSession: async () => { calls.session += 1; return sessionResult() },
    loginAccount: async (details) => sessionResult(details?.id ?? 1),
    logoutAccount: async () => ({ kind: 'success' }),
  }, clock)
  await session.enter('garage', '/vehicles')
  const api = {
    getVehicle: async (...args) => {
      calls.get.push(args)
      return overrides.getVehicle ? overrides.getVehicle(...args) : result(Number(args[0]))
    },
    updateVehicle: async (...args) => {
      calls.update.push(args)
      if (overrides.updateVehicle) return overrides.updateVehicle(...args)
      const fields = prepareVehiclePatch(args[1], args[2], args[3]).details
      delete fields.reading_confirmation
      return result(Number(args[0]), fields)
    },
  }
  const detail = createVehicleDetailStore(session, api, clock)
  return { detail, session, calls }
}

async function editing(overrides, clock) {
  const f = await fixture(overrides, clock)
  await f.detail.load('7')
  assert.equal(f.detail.beginEdit(), true)
  return f
}

test('page effect cleanup and replay cancel the first load without disposing the mounted resource', async () => {
  const first = deferred()
  let requests = 0
  const { detail, calls } = await fixture({ getVehicle: async () => ++requests === 1 ? first.promise : result(7) })
  const stale = detail.load('7')
  detail.depart()
  const fresh = detail.load('7')
  await fresh
  first.resolve(result(7, { model: 'Obsolete effect' }, now + 60 * minute))
  assert.equal((await stale).kind, 'cancelled')
  assert.equal(detail.getSnapshot().vehicle.model, 'Synthetic')
  assert.equal(calls.get.length, 2)
  detail.dispose()
})

test('a replacement mounted store never receives a disposed store load or confirmation', async () => {
  const reply = deferred()
  const f = await fixture({ getVehicle: () => reply.promise })
  const old = f.detail.load('7')
  f.detail.dispose()
  const replacement = createVehicleDetailStore(f.session, {
    getVehicle: async () => result(8), updateVehicle: async () => correction,
  }, () => now)
  await replacement.load('8')
  reply.resolve(result(7, {}, now + 60 * minute))
  assert.equal((await old).kind, 'cancelled')
  assert.equal(f.detail.getSnapshot().vehicle, null)
  assert.equal(replacement.getSnapshot().vehicle.id, 8)
  assert.equal(replacement.getSnapshot().confirmation, null)
  assert.equal(f.session.getSnapshot().expires_at, timestamp(now + 31 * minute))
  replacement.dispose()
})

test('load tracks route and authentication generation while committed and draft remain separate', async () => {
  const { detail, session, calls } = await fixture()
  const observed = []
  const stop = detail.subscribe(() => observed.push(detail.getSnapshot().status))
  await detail.load('7')
  assert.equal(detail.getSnapshot().vehicleId, '7')
  assert.equal(detail.getSnapshot().authenticationGeneration, session.getSnapshot().generation)
  assert.equal(detail.getSnapshot().draft.year, '2020')
  detail.beginEdit()
  detail.edit('model', 'Unsaved')
  assert.equal(detail.getSnapshot().vehicle.model, 'Synthetic')
  assert.equal(detail.getSnapshot().draft.model, 'Unsaved')
  detail.cancelEdit()
  assert.equal(detail.getSnapshot().draft.model, 'Synthetic')
  assert.equal(calls.get.length, 1)
  assert.ok(observed.includes('loading') && observed.includes('ready'))
  stop()
  detail.dispose()
})

test('Save sends the separate current record/draft and replaces them with the accepted committed result', async () => {
  const { detail, session, calls } = await editing()
  detail.edit('model', 'Changed')
  const saved = await detail.submit()
  assert.equal(saved.kind, 'success')
  assert.equal(detail.getSnapshot().vehicle.model, 'Changed')
  assert.equal(detail.getSnapshot().draft.model, 'Changed')
  assert.equal(detail.getSnapshot().editing, false)
  assert.equal(calls.update[0][0], '7')
  assert.equal(calls.update[0][1].model, 'Synthetic')
  assert.equal(calls.update[0][2].model, 'Changed')
  assert.equal(calls.update[0][3], undefined)
  assert.equal(session.getSnapshot().expires_at, timestamp(now + 31 * minute))
  assert.equal(calls.session, 1)
})

test('invalid and unchanged drafts do not call the PATCH helper', async () => {
  const { detail, calls } = await editing()
  assert.equal((await detail.submit()).kind, 'unchanged')
  detail.edit('make', '')
  assert.equal((await detail.submit()).kind, 'invalid')
  assert.ok(detail.getSnapshot().errors.make)
  detail.edit('make', 'Honda')
  assert.equal(detail.getSnapshot().errors.make, undefined)
  assert.equal(calls.update.length, 0)
})

test('synchronous in-flight protection blocks repeated Save, Confirm and edits before React rerenders', async () => {
  const reply = deferred()
  const { detail, calls } = await editing({ updateVehicle: () => reply.promise })
  detail.edit('model', 'Changed')
  const first = detail.submit()
  assert.equal(detail.getSnapshot().pending, true)
  assert.equal((await detail.submit()).kind, 'cancelled')
  assert.equal((await detail.confirm()).kind, 'cancelled')
  assert.equal(detail.edit('model', 'Late edit'), false)
  assert.equal(calls.update.length, 1)
  reply.resolve(result(7, { model: 'Changed' }))
  await first
  assert.equal(detail.getSnapshot().pending, false)
})

test('first 409 preserves the draft and requires an explicit confirmation action', async () => {
  let requests = 0
  const { detail, calls } = await editing({ updateVehicle: async () => ++requests === 1 ? correction : result(7, { mileage: '900.0' }) })
  detail.edit('mileage', '900')
  await detail.submit()
  assert.equal(detail.getSnapshot().status, 'confirmation-required')
  assert.equal(detail.getSnapshot().draft.mileage, '900')
  assert.equal(detail.getSnapshot().vehicle.mileage, '1000.0')
  assert.deepEqual(detail.getSnapshot().confirmation.currentReadings, { mileage: '1000.0' })
  assert.equal((await detail.submit()).kind, 'cancelled')
  assert.equal(calls.update.length, 1)
  await detail.confirm()
  assert.equal(calls.update.length, 2)
  assert.deepEqual(calls.update[1][3], { mileage: '1000.0' })
  assert.equal(detail.getSnapshot().vehicle.mileage, '900.0')
  assert.equal(detail.getSnapshot().confirmation, null)
})

test('editing any proposed business value invalidates confirmation without replay', async () => {
  const { detail, calls } = await editing({ updateVehicle: async () => correction })
  detail.edit('mileage', '900')
  await detail.submit()
  detail.edit('model', 'Different proposal')
  assert.equal(detail.getSnapshot().confirmation, null)
  assert.equal((await detail.confirm()).kind, 'cancelled')
  assert.equal(calls.update.length, 1)
  assert.equal(detail.getSnapshot().draft.mileage, '900')
})

test('canceling confirmation retains the draft and sends no request', async () => {
  const { detail, calls } = await editing({ updateVehicle: async () => correction })
  detail.edit('mileage', '900')
  await detail.submit()
  detail.cancelConfirmation()
  assert.equal(detail.getSnapshot().confirmation, null)
  assert.equal(detail.getSnapshot().draft.mileage, '900')
  assert.equal(detail.getSnapshot().editing, true)
  assert.equal(calls.update.length, 1)
})

test('both reading corrections use the server snapshot only after explicit confirmation', async () => {
  let requests = 0
  const { detail, calls } = await editing({ updateVehicle: async () => ++requests === 1 ? {
    kind: 'confirmation-required', fields: ['mileage', 'operating_hours'], currentReadings: { mileage: '1200.0', operating_hours: '11.0' },
  } : result(7, { mileage: null, operating_hours: '9.0' }) })
  detail.edit('mileage', '')
  detail.edit('operating_hours', '9')
  await detail.submit()
  assert.deepEqual(detail.getSnapshot().confirmation.fields, ['mileage', 'operating_hours'])
  await detail.confirm()
  assert.deepEqual(calls.update[1][3], { mileage: '1200.0', operating_hours: '11.0' })
  assert.equal(detail.getSnapshot().vehicle.mileage, null)
})

test('second 409 requires reload/review and cannot be bypassed by editing or pressing Save', async () => {
  const { detail, calls } = await editing({ updateVehicle: async () => correction })
  detail.edit('mileage', '900')
  await detail.submit()
  await detail.confirm()
  assert.equal(detail.getSnapshot().status, 'reload-required')
  assert.equal(detail.getSnapshot().reloadRequired, true)
  assert.equal(detail.getSnapshot().confirmation, null)
  detail.edit('model', 'Another proposal')
  await detail.submit()
  await detail.confirm()
  assert.equal(calls.update.length, 2)
  assert.equal(calls.get.length, 1)
})

test('empty-fields stale confirmation requires deliberate reload and preserves the draft until then', async () => {
  const { detail, calls } = await editing({ updateVehicle: async () => ({ kind: 'reload-required', fields: [], currentReadings: {}, message: 'Reload and review.' }) })
  detail.edit('mileage', '900')
  await detail.submit()
  assert.equal(detail.getSnapshot().reloadRequired, true)
  assert.equal(detail.getSnapshot().draft.mileage, '900')
  assert.equal((await detail.reload()).kind, 'cancelled')
  assert.equal(detail.requestReload(), true)
  assert.equal(detail.getSnapshot().message, vehicleReloadWarning)
  assert.equal(detail.getSnapshot().draft.mileage, '900')
  detail.cancelReload()
  assert.equal(detail.getSnapshot().draft.mileage, '900')
  detail.requestReload()
  await detail.reload()
  assert.equal(detail.getSnapshot().draft.mileage, '1000.0')
  assert.equal(detail.getSnapshot().confirmation, null)
  assert.equal(detail.getSnapshot().editing, false)
  assert.equal(detail.getSnapshot().reloadRequired, false)
  assert.equal(calls.get.length, 2)
  assert.equal(calls.update.length, 1)
})

for (const kind of ['invalid', 'forbidden', 'unavailable', 'network', 'unexpected', 'uncertain']) {
  test(`correctable ${kind} failure retains draft, and uncertain outcomes demand inspection`, async () => {
    const { detail, session, calls } = await editing({ updateVehicle: async () => ({ kind, errors: kind === 'invalid' ? { model: 'Enter a valid value.' } : {}, message: 'Safe feedback' }) })
    const deadline = session.getSnapshot().expires_at
    detail.edit('model', 'Unsaved')
    await detail.submit()
    assert.equal(detail.getSnapshot().draft.model, 'Unsaved')
    assert.equal(detail.getSnapshot().vehicle.model, 'Synthetic')
    assert.equal(detail.getSnapshot().pending, false)
    assert.equal(session.getSnapshot().expires_at, deadline)
    const uncertain = ['unavailable', 'network', 'unexpected', 'uncertain'].includes(kind)
    assert.equal(detail.getSnapshot().reloadRequired, uncertain)
    if (uncertain) {
      await detail.submit()
      assert.equal(calls.update.length, 1)
    }
  })
}

test('load unavailable/not-found states have no cached profile and support deliberate retry', async () => {
  let calls = 0
  const { detail } = await fixture({ getVehicle: async () => ++calls === 1 ? { kind: 'unavailable', message: 'Unavailable.' } : result() })
  await detail.load('7')
  assert.equal(detail.getSnapshot().vehicle, null)
  assert.equal(detail.getSnapshot().status, 'unavailable')
  await detail.load('7')
  assert.equal(detail.getSnapshot().vehicle.id, 7)
  assert.equal(calls, 2)
  const missing = await fixture({ getVehicle: async () => ({ kind: 'not-found', message: 'Vehicle not found.' }) })
  await missing.detail.load('7')
  assert.equal(missing.detail.getSnapshot().status, 'not-found')
  assert.equal(missing.detail.getSnapshot().vehicle, null)
})

for (const kind of ['guest', 'authentication-unavailable']) {
  test(`${kind} immediately gates and clears record, draft and confirmation`, async () => {
    const { detail, session } = await editing({ updateVehicle: async () => ({ kind }) })
    detail.edit('model', 'Unsaved')
    await detail.submit()
    assert.equal(detail.getSnapshot().vehicle, null)
    assert.deepEqual(detail.getSnapshot().draft, {})
    assert.equal(detail.getSnapshot().confirmation, null)
    assert.equal(detail.getSnapshot().pending, false)
    assert.equal(session.getSnapshot().user, null)
  })
}

const actions = ['other-id', 'same-account-login', 'other-account-login', 'logout', 'revalidation', 'hidden', 'session-departure', 'detail-departure', 'dispose']
for (const operation of ['get', 'patch', '409']) {
  for (const action of actions) {
    test(`late ${operation} cannot restore private state or a deadline after ${action}`, async () => {
      const reply = deferred()
      let count = 0
      const f = await fixture({
        getVehicle: async (id) => operation === 'get' && ++count === 1 ? reply.promise : result(Number(id), {}, now + 32 * minute),
        updateVehicle: () => reply.promise,
      })
      let pending
      if (operation === 'get') pending = f.detail.load('7')
      else {
        await f.detail.load('7')
        f.detail.beginEdit()
        f.detail.edit('mileage', '900')
        pending = f.detail.submit()
      }
      if (action === 'other-id') await f.detail.load('8')
      else if (action === 'same-account-login') await f.session.login({ id: 1 })
      else if (action === 'other-account-login') await f.session.login({ id: 2 })
      else if (action === 'logout') await f.session.logout()
      else if (action === 'revalidation') await f.session.recheck()
      else if (action === 'hidden') f.session.hide()
      else if (action === 'session-departure') f.session.depart()
      else if (action === 'detail-departure') f.detail.depart()
      else f.detail.dispose()
      const deadline = f.session.getSnapshot().expires_at
      reply.resolve(operation === '409' ? correction : result(7, { model: 'Stale private data' }, now + 120 * minute))
      assert.equal((await pending).kind, 'cancelled')
      assert.equal(f.session.getSnapshot().expires_at, deadline)
      assert.equal(f.detail.getSnapshot().pending, false)
      assert.equal(f.detail.getSnapshot().confirmation, null)
      if (action === 'other-id') assert.equal(f.detail.getSnapshot().vehicle.id, 8)
      else {
        assert.equal(f.detail.getSnapshot().vehicle, null)
        assert.deepEqual(f.detail.getSnapshot().draft, {})
      }
    })
  }
}

test('a superseded load of the same ID cannot overwrite its newer result', async () => {
  const old = deferred()
  let count = 0
  const { detail } = await fixture({ getVehicle: async () => ++count === 1 ? old.promise : result(7, { model: 'New response' }, now + 32 * minute) })
  const pending = detail.load('7')
  await detail.load('7')
  old.resolve(result(7, { model: 'Old response' }, now + 90 * minute))
  assert.equal((await pending).kind, 'cancelled')
  assert.equal(detail.getSnapshot().vehicle.model, 'New response')
})

for (const incoming of [null, 'malformed', '2026-11-14T12:30:00', timestamp(now + 29 * minute), timestamp(now - 1)]) {
  test('bad or older detail metadata cannot replace a newer deadline or clear valid identity', async () => {
    const { detail, session } = await editing({ updateVehicle: async () => ({ ...result(7, { model: 'Rejected response' }), deadline: incoming }) })
    const deadline = session.getSnapshot().expires_at
    detail.edit('model', 'Unsaved')
    await detail.submit()
    assert.equal(session.getSnapshot().expires_at, deadline)
    assert.equal(session.getSnapshot().user.id, 1)
    assert.equal(detail.getSnapshot().vehicle.model, 'Synthetic')
    assert.equal(detail.getSnapshot().draft.model, 'Unsaved')
    assert.equal(detail.getSnapshot().reloadRequired, true)
  })
}

test('equal accepted deadline preserves its original representation; newer deadline needs no session request', async () => {
  let requests = 0
  const { detail, session, calls } = await editing({ updateVehicle: async () => ++requests === 1
    ? { ...result(7, { model: 'First' }), deadline: '2026-11-14T12:31:00+00:00' }
    : result(7, { model: 'Second' }, now + 40 * minute) })
  const before = session.getSnapshot().expires_at
  detail.edit('model', 'First')
  await detail.submit()
  assert.equal(session.getSnapshot().expires_at, before)
  detail.beginEdit()
  detail.edit('model', 'Second')
  await detail.submit()
  assert.equal(session.getSnapshot().expires_at, timestamp(now + 40 * minute))
  assert.equal(calls.session, 1)
})

for (const offset of [0, 5 * minute, -5 * minute]) {
  test(`local deadline equality clears identity and all detail state with device offset ${offset}`, async (t) => {
    t.mock.timers.enable({ apis: ['Date', 'setTimeout'], now: now + offset })
    const reply = deferred()
    const { detail, session, calls } = await editing({ updateVehicle: () => reply.promise }, Date.now)
    detail.edit('model', 'Unsaved')
    const pending = detail.submit()
    const stop = session.watchExpiry()
    t.after(stop)
    t.mock.timers.tick(31 * minute - offset)
    assert.equal(session.getSnapshot().user, null)
    assert.equal(detail.getSnapshot().vehicle, null)
    assert.deepEqual(detail.getSnapshot().draft, {})
    reply.resolve(result(7, { model: 'Too late' }, now + 8 * 60 * minute))
    assert.equal((await pending).kind, 'cancelled')
    t.mock.timers.tick(8 * 60 * minute)
    assert.equal(calls.session, 1)
    assert.equal(calls.get.length, 1)
    assert.equal(calls.update.length, 1)
  })
}

test('a delayed expiry timer still cannot let a late PATCH restore identity', async () => {
  let clock = now
  const reply = deferred()
  const { detail, session, calls } = await editing({ updateVehicle: () => reply.promise }, () => clock)
  detail.edit('model', 'Unsaved')
  const pending = detail.submit()
  clock = now + 31 * minute
  reply.resolve(result(7, { model: 'Too late' }, now + 90 * minute))
  await pending
  assert.equal(session.getSnapshot().user, null)
  assert.equal(detail.getSnapshot().vehicle, null)
  assert.equal(calls.session, 1)
})

test('expired-before-start handling uses the existing local check without a data/session request', async () => {
  let clock = now
  const { detail, session, calls } = await fixture({}, () => clock)
  clock = now + 30 * minute
  await detail.load('7')
  assert.equal(calls.get.length, 0)
  assert.equal(calls.session, 1)
  assert.equal(session.getSnapshot().user, null)
  assert.equal(detail.getSnapshot().vehicle, null)
})

test('visibility return may validate deliberately but never automatically reloads private detail', async () => {
  const { detail, session, calls } = await editing()
  detail.edit('model', 'Unsaved')
  session.hide()
  assert.deepEqual(detail.getSnapshot().draft, {})
  await session.resume()
  assert.equal(calls.session, 2)
  assert.equal(calls.get.length, 1)
  assert.equal(detail.getSnapshot().vehicle, null)
  await detail.load('7')
  assert.equal(calls.get.length, 2)
})

test('wrong-ID or malformed API success cannot replace committed detail or a session deadline', async () => {
  const { detail, session } = await editing({ updateVehicle: async () => result(8, { model: 'Wrong vehicle' }, now + 60 * minute) })
  const deadline = session.getSnapshot().expires_at
  detail.edit('model', 'Unsaved')
  await detail.submit()
  assert.equal(detail.getSnapshot().vehicle.id, 7)
  assert.equal(detail.getSnapshot().draft.model, 'Unsaved')
  assert.equal(session.getSnapshot().expires_at, deadline)
})

test('invalid IDs and permanently disposed stores never issue data requests', async () => {
  const { detail, calls } = await fixture()
  await detail.load('01')
  assert.equal(calls.get.length, 0)
  assert.equal(detail.getSnapshot().vehicle, null)
  detail.dispose()
  detail.dispose()
  await detail.load('7')
  await detail.submit()
  assert.equal(calls.get.length, 0)
  assert.equal(detail.getSnapshot().vehicle, null)
})
