import assert from 'node:assert/strict'
import test from 'node:test'
import { getVehicle, updateVehicle, uncertainVehicleUpdate } from '../src/api.js'
import {
  isVehicleId, prepareVehiclePatch, vehicleDraft, vehicleIdMessage,
} from '../src/vehicleValidation.js'

const deadline = '2026-11-14T12:30:00Z'
const vehicle = {
  id: 7, year: 2020, make: 'Honda', model: 'Synthetic', vehicle_type: 'Car', engine: null,
  mileage: '1000.0', operating_hours: '10.0', readings_updated_at: '2026-11-14T11:00:00Z', created_at: '2026-11-13T11:00:00Z',
}
const response = (status, body, expires = deadline) => new Response(JSON.stringify(body), {
  status, headers: { 'Content-Type': 'application/json', ...(expires === null ? {} : { 'X-GarageGuide-Session-Expires-At': expires }) },
})
const update = (values = { model: 'Updated' }, confirmation, signal) => updateVehicle('7', vehicle, values, confirmation, signal)
const fixedError = (loc, msg, type = 'value_error') => ({ detail: [{ loc, msg, type }] })

for (const id of ['1', '7', '2147483647']) {
  test(`canonical ID ${id} builds a relative GET and requires its exact public identity`, async (t) => {
    const fetch = t.mock.method(globalThis, 'fetch', async (url, options) => {
      assert.equal(url, `/api/vehicles/${id}`)
      assert.equal(options.method, 'GET')
      assert.equal(options.credentials, 'same-origin')
      assert.deepEqual(options.headers, { Accept: 'application/json' })
      assert.equal(options.body, undefined)
      return response(200, { ...vehicle, id: Number(id) })
    })
    assert.equal(isVehicleId(id), true)
    assert.equal((await getVehicle(id)).kind, 'success')
    assert.equal(fetch.mock.callCount(), 1)
  })
}

const invalidIds = ['', '0', '00', '01', '+1', '-1', '-0', '1.0', '1e1', ' 1', '1 ', '1\n', '1\r\n', '\t1', '1\u00a0', '\u0661', '\uff11', '2147483648', '99999999999', '%31', '1/2', '1?token=private', null, undefined, 1, 1.0, true, false, 1n, {}, []]
for (const [index, id] of invalidIds.entries()) {
  test(`noncanonical ID case ${index} cannot reach fetch through either helper`, async (t) => {
    const fetch = t.mock.method(globalThis, 'fetch', () => assert.fail('Invalid ID reached fetch'))
    assert.equal(isVehicleId(id), false)
    for (const result of [await getVehicle(id), await updateVehicle(id, vehicle, { model: 'Updated' })]) {
      assert.equal(result.kind, 'invalid')
      assert.deepEqual(result.errors, { vehicle_id: vehicleIdMessage })
    }
    assert.equal(fetch.mock.callCount(), 0)
  })
}

test('PATCH sends only normalized changed values with JSON/CSRF and same-origin credentials', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, '/api/vehicles/7')
    assert.equal(options.method, 'PATCH')
    assert.equal(options.credentials, 'same-origin')
    assert.deepEqual(options.headers, { Accept: 'application/json', 'Content-Type': 'application/json', 'X-GarageGuide-CSRF': '1' })
    assert.deepEqual(JSON.parse(options.body), { model: 'Changed', mileage: '900.0', reading_confirmation: { mileage: '1000.0' } })
    return response(200, { ...vehicle, model: 'Changed', mileage: '900.0' })
  })
  const result = await update({ ...vehicleDraft(vehicle), model: ' Changed ', mileage: ' 0900 ' }, { mileage: '01000' })
  assert.equal(result.kind, 'success')
  assert.equal(result.vehicle.mileage, '900.0')
  assert.equal(fetch.mock.callCount(), 1)
})

test('untouched fields and unchanged legacy years never become PATCH fields', () => {
  for (const year of [1, 1885, 32767]) {
    const current = { ...vehicle, year }
    const prepared = prepareVehiclePatch(current, { ...vehicleDraft(current), model: 'Changed' })
    assert.equal(prepared.invalid, false)
    assert.deepEqual(prepared.details, { model: 'Changed' })
  }
  assert.deepEqual(prepareVehiclePatch(vehicle, { model: 'Changed' }).details, { model: 'Changed' })
})

for (const [name, value, expected] of [
  ['engine', '', null], ['engine', '  ', null], ['engine', null, null],
  ['mileage', '', null], ['operating_hours', ' \t ', null], ['mileage', null, null],
  ['mileage', '000.0', '0.0'], ['mileage', '99999999999.9', '99999999999.9'],
  ['operating_hours', '00012.3', '12.3'],
]) {
  test(`changed optional ${name} preserves the reviewed null/decimal value ${String(value)}`, () => {
    const current = name === 'engine' ? { ...vehicle, engine: 'V8' } : vehicle
    assert.deepEqual(prepareVehiclePatch(current, { [name]: value }).details, { [name]: expected })
  })
}

test('unknown readings remain null and confirmed zero remains a distinct reading', () => {
  const current = { ...vehicle, mileage: null, operating_hours: '0.0' }
  assert.equal(prepareVehiclePatch(current, vehicleDraft(current)).unchanged, true)
  assert.deepEqual(prepareVehiclePatch(current, { mileage: '0' }).details, { mileage: '0.0' })
  assert.deepEqual(prepareVehiclePatch(current, { operating_hours: '' }).details, { operating_hours: null })
})

for (const values of [{}, vehicleDraft(vehicle), { make: ' Honda ' }, { mileage: '01000' }]) {
  test('an empty or normalized-equal draft cannot send an empty PATCH', async (t) => {
    const fetch = t.mock.method(globalThis, 'fetch', () => assert.fail('Empty PATCH reached fetch'))
    assert.equal((await update(values)).kind, 'unchanged')
    assert.equal(fetch.mock.callCount(), 0)
  })
}

for (const [index, values] of [
  { make: null }, { model: null }, { year: null }, { vehicle_type: null }, { mileage: undefined },
  { mileage: 0 }, { mileage: '1.00' }, { mileage: '1e2' }, { mileage: '-0.0' },
  { mileage: '100000000000.0' }, { operating_hours: '\u0661' }, { year: true }, { year: '2020.0' },
  { year: 1885 }, { model: 'bad\0text' }, { engine: 'bad\ud800' }, { owner_id: 1 },
  { user_id: 1 }, { id: 1 }, { reading_confirmation: { mileage: '1000' } },
].entries()) {
  test(`invalid PATCH draft case ${index} is stopped before fetch`, async (t) => {
    const fetch = t.mock.method(globalThis, 'fetch', () => assert.fail('Invalid draft reached fetch'))
    assert.equal((await update(values)).kind, 'invalid')
    assert.equal(fetch.mock.callCount(), 0)
  })
}

for (const confirmation of [null, [], { owner_id: '1' }, { mileage: null }, { mileage: 1000 }, { operating_hours: '10' }]) {
  test('confirmation metadata must be non-null reading strings for genuinely changed fields', async (t) => {
    t.mock.method(globalThis, 'fetch', () => assert.fail('Invalid confirmation reached fetch'))
    assert.equal((await update({ mileage: '900' }, confirmation)).kind, 'invalid')
  })
}

test('a mismatched current record requires reload without sending a PATCH', async (t) => {
  t.mock.method(globalThis, 'fetch', () => assert.fail('Wrong vehicle reached fetch'))
  assert.equal((await updateVehicle('8', vehicle, { model: 'Changed' })).kind, 'reload-required')
})

for (const [index, body] of [
  { vehicles: [vehicle] }, { ...vehicle, id: 8 }, { ...vehicle, user_id: 1 },
  { ...vehicle, mileage: 0 }, { ...vehicle, mileage: '1.00' }, { ...vehicle, mileage: '1.0\n' },
  { ...vehicle, engine: '' }, { ...vehicle, year: 0 }, { ...vehicle, make: ' Honda ' },
  { ...vehicle, model: 'bad\ud800' }, { ...vehicle, created_at: '2026-11-14' },
  { ...vehicle, readings_updated_at: '2026-02-30T12:00:00Z' }, null, [], {},
].entries()) {
  test(`mismatched public profile case ${index} is never accepted as success`, async (t) => {
    t.mock.method(globalThis, 'fetch', async () => response(200, body))
    assert.equal((await getVehicle('7')).kind, 'unexpected')
    const result = await update()
    assert.equal(result.kind, 'uncertain')
    assert.equal(result.message, uncertainVehicleUpdate)
  })
}

for (const expires of [null, 'garbage', '2026-11-14T12:30:00', '2026-02-30T12:30:00Z']) {
  test('missing or malformed deadline metadata rejects the response without inventing a deadline', async (t) => {
    t.mock.method(globalThis, 'fetch', async () => response(200, vehicle, expires))
    assert.equal((await getVehicle('7')).kind, 'unexpected')
    assert.equal((await update()).kind, 'uncertain')
  })
}

test('detail and update accept stored legacy years and reject creation/list status shapes', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch', async () => response(200, { ...vehicle, year: 1 }))
  assert.equal((await getVehicle('7')).vehicle.year, 1)
  fetch.mock.mockImplementation(async () => response(201, vehicle))
  assert.equal((await getVehicle('7')).kind, 'unexpected')
  assert.equal((await update()).kind, 'uncertain')
})

test('only the exact requested reading fields and canonical current readings are accepted for 409', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch', async () => response(409, {
    detail: 'Reading changes require confirmation.', fields: ['mileage'], current_readings: { mileage: '1000.0' },
  }))
  const first = await update({ mileage: '900' })
  assert.equal(first.kind, 'confirmation-required')
  assert.deepEqual(first.currentReadings, { mileage: '1000.0' })
  assert.equal(first.deadline, undefined)
  fetch.mock.mockImplementation(async () => response(409, {
    detail: 'Reading changes require confirmation.', fields: [], current_readings: {},
  }))
  assert.equal((await update({ mileage: '900' }, { mileage: '1000' })).kind, 'reload-required')
  assert.equal(fetch.mock.callCount(), 2)
})

for (const [index, body] of [
  { detail: 'private', fields: ['mileage'], current_readings: { mileage: '1000.0' } },
  { detail: 'Reading changes require confirmation.', fields: ['owner_id'], current_readings: { owner_id: '1.0' } },
  { detail: 'Reading changes require confirmation.', fields: ['operating_hours'], current_readings: { operating_hours: '10.0' } },
  { detail: 'Reading changes require confirmation.', fields: ['mileage', 'mileage'], current_readings: { mileage: '1000.0' } },
  { detail: 'Reading changes require confirmation.', fields: ['mileage'], current_readings: { mileage: null } },
  { detail: 'Reading changes require confirmation.', fields: ['mileage'], current_readings: { mileage: 1000 } },
  { detail: 'Reading changes require confirmation.', fields: ['mileage'], current_readings: { mileage: '01000.0' } },
  { detail: 'Reading changes require confirmation.', fields: ['mileage'], current_readings: { mileage: '1000.0\n' } },
  { detail: 'Reading changes require confirmation.', fields: ['mileage'], current_readings: { mileage: '800.0' } },
  { detail: 'Reading changes require confirmation.', fields: ['mileage'], current_readings: { mileage: '1000.0', other: 'private' } },
  { detail: 'Reading changes require confirmation.', fields: [], current_readings: {} },
  { detail: 'Reading changes require confirmation.', fields: [], current_readings: [], other: 'private' },
].entries()) {
  test(`untrusted or mismatched 409 case ${index} becomes safe uncertainty without replay`, async (t) => {
    const fetch = t.mock.method(globalThis, 'fetch', async () => response(409, body))
    const result = await update({ mileage: '900' })
    assert.equal(result.kind, 'uncertain')
    assert.equal(result.message, uncertainVehicleUpdate)
    assert.equal(fetch.mock.callCount(), 1)
  })
}

for (const [status, detail, kind] of [
  [404, 'Vehicle not found.', 'not-found'], [401, 'Not authenticated.', 'guest'],
  [403, 'Request not allowed.', 'forbidden'],
  [503, 'Authentication unavailable. Please try again.', 'authentication-unavailable'],
  [503, 'Vehicles unavailable. Please try again.', 'unavailable'],
]) {
  test(`fixed ${status} ${kind} is recognized without accepting error deadline metadata`, async (t) => {
    t.mock.method(globalThis, 'fetch', async () => response(status, { detail }, '2099-01-01T00:00:00Z'))
    for (const result of [await getVehicle('7'), await update()]) {
      assert.equal(result.kind, kind)
      assert.equal(result.deadline, undefined)
    }
  })
}

for (const body of [
  fixedError(['path', 'vehicle_id'], vehicleIdMessage),
  fixedError(['body'], 'Provide at least one editable vehicle field.'),
  fixedError(['body', 'make'], 'This field cannot be cleared.'),
  fixedError(['body', 'reading_confirmation'], 'Provide confirmation values only for supplied reading fields.'),
  fixedError(['body', 'mileage'], 'Enter a nonnegative decimal string with at most one decimal place, up to 99999999999.9.'),
]) {
  test('reviewed sanitized validation locations/messages are accepted', async (t) => {
    t.mock.method(globalThis, 'fetch', async () => response(422, body))
    assert.equal((await update()).kind, 'invalid')
  })
}

test('detail GET accepts only path-ID validation, never PATCH-only body errors', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch', async () => response(422, fixedError(['path', 'vehicle_id'], vehicleIdMessage)))
  assert.equal((await getVehicle('7')).kind, 'invalid')
  for (const body of [
    fixedError(['body'], 'Provide at least one editable vehicle field.'),
    fixedError(['body', 'make'], 'This field cannot be cleared.'),
    fixedError(['body', 'reading_confirmation'], 'Provide confirmation values only for supplied reading fields.'),
  ]) {
    fetch.mock.mockImplementation(async () => response(422, body))
    assert.equal((await getVehicle('7')).kind, 'unexpected')
  }
})

for (const body of [
  fixedError(['body', 'make'], 'private-server-value'),
  fixedError(['body', 'owner_id'], 'Enter a valid value.'),
  { detail: [{ loc: ['body'], msg: 'Enter a valid value.', type: 'value_error', input: 'private' }] },
  { detail: [], other: 'private' }, { detail: [] },
]) {
  test('raw or unapproved validation data cannot become UI feedback', async (t) => {
    t.mock.method(globalThis, 'fetch', async () => response(422, body))
    const result = await update()
    assert.equal(result.kind, 'uncertain')
    assert.equal(result.message, uncertainVehicleUpdate)
  })
}

test('generic 500 and invalid JSON are uncertain for PATCH without raw server text', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch', async () => response(500, { detail: 'Internal server error' }))
  assert.equal((await update()).message, uncertainVehicleUpdate)
  fetch.mock.mockImplementation(async () => new Response('private invalid JSON', { status: 200 }))
  assert.equal((await update()).message, uncertainVehicleUpdate)
  assert.equal((await getVehicle('7')).kind, 'unexpected')
})

test('network and unexpected failures never replay PATCH', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch', async () => { throw new TypeError('private-network-details') })
  const network = await update()
  assert.equal(network.kind, 'network')
  assert.equal(network.uncertain, true)
  assert.equal(network.message, uncertainVehicleUpdate)
  fetch.mock.mockImplementation(async () => { throw new Error('private-error') })
  assert.equal((await update()).kind, 'uncertain')
  assert.equal(fetch.mock.callCount(), 2)
})

test('PATCH times out once at ten seconds and releases its timer without retry', async (t) => {
  t.mock.timers.enable({ apis: ['setTimeout'] })
  const fetch = t.mock.method(globalThis, 'fetch', (url, { signal }) => new Promise((resolve, reject) => {
    signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })
  }))
  const pending = update()
  t.mock.timers.tick(9999)
  assert.equal(fetch.mock.calls[0].arguments[1].signal.aborted, false)
  t.mock.timers.tick(1)
  const result = await pending
  assert.equal(result.kind, 'network')
  assert.equal(result.message, uncertainVehicleUpdate)
  t.mock.timers.tick(100000)
  assert.equal(fetch.mock.callCount(), 1)
})

test('pre-aborted and subsequently aborted requests are cancelled without retry', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch', (url, { signal }) => new Promise((resolve, reject) => {
    signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })
  }))
  const before = new AbortController()
  before.abort()
  assert.equal((await getVehicle('7', before.signal)).kind, 'cancelled')
  assert.equal((await update({ model: 'Updated' }, undefined, before.signal)).kind, 'cancelled')
  assert.equal(fetch.mock.callCount(), 0)
  const controller = new AbortController()
  const pending = update({ model: 'Updated' }, undefined, controller.signal)
  controller.abort()
  assert.equal((await pending).kind, 'cancelled')
  assert.equal(fetch.mock.callCount(), 1)
})
