import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createVehicle, listVehicles } from '../src/api.js'
import { parseSessionDeadline } from '../src/sessionDeadline.js'
import { isPublicVehicle, parseVehicleErrors, prepareVehicleInput } from '../src/vehicleValidation.js'

const deadline = '2026-11-13T12:30:00Z'
const body = { year: '2020', make: ' Honda ', model: 'Synthetic', vehicle_type: 'Custom', engine: '', mileage: '', operating_hours: '0' }
const vehicle = { id: 7, year: 2020, make: 'Honda', model: 'Synthetic', vehicle_type: 'Custom', engine: null,
  mileage: null, operating_hours: '0.0', readings_updated_at: '2026-11-13T12:00:00Z', created_at: '2026-11-13T12:00:00Z' }
const response = (status, data, expires = deadline) => new Response(JSON.stringify(data), {
  status, headers: { 'Content-Type': 'application/json', ...(expires === null ? {} : { 'X-GarageGuide-Session-Expires-At': expires }) },
})
function replaceFetch(t, fn) { t.mock.method(globalThis, 'fetch', fn) }

test('vehicle GET and POST use relative same-origin URLs and exact normalized JSON without ownership', async (t) => {
  let calls = 0
  replaceFetch(t, async (url, options) => {
    calls += 1
    assert.equal(url, '/api/vehicles')
    assert.equal(options.credentials, 'same-origin')
    assert.ok(options.signal instanceof AbortSignal)
    assert.equal(Object.hasOwn(options.headers, 'Origin'), false)
    if (options.method === 'GET') {
      assert.equal(Object.hasOwn(options, 'body'), false)
      assert.equal(Object.hasOwn(options.headers, 'X-GarageGuide-CSRF'), false)
      return response(200, { vehicles: [vehicle] })
    }
    assert.deepEqual(options.headers, { Accept: 'application/json', 'Content-Type': 'application/json', 'X-GarageGuide-CSRF': '1' })
    assert.deepEqual(JSON.parse(options.body), { year: 2020, make: 'Honda', model: 'Synthetic', vehicle_type: 'Custom', engine: null, mileage: null, operating_hours: '0.0' })
    return response(201, vehicle)
  })
  assert.deepEqual(await listVehicles(), { kind: 'success', vehicles: [vehicle], deadline })
  assert.deepEqual(await createVehicle(body), { kind: 'success', vehicle, deadline })
  assert.equal(calls, 2)
})

for (const [index, readings] of [
  { mileage: null, operating_hours: null }, { mileage: '0', operating_hours: null },
  { mileage: null, operating_hours: '0.0' }, { mileage: '99999999999.9', operating_hours: '00012.3' },
].entries()) {
  test(`readings preserve decimal strings and unknown versus zero case ${index}`, () => {
    const prepared = prepareVehicleInput({ ...body, ...readings })
    assert.equal(prepared.invalid, false)
    assert.equal(prepared.details.mileage, readings.mileage === '0' ? '0.0' : readings.mileage)
    assert.equal(prepared.details.operating_hours, readings.operating_hours === '00012.3' ? '12.3' : readings.operating_hours)
    assert.equal(typeof prepared.details.mileage === 'number', false)
  })
}

for (const [index, changes] of [
  { year: true }, { year: '1885' }, { year: '2020.0' }, { year: '2e3' }, { year: '' },
  { make: '' }, { model: '\u0000Synthetic' }, { engine: '\ud800' }, { vehicle_type: ' ' },
  { mileage: 0 }, { mileage: '0.00' }, { mileage: '-0.0' }, { mileage: '1e3' },
  { operating_hours: '100000000000.0' }, { operating_hours: '\u0661.0' },
  { user_id: 99 }, { owner_id: 99 }, { id: 7 },
].entries()) {
  test(`invalid creation values are rejected without network work case ${index}`, async (t) => {
    const fetch = t.mock.method(globalThis, 'fetch', async () => assert.fail('Invalid form must not be sent'))
    const result = await createVehicle({ ...body, ...changes })
    assert.equal(result.kind, 'invalid')
    assert.equal(fetch.mock.callCount(), 0)
  })
}

test('text normalization preserves case and Unicode; backend owns the current-year upper limit', () => {
  const prepared = prepareVehicleInput({ ...body, year: '2035', make: ' \u00c9xample \ud83d\udef5 ', engine: ' V8 ' })
  assert.equal(prepared.invalid, false)
  assert.equal(prepared.details.year, 2035)
  assert.equal(prepared.details.make, '\u00c9xample \ud83d\udef5')
  assert.equal(prepared.details.engine, 'V8')
  assert.equal(isPublicVehicle({ ...vehicle, year: 1 }), true)
})

for (const [index, value] of [null, '', 'garbage', '2026-11-13T12:30:00', '2026-02-29T12:00:00Z',
  '2026-04-31T12:00:00Z', '2026-11-13T24:00:00Z', '2026-11-13T12:30:00+24:00'].entries()) {
  test(`invalid or missing deadline rejected case ${index}`, async (t) => {
    assert.equal(parseSessionDeadline(value), null)
    replaceFetch(t, async () => response(201, vehicle, value))
    const result = await createVehicle(body)
    assert.equal(result.kind, 'uncertain')
    assert.match(result.message, /may have been created.*Check your garage/)
  })
}

test('valid aware deadline forms are parsed without inventing a deadline', () => {
  for (const value of [deadline, '2028-02-29T12:00:00.123456+00:00', '2026-11-13T07:30:00-05:00']) {
    assert.equal(parseSessionDeadline(value), value)
  }
})

for (const [index, changes] of [{ user_id: 99 }, { token: 'private-marker' }, { id: '7' }, { mileage: 0 },
  { operating_hours: '00.0' }, { mileage: '-1.0' }, { engine: '\0' }, { year: 0 }, { created_at: 'garbage' }].entries()) {
  test(`invalid public vehicle response is not retained case ${index}`, async (t) => {
    replaceFetch(t, async () => response(200, { vehicles: [{ ...vehicle, ...changes }] }))
    const result = await listVehicles()
    assert.equal(result.kind, 'unexpected')
    assert.equal(JSON.stringify(result).includes('private-marker'), false)
  })
}

for (const data of [{ vehicles: [], user_id: 99 }, { other: [] }, { vehicles: [vehicle, vehicle] }, []]) {
  test('list requires exact collection shape and unique public identities', async (t) => {
    replaceFetch(t, async () => response(200, data))
    assert.equal((await listVehicles()).kind, 'unexpected')
  })
}

const safeError = { loc: ['body', 'make'], msg: 'Enter nonblank text with valid Unicode and no NUL.', type: 'value_error' }
test('safe validation errors are accepted and unsafe errors never enter UI state', async (t) => {
  replaceFetch(t, async () => response(422, { detail: [safeError] }, null))
  const result = await createVehicle(body)
  assert.equal(result.kind, 'invalid')
  assert.deepEqual(result.errors, { make: safeError.msg })
  for (const entry of [{ ...safeError, input: 'private-marker' }, { ...safeError, ctx: {} },
    { ...safeError, msg: 'private-marker' }, { ...safeError, loc: ['body', 'user_id'] },
    { ...safeError, type: {} }]) assert.equal(parseVehicleErrors([entry]), null)
})

for (const [status, detail, kind] of [
  [401, 'Not authenticated.', 'guest'], [403, 'Request not allowed.', 'forbidden'],
  [503, 'Authentication unavailable. Please try again.', 'authentication-unavailable'],
  [503, 'Vehicles unavailable. Please try again.', 'unavailable'], [500, 'Internal server error', 'unexpected'],
  [409, 'private-marker', 'uncertain'],
]) {
  test(`POST status ${status} uses safe distinct feedback ${kind}`, async (t) => {
    replaceFetch(t, async () => response(status, { detail }, null))
    const result = await createVehicle(body)
    assert.equal(result.kind, kind)
    assert.equal(JSON.stringify(result).includes('private-marker'), false)
    if (status === 503 && kind === 'unavailable') assert.match(result.message, /may have been created/)
  })
}

for (const operation of [listVehicles, (signal) => createVehicle(body, signal)]) {
  test('ten-second bound cancels once without polling or retries', async (t) => {
    t.mock.timers.enable({ apis: ['setTimeout'] })
    let calls = 0
    replaceFetch(t, (url, options) => new Promise((resolve, reject) => {
      calls += 1
      options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })
    }))
    const pending = operation()
    t.mock.timers.tick(10000)
    assert.equal((await pending).kind, 'network')
    t.mock.timers.tick(60000)
    assert.equal(calls, 1)
  })
}

test('network and malformed success outcomes remain uncertain and do not retry POST', async (t) => {
  let calls = 0
  replaceFetch(t, async () => { calls += 1; throw new TypeError('private-marker') })
  let result = await createVehicle(body)
  assert.equal(result.kind, 'network')
  assert.match(result.message, /may have been created/)
  assert.equal(calls, 1)
  globalThis.fetch = async () => { calls += 1; return new Response('{', { status: 201 }) }
  result = await createVehicle(body)
  assert.equal(result.kind, 'uncertain')
  assert.equal(JSON.stringify(result).includes('private-marker'), false)
  assert.equal(calls, 2)
})

test('external cancellation before send performs no request', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch', async () => assert.fail('Must not send'))
  const controller = new AbortController()
  controller.abort()
  assert.equal((await createVehicle(body, controller.signal)).kind, 'cancelled')
  assert.equal(fetch.mock.callCount(), 0)
})

test('ten-second vehicle timeout also covers consuming the response body', async (t) => {
  t.mock.timers.enable({ apis: ['setTimeout'] })
  let signal
  replaceFetch(t, async (url, options) => {
    signal = options.signal
    return { status: 201, headers: new Headers({ 'X-GarageGuide-Session-Expires-At': deadline }),
      json: () => new Promise((resolve, reject) => signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })) }
  })
  const pending = createVehicle(body)
  await Promise.resolve()
  t.mock.timers.tick(10000)
  const result = await pending
  assert.equal(result.kind, 'network')
  assert.equal(signal.aborted, true)
  assert.match(result.message, /may have been created/)
})
