import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import { createService, getService, listServices, removeService, updateService } from '../src/api.js'
import { isPublicService, isServiceDate, prepareServiceInput, serviceDraft, serviceMessages } from '../src/serviceValidation.js'
import { input, loaded, record, stamp } from './serviceFixtures.js'

const operations = ['list', 'detail', 'create', 'update', 'remove']
const call = (op, signal) => ({ list: () => listServices('7', signal), detail: () => getService('7', '8', signal),
  create: () => createService('7', input, signal), update: () => updateService('7', '8', record, { notes: 'Updated' }, signal),
  remove: () => removeService('7', '8', true, signal) })[op]()
const body = (op) => op === 'list' ? { vehicle_id: 7, services: [record] } : op === 'remove' ? { id: 8, vehicle_id: 7, deleted: true } : record
const respond = (op, data = body(op), status = op === 'create' ? 201 : 200, deadline = stamp()) => new Response(JSON.stringify(data), {
  status, headers: deadline === null ? {} : { 'X-GarageGuide-Session-Expires-At': deadline },
})
function mockFetch(t, fn) { t.mock.method(globalThis, 'fetch', fn) }

for (const op of operations) {
  test(`${op}: exact relative URL, method, headers, body and public response`, async (t) => {
    let count = 0
    mockFetch(t, async (url, options) => {
      count++
      assert.equal(url, `/api/vehicles/7/services${['list', 'create'].includes(op) ? '' : '/8'}`)
      assert.equal(options.method, { list: 'GET', detail: 'GET', create: 'POST', update: 'PATCH', remove: 'DELETE' }[op])
      assert.equal(options.credentials, 'same-origin')
      assert.equal(options.headers.Accept, 'application/json')
      if (['list', 'detail'].includes(op)) assert.equal(options.body, undefined)
      else {
        assert.equal(options.headers['Content-Type'], 'application/json')
        assert.equal(options.headers['X-GarageGuide-CSRF'], '1')
        assert.deepEqual(JSON.parse(options.body), op === 'create' ? input : op === 'update' ? { notes: 'Updated' } : { confirm_removal: true })
      }
      return respond(op)
    })
    assert.equal((await call(op)).kind, 'success')
    assert.equal(count, 1)
  })
  for (const bad of [null, [], {}, { ...body(op), extra: 'private' }, { ...body(op), vehicle_id: 9 }]) {
    test(`${op}: rejects malformed or mismatched success ${JSON.stringify(bad)}`, async (t) => {
      mockFetch(t, async () => respond(op, bad))
      assert.equal((await call(op)).kind, ['list', 'detail'].includes(op) ? 'unexpected' : 'uncertain')
    })
  }
  for (const deadline of [null, 'bad']) test(`${op}: missing/malformed deadline cannot succeed ${deadline}`, async (t) => {
    mockFetch(t, async () => respond(op, body(op), undefined, deadline))
    assert.notEqual((await call(op)).kind, 'success')
  })
  for (const [status, detail, kind] of [
    [401, 'Not authenticated.', 'guest'], [403, 'Request not allowed.', 'forbidden'],
    [503, 'Authentication unavailable. Please try again.', 'authentication-unavailable'],
    [503, 'Service history unavailable. Please try again.', 'unavailable'],
    [404, ['list', 'create'].includes(op) ? 'Vehicle not found.' : 'Service record not found.', 'not-found'],
  ]) test(`${op}: fixed ${status} ${kind}`, async (t) => {
    mockFetch(t, async () => respond(op, { detail }, status))
    assert.equal((await call(op)).kind, kind)
  })
  for (const failure of ['network', 'malformed', 'server', 'raw']) test(`${op}: safe ${failure} result; never retries`, async (t) => {
    let calls = 0
    mockFetch(t, async () => {
      calls++
      if (failure === 'network') throw new TypeError('PRIVATE DRIVER DETAILS')
      if (failure === 'malformed') return new Response('PRIVATE BODY', { status: 200 })
      return respond(op, { detail: failure === 'server' ? 'Internal server error' : 'PRIVATE RAW DATA' }, 500)
    })
    const result = await call(op)
    assert.equal(result.kind, ['list', 'detail'].includes(op) ? failure === 'network' || failure === 'malformed' ? 'network' : 'unexpected' : 'uncertain')
    assert.doesNotMatch(JSON.stringify(result), /PRIVATE/)
    assert.equal(calls, 1)
  })
  test(`${op}: cancellation before dispatch never fetches`, async (t) => {
    mockFetch(t, () => assert.fail('unexpected dispatch'))
    const controller = new AbortController(); controller.abort()
    assert.equal((await call(op, controller.signal)).kind, 'cancelled')
  })
  test(`${op}: cancellation after dispatch accounts for uncertain writes`, async (t) => {
    const controller = new AbortController()
    mockFetch(t, async () => { controller.abort(); return respond(op) })
    assert.equal((await call(op, controller.signal)).kind, ['list', 'detail'].includes(op) ? 'cancelled' : 'uncertain')
  })
  test(`${op}: ten-second timeout aborts once without replay`, async (t) => {
    t.mock.timers.enable({ apis: ['setTimeout'] })
    let calls = 0
    mockFetch(t, (_, options) => { calls++; return new Promise((resolve, reject) => options.signal.addEventListener('abort', () => reject(new DOMException('Timeout', 'AbortError')))) })
    const pending = call(op)
    t.mock.timers.tick(10000)
    assert.equal((await pending).kind, ['list', 'detail'].includes(op) ? 'network' : 'uncertain')
    t.mock.timers.tick(60000)
    assert.equal(calls, 1)
  })
}

for (const id of ['', '0', '01', '+1', '-1', ' 1', '1 ', '1.0', '1e2', '١', '１', '2147483648', '99999999999', 7, null, '%37', '7/8']) {
  test(`canonical IDs reject ${JSON.stringify(id)} without network`, async (t) => {
    mockFetch(t, () => assert.fail('invalid ID dispatched'))
    for (const action of [() => listServices(id), () => getService('7', id), () => createService(id, input),
      () => updateService('7', id, record, { notes: 'x' }), () => removeService('7', id, true)]) {
      assert.notEqual((await action()).kind, 'success')
    }
  })
}
for (const id of ['1', '2147483647']) test(`canonical ID accepts ${id}`, async (t) => {
  mockFetch(t, async () => respond('detail', { ...record, id: Number(id), vehicle_id: Number(id) }))
  assert.equal((await getService(id, id)).kind, 'success')
})
for (const confirmed of [undefined, false, null, 1, 'true', {}]) test(`removal needs literal true: ${JSON.stringify(confirmed)}`, async (t) => {
  mockFetch(t, () => assert.fail('unconfirmed removal'))
  assert.equal((await removeService('7', '8', confirmed)).kind, 'invalid')
})
for (const [op, detail] of [['update', 'Service record is linked to maintenance completion and cannot be changed.'], ['remove', 'Service record has linked data and cannot be removed.']]) {
  test(`${op}: only its fixed 409 is accepted`, async (t) => {
    mockFetch(t, async () => respond(op, { detail }, 409))
    assert.equal((await call(op)).kind, 'conflict')
    mockFetch(t, async () => respond(op, { detail: 'PRIVATE', children: [] }, 409))
    assert.equal((await call(op)).kind, 'uncertain')
  })
}
test('public records enforce exact fields, decimals, dates and Unicode while allowing stored future dates', () => {
  assert.equal(isPublicService(record), true)
  assert.equal(isPublicService({ ...record, service_date: '9999-12-31' }), true)
  for (const changes of [{ id: 2147483648 }, { notes: '' }, { cost: '0' }, { cost: 0 }, { mileage: '-0.0' },
    { mileage: '00.0' }, { service_date: '2026-02-30' }, { notes: '\ud800' }, { description: '\0' }, { user_id: 1 }]) assert.equal(isPublicService({ ...record, ...changes }), false)
  for (const date of ['0000-01-01', '1900-02-29', '2026-04-31', '2026-1-01']) assert.equal(isServiceDate(date), false)
  assert.equal(isServiceDate('2000-02-29'), true)
})
test('changed-only PATCH preserves legacy dates, clears optional blanks and distinguishes zero without float math', () => {
  const legacy = { ...record, service_date: '9999-12-31', mileage: '99999999999.9', cost: '9999999999.99', notes: 'saved' }
  assert.deepEqual(prepareServiceInput({ ...serviceDraft(legacy), notes: ' ', operating_hours: '000.0', cost: '000.00', mileage: '' }, legacy).details,
    { notes: null, operating_hours: '0.0', cost: '0.00', mileage: null })
  assert.equal(prepareServiceInput(serviceDraft(legacy), legacy).unchanged, true)
  assert.deepEqual(prepareServiceInput({ description: '  New  ' }, record).details, { description: 'New' })
  assert.equal(prepareServiceInput({ ...input, service_date: '9999-12-31' }).invalid, false)
})
test('history exposes both entries from the shared backend whitespace response', async (t) => {
  const contract = JSON.parse(readFileSync(new URL('./fixtures/serviceWhitespace.json', import.meta.url), 'utf8'))
  const [affected, ordinary] = contract.response.services
  mockFetch(t, async () => respond('list', contract.response))
  const { store } = await loaded('history', { listServices })
  t.after(() => store.dispose())
  assert.equal(store.getSnapshot().loaded, true)
  assert.deepEqual(store.getSnapshot().records, [affected, ordinary])
  const prepared = prepareServiceInput({ ...input, ...contract.input })
  assert.equal(prepared.invalid, false)
  assert.equal(prepared.details.description, affected.description)
  assert.equal(prepared.details.notes, affected.notes)
  assert.deepEqual(prepareServiceInput({ ...serviceDraft(affected), cost: '10.00' }, affected).details, { cost: '10.00' })
  assert.equal(prepareServiceInput({ notes: '\u0085\u001c' }, affected).details.notes, null)
  assert.equal(prepareServiceInput({ description: '\u0085\u001c' }, affected).invalid, true)
})
for (const value of [0, undefined, '-1', '+1', '1e2', 'NaN', 'Infinity', '1,000', '1.01', '100000000000.0', '١']) test(`invalid reading ${JSON.stringify(value)}`, () => {
  assert.equal(prepareServiceInput({ ...input, mileage: value }).invalid, true)
})
for (const value of [0, '-0', '1.001', '10000000000.00', '1e2']) test(`invalid USD ${JSON.stringify(value)}`, () => {
  assert.equal(prepareServiceInput({ ...input, cost: value }).invalid, true)
})
test('validation responses use only approved locations, messages and types; no raw data', async (t) => {
  for (const extra of [false, true]) {
    mockFetch(t, async () => respond('create', { detail: [{ loc: ['body', 'service_date'], msg: serviceMessages.service_date, type: 'value_error', ...(extra ? { input: 'PRIVATE' } : {}) }] }, 422))
    const result = await createService('7', input)
    assert.equal(result.kind, extra ? 'uncertain' : 'invalid')
    assert.doesNotMatch(JSON.stringify(result), /PRIVATE/)
  }
})
test('unchanged PATCH and invalid input never dispatch', async (t) => {
  mockFetch(t, () => assert.fail('unexpected write'))
  assert.equal((await updateService('7', '8', record, serviceDraft(record))).kind, 'unchanged')
  assert.equal((await createService('7', { ...input, user_id: 1 })).kind, 'invalid')
  for (const field of ['service_date', 'service_type', 'description']) assert.equal(prepareServiceInput({ [field]: null }, record).invalid, true)
})
