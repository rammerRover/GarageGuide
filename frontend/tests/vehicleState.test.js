import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createVehicleStore } from '../src/vehicleState.js'

function deferred() { let resolve; const promise = new Promise((done) => { resolve = done }); return { promise, resolve } }
const direct = (operation, signal) => operation(signal)

test('garage transitions through loading, empty, populated and unavailable with deliberate retry', async () => {
  const first = deferred()
  let calls = 0
  const api = { listVehicles: async () => {
    calls += 1
    return calls === 1 ? first.promise : calls === 2 ? { kind: 'unavailable', message: 'Your garage is unavailable. Please try again.' } : { kind: 'success', vehicles: [{ id: 2 }] }
  } }
  const store = createVehicleStore(direct, api)
  const loading = store.load()
  assert.equal(store.getSnapshot().status, 'loading')
  first.resolve({ kind: 'success', vehicles: [] })
  await loading
  assert.deepEqual(store.getSnapshot().vehicles, [])
  assert.equal(store.getSnapshot().status, 'success')
  await store.load()
  assert.equal(store.getSnapshot().status, 'unavailable')
  assert.equal(calls, 2)
  await store.load()
  assert.deepEqual(store.getSnapshot().vehicles, [{ id: 2 }])
  assert.equal(calls, 3)
})

test('create has an immediate guard against click or Enter repetition and never retries', async () => {
  const reply = deferred()
  let calls = 0
  const store = createVehicleStore(direct, { createVehicle: () => { calls += 1; return reply.promise } })
  const first = store.submit({})
  assert.equal(store.getSnapshot().pending, true)
  assert.equal((await store.submit({})).kind, 'cancelled')
  reply.resolve({ kind: 'network', message: 'Check your garage before submitting again.' })
  await first
  assert.equal(store.getSnapshot().pending, false)
  assert.equal(store.getSnapshot().status, 'network')
  assert.equal(calls, 1)
})

test('correctable field errors clear individually without another focus request or mutation', () => {
  const store = createVehicleStore(direct, {})
  store.invalid({ make: 'Required', model: 'Required' })
  const version = store.getSnapshot().focusVersion
  store.correct('make')
  assert.deepEqual(store.getSnapshot().errors, { model: 'Required' })
  assert.equal(store.getSnapshot().focusVersion, version)
})

for (const kind of ['invalid', 'network', 'uncertain', 'unavailable', 'forbidden', 'unexpected']) {
  test(`creation preserves correctable input ownership outside store after ${kind}`, async () => {
    const input = { make: 'Synthetic' }
    const store = createVehicleStore(direct, { createVehicle: async () => ({ kind, errors: { make: 'Safe error' }, message: 'Safe feedback' }) })
    await store.submit(input)
    assert.deepEqual(input, { make: 'Synthetic' })
    assert.equal(store.getSnapshot().status, kind)
    assert.equal(store.getSnapshot().pending, false)
    assert.equal(Object.hasOwn(store.getSnapshot(), 'details'), false)
  })
}

test('dispose clears cached vehicles and ignores late responses; remount can load again', async () => {
  const reply = deferred()
  let calls = 0
  const store = createVehicleStore(direct, { listVehicles: () => ++calls === 1 ? reply.promise : Promise.resolve({ kind: 'success', vehicles: [] }) })
  const old = store.load()
  store.dispose()
  reply.resolve({ kind: 'success', vehicles: [{ id: 99 }] })
  assert.equal((await old).kind, 'cancelled')
  assert.deepEqual(store.getSnapshot().vehicles, [])
  await store.load()
  assert.equal(store.getSnapshot().status, 'success')
  assert.deepEqual(store.getSnapshot().vehicles, [])
})

test('new list request suppresses older data even if cancellation is ignored by transport', async () => {
  const first = deferred()
  let calls = 0
  const store = createVehicleStore(direct, { listVehicles: () => ++calls === 1 ? first.promise : Promise.resolve({ kind: 'success', vehicles: [{ id: 2 }] }) })
  const old = store.load()
  await store.load()
  first.resolve({ kind: 'success', vehicles: [{ id: 1 }] })
  assert.equal((await old).kind, 'cancelled')
  assert.deepEqual(store.getSnapshot().vehicles, [{ id: 2 }])
})

test('unexpected request exceptions give safe feedback and release pending guard', async () => {
  const store = createVehicleStore(async () => { throw new Error('private-marker') })
  await store.submit({})
  assert.equal(store.getSnapshot().status, 'unexpected')
  assert.equal(store.getSnapshot().pending, false)
  assert.equal(JSON.stringify(store.getSnapshot()).includes('private-marker'), false)
})
