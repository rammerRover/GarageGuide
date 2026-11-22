import assert from 'node:assert/strict'
import test from 'node:test'
import { matchRoutes } from 'react-router-dom'
import { createMaintenanceSchedule, listMaintenanceSchedules, updateMaintenanceSchedule } from '../src/api.js'
import { createScheduleStore } from '../src/scheduleState.js'
import { duplicateScheduleMessage, prepareScheduleInput, scheduleDraft, scheduleFields } from '../src/scheduleValidation.js'
import { createSessionStore } from '../src/sessionState.js'
import { maintenanceSchedulesRoute, protectedRoutes } from '../src/vehicleRoutes.js'
import { deferred, now, publicSession, stamp } from './serviceFixtures.js'

const path = '/api/vehicles/7/maintenance-schedules'
const page = '/vehicles/7/maintenance-schedules'
const record = {
  id: 12, vehicle_id: 7, name: 'Oil change', interval_days: 30, baseline_date: '2020-01-01',
  interval_miles: null, baseline_mileage: null, interval_hours: null, baseline_hours: null,
  source_notes: null, created_at: stamp(-60),
}
const conflict = (matches, extras = {}) => ({ code: 'duplicate_schedule_name', detail: duplicateScheduleMessage, matches, ...extras })
const response = (body, status = 200) => new Response(JSON.stringify(body), {
  status, headers: { 'Content-Type': 'application/json', 'X-GarageGuide-Session-Expires-At': stamp(31) },
})
const duplicate = (matches) => ({ kind: 'duplicate', matches })
const success = (schedule) => ({ kind: 'success', schedule, deadline: stamp(32) })

test('protected navigation uses the same route for case, trailing slash, and decoded path variants', () => {
  for (const pathname of [page, page.toUpperCase() + '/', '/vehicles/%37/maint%65nance-schedules']) {
    const matched = matchRoutes(protectedRoutes, { pathname }).at(-1)
    assert.equal(matched.route, maintenanceSchedulesRoute)
    assert.equal(matched.params.vehicleId, '7')
  }
  assert.equal(matchRoutes(protectedRoutes, '/vehicles/7/maintenance-schedules-extra'), null)
})

test('combined pairs require complete baselines and preserve exact decimals and zero', () => {
  const draft = { ...scheduleDraft(record), interval_miles: '00012.5', interval_hours: '9', baseline_hours: '1.2' }
  assert.equal(prepareScheduleInput(draft).errors.baseline_mileage, 'Set both the mileage interval and its baseline, or clear both.')
  const prepared = prepareScheduleInput({ ...draft, baseline_mileage: '0' })
  assert.equal(prepared.invalid, false)
  assert.deepEqual(prepared.details, { ...recordFields(record), interval_miles: '12.5', baseline_mileage: '0.0',
    interval_hours: '9.0', baseline_hours: '1.2' })
  assert.equal(prepareScheduleInput({ ...draft, baseline_mileage: '0.0', interval_hours: '0' }).invalid, true)
})

function recordFields(schedule) {
  return Object.fromEntries(scheduleFields.map((field) => [field, schedule[field]]))
}

test('PATCH preserves untouched legacy notes and requires both fields when disabling a pair', () => {
  const stored = { ...record, interval_miles: '12.5', baseline_mileage: '0.0', source_notes: ' Historical notes ' }
  const draft = { ...scheduleDraft(stored), name: '  Check oil  ' }
  assert.deepEqual(prepareScheduleInput(draft, stored).details, { name: 'Check oil' })
  assert.equal(prepareScheduleInput({ ...draft, interval_miles: '' }, stored).invalid, true)
  assert.deepEqual(prepareScheduleInput({ ...draft, interval_miles: '', baseline_mileage: '' }, stored).details,
    { name: 'Check oil', interval_miles: null, baseline_mileage: null })
  assert.equal(prepareScheduleInput({ ...scheduleDraft(), name: 'New' }).invalid, true)
})

test('API uses scoped GET/POST/PATCH and existing mutation protection', async (t) => {
  const bodies = [response({ vehicle_id: 7, schedules: [record] }), response(record, 201), response(record)]
  const fetch = t.mock.method(globalThis, 'fetch', async () => bodies.shift())
  assert.deepEqual(await listMaintenanceSchedules('7'), { kind: 'success', schedules: [record], deadline: stamp(31) })
  assert.equal((await createMaintenanceSchedule('7', recordFields(record))).kind, 'success')
  const details = { source_notes: null, reviewed_duplicate_ids: [13] }
  assert.equal((await updateMaintenanceSchedule('7', '12', details)).kind, 'success')
  const calls = fetch.mock.calls.map((call) => call.arguments)
  assert.deepEqual(calls.map(([url, options]) => [url, options.method]), [[path, 'GET'], [path, 'POST'], [path + '/12', 'PATCH']])
  assert.ok(calls.every(([, options]) => options.credentials === 'same-origin'))
  assert.ok(calls.slice(1).every(([, options]) => options.headers['X-GarageGuide-CSRF'] === '1'))
  assert.deepEqual(JSON.parse(calls[2][1].body), details)
  assert.equal((await updateMaintenanceSchedule('7', null, details)).kind, 'invalid')
  assert.equal((await listMaintenanceSchedules('07')).kind, 'invalid')
  assert.equal(fetch.mock.callCount(), 3)
})

test('API only accepts correctly scoped unique 409 matches, including a fresh empty set', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch')
  const changes = { name: 'Oil change' }
  const other = { ...record, id: 13 }
  for (const matches of [[other], []]) {
    fetch.mock.mockImplementation(async () => response(conflict(matches), 409))
    assert.deepEqual((await updateMaintenanceSchedule('7', '12', changes)).matches, matches)
  }
  for (const body of [conflict([record]), conflict([{ ...other, vehicle_id: 8 }]), conflict([other, other]),
    conflict([other], { private: 'unexpected' })]) {
    fetch.mock.mockImplementation(async () => response(body, 409))
    assert.equal((await updateMaintenanceSchedule('7', '12', changes)).kind, 'uncertain')
  }
})

test('API accepts field-safe 422 errors and discards unrecognized messages', async (t) => {
  const entry = { loc: ['body', 'baseline_mileage'], type: 'value_error',
    msg: 'Set both the mileage interval and its baseline, or clear both.' }
  const fetch = t.mock.method(globalThis, 'fetch', async () => response({ detail: [entry] }, 422))
  assert.deepEqual((await updateMaintenanceSchedule('7', '12', { baseline_mileage: null })).errors,
    { baseline_mileage: entry.msg })
  fetch.mock.mockImplementation(async () => response({ detail: [{ ...entry, msg: 'Sensitive data' }] }, 422))
  const rejected = await updateMaintenanceSchedule('7', '12', { baseline_mileage: null })
  assert.equal(rejected.kind, 'uncertain')
  assert.ok(!rejected.message.includes('Sensitive data'))
})

async function fixture(overrides = {}, clock = () => now) {
  const bodies = []
  const session = createSessionStore({
    getSession: async () => publicSession(),
    loginAccount: async () => publicSession(), logoutAccount: async () => ({ kind: 'success' }),
  }, clock)
  await session.enter('schedule-key', page)
  const vehicle = { id: 7, mileage: '0.0', operating_hours: null }
  const store = createScheduleStore(session, {
    getVehicle: async () => ({ kind: 'success', vehicle, deadline: stamp(30) }),
    listMaintenanceSchedules: async () => ({ kind: 'success', schedules: [record], deadline: stamp(31) }),
    createMaintenanceSchedule: async (_, details) => { bodies.push(details); return success({ ...record, ...details, id: 15 }) },
    updateMaintenanceSchedule: async (_, id, details) => { bodies.push(details); return success({ ...record, ...details, id: Number(id) }) },
    ...overrides,
  }, clock)
  return { store, session, vehicle, bodies }
}

function fill(store, name = 'Oil change') {
  store.change('name', name)
  store.change('interval_days', '30')
  store.change('baseline_date', '2020-01-01')
}

test('current zero is only copied on request, unknown stays blank, and saving leaves vehicle readings intact', async () => {
  const { store, bodies, vehicle } = await fixture()
  await store.load('7')
  assert.equal(store.getSnapshot().draft.baseline_mileage, '')
  assert.equal(store.copyReading('baseline_hours'), false)
  assert.equal(store.getSnapshot().draft.baseline_hours, '')
  assert.equal(store.copyReading('baseline_mileage'), true)
  assert.equal(store.getSnapshot().draft.baseline_mileage, '0.0')
  fill(store, 'Separate work')
  store.change('interval_miles', '1000')
  await store.submit()
  assert.equal(bodies[0].baseline_mileage, '0.0')
  assert.equal(bodies[0].baseline_hours, null)
  assert.deepEqual(vehicle, { id: 7, mileage: '0.0', operating_hours: null })
  assert.equal(store.getSnapshot().schedules[1].name, 'Separate work')
  store.dispose()
})

test('only explicit separate save sends the currently displayed IDs, including a refreshed conflict', async () => {
  const bodies = []
  const newer = { ...record, id: 13 }
  const { store, session } = await fixture({
    createMaintenanceSchedule: async (_, details) => {
      bodies.push(details)
      if (bodies.length === 1) return { ...duplicate([record]), deadline: stamp(90) }
      if (bodies.length === 2) return duplicate([record, newer])
      return success({ ...record, id: 15 })
    },
  })
  await store.load('7')
  fill(store)
  await store.submit()
  assert.equal(session.getSnapshot().expires_at, stamp(31))
  assert.deepEqual(store.getSnapshot().review, [record])
  await store.submit()
  assert.equal(bodies.length, 1)
  const saving = store.saveSeparate()
  await store.saveSeparate()
  await saving
  assert.deepEqual(store.getSnapshot().review, [record, newer])
  assert.deepEqual(bodies[1].reviewed_duplicate_ids, [12])
  assert.equal(bodies.length, 2)
  await store.saveSeparate()
  assert.deepEqual(bodies[2].reviewed_duplicate_ids, [12, 13])
  assert.equal(store.getSnapshot().review, null)
  assert.equal(store.getSnapshot().message, 'Schedule created.')
  store.dispose()
})

test('draft changes clear review and opening a match switches to scoped PATCH', async () => {
  const { store, bodies } = await fixture({
    createMaintenanceSchedule: async () => duplicate([record]),
  })
  await store.load('7')
  fill(store)
  await store.submit()
  store.change('source_notes', 'Updated draft')
  assert.equal(store.getSnapshot().review, null)
  assert.equal(store.saveSeparate(), undefined)
  await store.submit()
  assert.equal(store.beginEdit(12), true)
  assert.equal(store.getSnapshot().draft.name, record.name)
  assert.equal(store.getSnapshot().review, null)
  store.change('source_notes', 'User-entered notes')
  await store.submit()
  assert.deepEqual(bodies, [{ source_notes: 'User-entered notes' }])
  assert.equal(store.getSnapshot().schedules[0].source_notes, 'User-entered notes')
  store.dispose()
})

test('when a fresh conflict is empty, another ordinary submission still needs a click', async () => {
  const bodies = []
  const { store } = await fixture({ createMaintenanceSchedule: async (_, details) => {
    bodies.push(details)
    return [duplicate([record]), duplicate([]), success({ ...record, id: 15 })][bodies.length - 1]
  } })
  await store.load('7')
  fill(store)
  await store.submit()
  await store.saveSeparate()
  assert.deepEqual(store.getSnapshot().review, [])
  assert.equal(store.saveSeparate(), undefined)
  assert.equal(bodies.length, 2)
  await store.submit()
  assert.equal(bodies.length, 3)
  assert.equal(bodies[2].reviewed_duplicate_ids, undefined)
  store.dispose()
})

test('uncertain save retains the draft and requires a successful reload and deliberate inspection', async () => {
  let reads = 0, writes = 0
  const { store } = await fixture({
    listMaintenanceSchedules: async () => ++reads === 2 ? { kind: 'unavailable' } :
      { kind: 'success', schedules: [record], deadline: stamp(31) },
    createMaintenanceSchedule: async () => { ++writes; return { kind: 'uncertain' } },
  })
  await store.load('7')
  fill(store)
  await store.submit()
  assert.equal(store.getSnapshot().draft.name, record.name)
  assert.equal(store.acknowledgeInspection(), false)
  await store.reload()
  assert.equal(store.acknowledgeInspection(), false)
  await store.submit()
  assert.equal(writes, 1)
  await store.reload()
  assert.equal(store.acknowledgeInspection(), true)
  assert.equal(writes, 1)
  store.dispose()
})

test('a stale vehicle load cannot start a schedule request or expose the vehicle', async () => {
  const profile = deferred()
  let lists = 0
  const { store, session, vehicle } = await fixture({
    getVehicle: () => profile.promise,
    listMaintenanceSchedules: async () => { lists++; return { kind: 'success', schedules: [record], deadline: stamp(90) } },
  })
  const pending = store.load('7')
  await session.enter('other-vehicle', '/vehicles/8')
  const deadline = session.getSnapshot().expires_at
  profile.resolve({ kind: 'success', vehicle, deadline: stamp(90) })
  assert.equal((await pending).kind, 'cancelled')
  assert.equal(lists, 0)
  assert.equal(store.getSnapshot().vehicle, null)
  assert.equal(session.getSnapshot().expires_at, deadline)
  store.dispose()
})

for (const exit of ['navigate', 'hidden', 'logout', 'same account sign-in', 'expired', 'pagehide']) {
  test(`a late save cannot restore schedules or extend the deadline after ${exit}`, async () => {
    let clock = now
    const reply = deferred()
    const { store, session } = await fixture({ createMaintenanceSchedule: () => reply.promise }, () => clock)
    await store.load('7')
    fill(store)
    const pending = store.submit()
    if (exit === 'navigate') await session.enter('elsewhere', '/vehicles')
    if (exit === 'hidden') session.hide()
    if (exit === 'logout') await session.logout()
    if (exit === 'same account sign-in') await session.login({})
    if (exit === 'expired') {
      clock = Date.parse(session.getSnapshot().expires_at)
      await session.authenticatedRequest(() => assert.fail('No request at local expiry'))
    }
    if (exit === 'pagehide') store.depart()
    const deadline = session.getSnapshot().expires_at
    reply.resolve({ ...success(record), deadline: stamp(90) })
    assert.equal((await pending).kind, 'cancelled')
    assert.equal(store.getSnapshot().vehicle, null)
    assert.deepEqual(store.getSnapshot().schedules, [])
    assert.equal(session.getSnapshot().expires_at, deadline)
    store.dispose()
  })
}
