import assert from 'node:assert/strict'
import test from 'node:test'
import { addServicePart, listServiceParts, lookupServicePart, removeServicePart } from '../src/api.js'
import { catalogConflictMessage, catalogMissingMessage, isCatalogPreview, isPartSnapshot, partMessages, preparePartInput } from '../src/servicePartValidation.js'
import { catalog, manual, preview, snapshot, stamp } from './servicePartFixtures.js'

const operations = ['list', 'lookup', 'manual', 'catalog', 'remove']
const data = (operation) => operation === 'list' ? { vehicle_id: 7, service_record_id: 8, parts: [snapshot] } :
  operation === 'lookup' ? preview : operation === 'remove' ? { id: 9, service_record_id: 8, deleted: true } :
    operation === 'catalog' ? { ...snapshot, part_id: preview.id, name: preview.name, manufacturer: preview.manufacturer, part_number: preview.part_number } : snapshot
const response = (operation, body = data(operation), status = ['manual', 'catalog'].includes(operation) ? 201 : 200, deadline = stamp()) => new Response(JSON.stringify(body), {
  status, headers: { 'Content-Type': 'application/json', ...(deadline ? { 'X-GarageGuide-Session-Expires-At': deadline } : {}) },
})
function invoke(operation, ...args) {
  const vid = args.length ? args[0] : '7', sid = args.length >= 2 ? args[1] : '8', signal = args[2]
  return operation === 'list' ? listServiceParts(vid, sid, signal) :
    operation === 'lookup' ? lookupServicePart(vid, sid, { manufacturer: 'Maker', part_number: 'EX-123' }, signal) :
      operation === 'remove' ? removeServicePart(vid, sid, '9', true, signal) : addServicePart(vid, sid, operation === 'catalog' ? catalog : manual, signal)
}

for (const operation of operations) test(`${operation}: exact request path, headers, credentials and response`, async (t) => {
  const calls = []
  t.mock.method(globalThis, 'fetch', async (...args) => { calls.push(args); return response(operation) })
  const result = await invoke(operation)
  assert.equal(result.kind, 'success')
  assert.equal(calls.length, 1)
  const [url, options] = calls[0]
  assert.equal(url, '/api/vehicles/7/services/8/parts' + (operation === 'lookup' ? '/lookup' : operation === 'remove' ? '/9' : ''))
  assert.equal(options.credentials, 'same-origin')
  assert.equal(options.method, operation === 'list' ? 'GET' : operation === 'remove' ? 'DELETE' : 'POST')
  assert.equal(options.signal instanceof AbortSignal, true)
  if (operation === 'list') assert.equal(options.body, undefined)
  else {
    assert.equal(options.headers['X-GarageGuide-CSRF'], '1')
    assert.equal(options.headers['Content-Type'], 'application/json')
    assert.deepEqual(JSON.parse(options.body), operation === 'lookup' ? { manufacturer: 'Maker', part_number: 'EX-123' } : operation === 'remove' ? { confirm_removal: true } : operation === 'catalog' ? catalog : manual)
  }
})

for (const operation of operations) for (const bad of [null, undefined, 7, '0', '01', '+7', '7.0', ' 7', '7 ', '７', '%37', '2147483648']) {
  test(`${operation}: invalid vehicle/service IDs never dispatch ${JSON.stringify(bad)}`, async (t) => {
    const spy = t.mock.method(globalThis, 'fetch', async () => response(operation))
    assert.equal((await invoke(operation, bad)).kind, 'invalid')
    assert.equal((await invoke(operation, '7', bad)).kind, 'invalid')
    assert.equal(spy.mock.callCount(), 0)
  })
}
for (const bad of [null, undefined, 9, '0', '01', ' 9', '+9', '9.0', '９', '2147483648']) test(`invalid snapshot ID never dispatches ${JSON.stringify(bad)}`, async (t) => {
  const spy = t.mock.method(globalThis, 'fetch', async () => response('remove'))
  assert.equal((await removeServicePart('7', '8', bad, true)).kind, 'invalid')
  assert.equal(spy.mock.callCount(), 0)
})
for (const confirmed of [undefined, false, null, 1, 'true']) test(`removal is explicitly confirmed: ${JSON.stringify(confirmed)}`, async (t) => {
  const spy = t.mock.method(globalThis, 'fetch', async () => response('remove'))
  assert.equal((await removeServicePart('7', '8', '9', confirmed)).kind, 'invalid')
  assert.equal(spy.mock.callCount(), 0)
})

test('manual normalization keeps Python whitespace, FEFF, long interior text and null fields distinct', async (t) => {
  const text = '\ufeffBefore' + ' '.repeat(32768) + 'After\ufeff'
  const prepared = preparePartInput({ source: 'manual', name: '\u0085' + text + '\u001c', notes: ' \t', manufacturer: '0', quantity: '2147483647' })
  assert.deepEqual(prepared.details, { source: 'manual', name: text, manufacturer: '0', part_number: null, quantity: 2147483647, notes: null })
  assert.equal(isPartSnapshot({ ...snapshot, name: text, notes: ' \ufeff ' }), true)
  const calls = []
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    calls.push(JSON.parse(options.body))
    return response('manual', { ...snapshot, name: text, manufacturer: '0', quantity: 2147483647 })
  })
  assert.equal((await addServicePart('7', '8', { ...prepared.details })).kind, 'success')
  assert.equal(calls.length, 1)
})
for (const quantity of [null, true, false, 0, -1, 2147483648, 1.5, '', '1.0', '1e2', '+1', ' 1', '１']) test(`invalid form quantity ${JSON.stringify(quantity)}`, () => {
  assert.equal(preparePartInput({ source: 'manual', name: 'Filter', quantity }).invalid, true)
})
test('quantity defaults only when absent and all extra fields are rejected', () => {
  assert.equal(preparePartInput({ source: 'manual', name: 'Filter' }).details.quantity, 1)
  for (const extra of ['user_id', 'vehicle_id', 'part_id', 'created_at']) assert.equal(preparePartInput({ ...manual, [extra]: 1 }).invalid, true)
  assert.equal(preparePartInput({ ...catalog, name: 'Override' }).invalid, true)
})

for (const operation of operations) test(`${operation}: wrong public shape is rejected safely`, async (t) => {
  const spy = t.mock.method(globalThis, 'fetch', async () => response(operation, { ...data(operation), private: 'server-only' }))
  const result = await invoke(operation)
  assert.equal(result.kind, ['manual', 'catalog', 'remove'].includes(operation) ? 'uncertain' : 'unexpected')
  assert.equal(JSON.stringify(result).includes('server-only'), false)
  assert.equal(spy.mock.callCount(), 1)
})
for (const bad of [{ ...snapshot, quantity: '1' }, { ...snapshot, service_record_id: 99 }, { ...snapshot, notes: 'bad\0text' }]) test(`mixed history rejects invalid snapshot ${JSON.stringify(bad)}`, async (t) => {
  t.mock.method(globalThis, 'fetch', async () => response('list', { vehicle_id: 7, service_record_id: 8, parts: [snapshot, bad] }))
  assert.equal((await invoke('list')).kind, 'unexpected')
})
test('duplicate snapshot IDs and mismatched parent envelopes are rejected', async (t) => {
  for (const body of [{ vehicle_id: 7, service_record_id: 8, parts: [snapshot, snapshot] }, { vehicle_id: 99, service_record_id: 8, parts: [] }]) {
    t.mock.method(globalThis, 'fetch', async () => response('list', body))
    assert.equal((await invoke('list')).kind, 'unexpected')
  }
})
test('catalog lookup is exact and requires every displayed identity field', async (t) => {
  const exact = { ...preview, manufacturer: ' Maker ', part_number: 'Ex-123\ufeff' }
  assert.equal(isCatalogPreview(exact), true)
  t.mock.method(globalThis, 'fetch', async (url, options) => response('lookup', { ...exact, ...JSON.parse(options.body) }))
  assert.equal((await lookupServicePart('7', '8', exact)).kind, 'invalid')
  const result = await lookupServicePart('7', '8', { manufacturer: exact.manufacturer, part_number: exact.part_number })
  assert.deepEqual(result.preview, exact)
})
for (const [status, detail, expected] of [
  [401, 'Not authenticated.', 'guest'], [403, 'Request not allowed.', 'forbidden'],
  [404, 'Service record not found.', 'not-found'], [404, 'Vehicle not found.', 'not-found'],
  [503, 'Authentication unavailable. Please try again.', 'authentication-unavailable'],
  [503, 'Service parts unavailable. Please try again.', 'unavailable'],
]) test(`fixed ${status} ${detail}`, async (t) => {
  t.mock.method(globalThis, 'fetch', async () => response('list', { detail }, status))
  assert.equal((await invoke('list')).kind, expected)
})
test('catalog miss and stale preview never become manual creation or automatic retries', async (t) => {
  const spy = t.mock.method(globalThis, 'fetch', async () => response('lookup', { detail: catalogMissingMessage }, 404))
  assert.equal((await invoke('lookup')).kind, 'catalog-missing')
  t.mock.method(globalThis, 'fetch', async () => response('catalog', { detail: catalogConflictMessage }, 409))
  assert.equal((await invoke('catalog')).kind, 'stale-preview')
  assert.equal(spy.mock.callCount(), 1)
})
test('sanitized validation is parsed, but raw input or unknown messages are rejected', async (t) => {
  for (const extra of [false, true]) {
    const detail = [{ loc: ['body', 'quantity'], msg: partMessages.quantity, type: 'value_error', ...(extra ? { input: 'private' } : {}) }]
    t.mock.method(globalThis, 'fetch', async () => response('manual', { detail }, 422))
    const result = await invoke('manual')
    assert.equal(result.kind, extra ? 'uncertain' : 'invalid')
    assert.equal(JSON.stringify(result).includes('private'), false)
  }
})
test('malformed validation types and locations cannot pass through property coercion', async (t) => {
  for (const entry of [
    { loc: ['body', 'quantity'], msg: partMessages.quantity, type: ['value_error'] },
    { loc: ['body', ['quantity']], msg: partMessages.quantity, type: 'value_error' },
    { loc: ['body', 'quantity'], msg: [partMessages.quantity], type: 'value_error' },
  ]) {
    t.mock.method(globalThis, 'fetch', async () => response('manual', { detail: [entry] }, 422))
    assert.equal((await invoke('manual')).kind, 'uncertain')
  }
})
for (const operation of ['manual', 'catalog', 'remove']) for (const status of [500, 503]) test(`${operation}: ${status} may follow a committed write`, async (t) => {
  const spy = t.mock.method(globalThis, 'fetch', async () => response(operation, { detail: status === 503 ? 'Service parts unavailable. Please try again.' : 'Internal server error' }, status))
  const result = await invoke(operation)
  assert.equal(result.uncertain, true)
  assert.match(result.message, /Reload/)
  assert.equal(spy.mock.callCount(), 1)
})
for (const operation of operations) test(`${operation}: ten-second timeout, cancellation and no retries`, async (t) => {
  t.mock.timers.enable({ apis: ['setTimeout'] })
  const spy = t.mock.method(globalThis, 'fetch', async (url, { signal }) => new Promise((resolve, reject) => {
    signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })
  }))
  const pending = invoke(operation)
  t.mock.timers.tick(10000)
  const result = await pending
  assert.equal(result.kind, ['manual', 'catalog', 'remove'].includes(operation) ? 'uncertain' : 'network')
  assert.equal(spy.mock.callCount(), 1)
  t.mock.timers.tick(60000)
  assert.equal(spy.mock.callCount(), 1)
})
test('pre-aborted requests never dispatch, post-dispatch write abort remains uncertain', async (t) => {
  const before = new AbortController(); before.abort()
  const spy = t.mock.method(globalThis, 'fetch', async (url, { signal }) => new Promise((resolve, reject) => signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))))
  assert.equal((await invoke('manual', '7', '8', before.signal)).kind, 'cancelled')
  assert.equal(spy.mock.callCount(), 0)
  const after = new AbortController(), pending = invoke('manual', '7', '8', after.signal)
  after.abort()
  assert.equal((await pending).kind, 'uncertain')
  assert.equal(spy.mock.callCount(), 1)
})
for (const operation of ['list', 'manual']) test(`${operation}: malformed JSON does not expose response text`, async (t) => {
  t.mock.method(globalThis, 'fetch', async () => new Response('private response', { status: operation === 'manual' ? 201 : 200 }))
  const result = await invoke(operation)
  assert.equal(result.kind, operation === 'manual' ? 'uncertain' : 'unexpected')
  assert.equal(JSON.stringify(result).includes('private response'), false)
})
