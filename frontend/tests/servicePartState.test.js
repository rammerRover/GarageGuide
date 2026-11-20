import assert from 'node:assert/strict'
import test from 'node:test'
import { catalogConflictMessage, catalogMissingMessage } from '../src/servicePartValidation.js'
import { fixture, loaded, now, stamp, snapshot, preview, deferred, selectCatalog } from './servicePartFixtures.js'

test('load, manual add, required refresh and confirmed removal keep separate saved and draft values', async () => {
  const f = await loaded()
  assert.deepEqual(f.store.getSnapshot().parts, [snapshot])
  assert.equal(f.store.getSnapshot().draft.quantity, '1')
  f.store.edit('name', '  New filter  ')
  assert.equal(f.store.getSnapshot().parts[0].name, snapshot.name)
  assert.equal((await f.store.submit()).kind, 'success')
  assert.equal(f.calls.add.length, 1)
  assert.equal(f.calls.add[0][2].name, 'New filter')
  assert.equal(f.calls.list.length, 2)
  assert.equal(f.store.getSnapshot().refreshRequired, false)
  assert.equal(f.store.getSnapshot().draft.name, '')
  assert.equal(f.store.requestRemoval('9'), true)
  f.store.cancelRemoval()
  assert.equal((await f.store.confirmRemoval()).kind, 'cancelled')
  assert.equal(f.calls.remove.length, 0)
  f.store.requestRemoval('9')
  await f.store.confirmRemoval()
  assert.equal(f.calls.remove.length, 1)
  assert.equal(f.calls.remove[0][3], true)
  assert.equal(f.calls.list.length, 3)
  assert.equal(f.store.getSnapshot().parts.some((part) => part.id === 9), false)
  f.store.dispose()
})

test('catalog lookup requires review, exact pair changes invalidate it and successful add clears the preview', async () => {
  const f = await loaded()
  selectCatalog(f.store)
  assert.equal((await f.store.submit()).kind, 'invalid')
  assert.equal(f.calls.add.length, 0)
  await f.store.lookup()
  assert.deepEqual(f.store.getSnapshot().preview, preview)
  f.store.editLookup('manufacturer', 'Other maker')
  assert.equal(f.store.getSnapshot().preview, null)
  assert.equal((await f.store.submit()).kind, 'invalid')
  f.store.editLookup('manufacturer', preview.manufacturer)
  assert.equal(f.calls.lookup.length, 1)
  await f.store.lookup()
  await f.store.submit()
  assert.equal(f.calls.add.length, 1)
  assert.deepEqual(f.calls.add[0][2].preview, preview)
  assert.equal(f.store.getSnapshot().preview, null)
  assert.equal(f.store.getSnapshot().source, 'catalog')
  f.store.dispose()
})

test('stale preview requires deliberate lookup or explicit manual switch, without automatic fallback', async () => {
  const f = await loaded({ addServicePart: async (vid, sid, details) => details.source === 'catalog'
    ? { kind: 'stale-preview', message: catalogConflictMessage } : { kind: 'success', part: { ...snapshot, id: 10, name: details.name }, deadline: stamp() } })
  selectCatalog(f.store); await f.store.lookup(); await f.store.submit()
  assert.equal(f.store.getSnapshot().status, 'stale-preview')
  assert.equal(f.store.getSnapshot().source, 'catalog')
  assert.equal(f.store.getSnapshot().preview, null)
  assert.equal(f.calls.lookup.length, 1)
  assert.equal((await f.store.submit()).kind, 'invalid')
  assert.equal(f.calls.add.length, 1)
  f.store.chooseSource('manual'); f.store.edit('name', 'Manual correction')
  await f.store.submit()
  assert.equal(f.calls.add.length, 2)
  assert.equal(f.calls.add[1][2].source, 'manual')
  f.store.dispose()
})

test('empty catalog offers a deliberate manual path', async () => {
  const f = await loaded({ lookupServicePart: async () => ({ kind: 'catalog-missing', message: catalogMissingMessage }) })
  selectCatalog(f.store); await f.store.lookup()
  assert.equal(f.store.getSnapshot().status, 'catalog-missing')
  assert.equal(f.store.getSnapshot().source, 'catalog')
  assert.equal(f.calls.add.length, 0)
  f.store.chooseSource('manual'); f.store.edit('name', 'Not in catalog')
  assert.equal((await f.store.submit()).kind, 'success')
  f.store.dispose()
})

test('corrected second draft can submit after a successful required refresh', async () => {
  const f = await loaded()
  f.store.edit('name', 'First'); await f.store.submit()
  assert.equal((await f.store.submit()).kind, 'invalid')
  f.store.edit('name', 'Second')
  assert.equal((await f.store.submit()).kind, 'success')
  assert.equal(f.calls.add.length, 2)
  assert.equal(f.calls.list.length, 3)
  f.store.dispose()
})
for (const operation of ['add', 'remove']) test(`${operation}: failed required refresh blocks more writes until deliberate reload succeeds`, async () => {
  let reads = 0, fail = true
  const f = await loaded({ listServiceParts: async () => ++reads > 1 && fail ? { kind: 'unavailable' } : { kind: 'success', parts: [snapshot], deadline: stamp() } })
  if (operation === 'add') { f.store.edit('name', 'First'); await f.store.submit() }
  else { f.store.requestRemoval('9'); await f.store.confirmRemoval() }
  assert.equal(f.store.getSnapshot().refreshRequired, true)
  f.store.edit('name', 'Next')
  assert.equal((await f.store.submit()).kind, 'cancelled')
  assert.equal(f.store.requestRemoval('9'), false)
  f.store.requestReload(); await f.store.reload()
  assert.equal(f.store.getSnapshot().refreshRequired, true)
  fail = false
  f.store.requestReload(); await f.store.reload()
  assert.equal(f.store.getSnapshot().refreshRequired, false)
  if (operation === 'add') assert.equal(f.calls.add.length, 1)
  else assert.equal(f.calls.remove.length, 1)
  f.store.dispose()
})

test('uncertain create requires successful inspection and explicit duplicate-risk acknowledgment', async () => {
  let reads = 0
  const f = await loaded({ addServicePart: async () => ({ kind: 'uncertain', uncertain: true }),
    listServiceParts: async () => ({ kind: 'success', parts: reads++ ? [] : [snapshot], deadline: stamp() }) })
  f.store.edit('name', 'May exist'); await f.store.submit()
  assert.equal(f.calls.list.length, 1)
  assert.equal(f.store.getSnapshot().draft.name, 'May exist')
  assert.equal(f.store.acknowledgeAddRisk(), false)
  assert.equal((await f.store.submit()).kind, 'cancelled')
  f.store.requestReload(); await f.store.reload()
  assert.equal(f.store.getSnapshot().parts.length, 0)
  assert.match(f.store.getSnapshot().message, /absent entry does not prove failure/)
  assert.equal((await f.store.submit()).kind, 'cancelled')
  assert.equal(f.store.acknowledgeAddRisk(), true)
  assert.equal(f.calls.add.length, 1)
  await f.store.submit()
  assert.equal(f.calls.add.length, 2)
  f.store.dispose()
})
for (const present of [true, false]) test(`uncertain removal: inspected current presence ${present} never automatically retries`, async () => {
  let reads = 0
  const f = await loaded({ removeServicePart: async () => ({ kind: 'uncertain', uncertain: true }),
    listServiceParts: async () => ({ kind: 'success', parts: reads++ === 0 || present ? [snapshot] : [], deadline: stamp() }) })
  f.store.requestRemoval('9'); await f.store.confirmRemoval()
  assert.equal(f.calls.remove.length, 1)
  assert.equal((await f.store.confirmRemoval()).kind, 'cancelled')
  f.store.requestReload(); await f.store.reload()
  assert.equal(f.store.getSnapshot().confirmation, null)
  assert.equal(f.calls.remove.length, 1)
  assert.equal((await f.store.confirmRemoval()).kind, 'cancelled')
  if (present) {
    assert.equal(f.store.requestRemoval('9'), true)
    await f.store.confirmRemoval()
    assert.equal(f.calls.remove.length, 2)
  } else assert.match(f.store.getSnapshot().message, /currently absent/)
  f.store.dispose()
})

for (const operation of ['add', 'lookup', 'remove']) test(`${operation}: synchronous in-flight guard prevents repeated requests`, async () => {
  const reply = deferred()
  const method = { add: 'addServicePart', lookup: 'lookupServicePart', remove: 'removeServicePart' }[operation]
  const f = await loaded({ [method]: () => reply.promise })
  if (operation === 'add') f.store.edit('name', 'Filter')
  if (operation === 'lookup') selectCatalog(f.store)
  if (operation === 'remove') f.store.requestRemoval('9')
  const action = () => operation === 'add' ? f.store.submit() : operation === 'lookup' ? f.store.lookup() : f.store.confirmRemoval()
  const pending = action()
  assert.equal((await action()).kind, 'cancelled')
  assert.equal(f.calls[operation].length, 1)
  reply.resolve(operation === 'lookup' ? { kind: 'success', preview, deadline: stamp() } : operation === 'remove'
    ? { kind: 'success', removed: { id: 9, service_record_id: 8, deleted: true }, deadline: stamp() }
    : { kind: 'success', part: snapshot, deadline: stamp() })
  await pending
  f.store.dispose()
})

test('changing an in-flight lookup pair cancels old preview work before it can extend the deadline', async () => {
  const reply = deferred(), f = await loaded({ lookupServicePart: () => reply.promise })
  selectCatalog(f.store)
  const pending = f.store.lookup()
  f.store.editLookup('part_number', 'Another')
  const deadline = f.session.getSnapshot().expires_at
  reply.resolve({ kind: 'success', preview, deadline: stamp(60) })
  assert.equal((await pending).kind, 'cancelled')
  assert.equal(f.store.getSnapshot().preview, null)
  assert.equal(f.store.getSnapshot().lookupPair.part_number, 'Another')
  assert.equal(f.session.getSnapshot().expires_at, deadline)
  f.store.dispose()
})

for (const operation of ['load', 'lookup', 'add', 'remove']) for (const event of ['navigation', 'back-forward', 'hidden', 'departure', 'dispose', 'logout', 'account-change', 'same-account-login', 'expiration']) {
  test(`${operation}: ${event} prevents late private state or session deadline restoration`, async () => {
    let clock = now
    const reply = deferred()
    const method = { load: 'listServiceParts', lookup: 'lookupServicePart', add: 'addServicePart', remove: 'removeServicePart' }[operation]
    const f = operation === 'load' ? await fixture({ [method]: () => reply.promise }, () => clock) : await loaded({ [method]: () => reply.promise }, () => clock)
    if (operation === 'lookup') selectCatalog(f.store)
    if (operation === 'add') f.store.edit('name', 'Filter')
    if (operation === 'remove') f.store.requestRemoval('9')
    const pending = operation === 'load' ? f.store.load('7', '8') : operation === 'lookup' ? f.store.lookup() : operation === 'add' ? f.store.submit() : f.store.confirmRemoval()
    if (event === 'navigation') await f.session.enter('other', '/vehicles')
    if (event === 'back-forward') { await f.session.enter('back', '/account'); await f.session.enter('forward', '/vehicles/7/services/8') }
    if (event === 'hidden') f.session.hide()
    if (event === 'departure') f.store.depart()
    if (event === 'dispose') f.store.dispose()
    if (event === 'logout') await f.session.logout()
    if (event === 'account-change') await f.session.login({ id: 2 })
    if (event === 'same-account-login') await f.session.login({ id: 1 })
    if (event === 'expiration') { clock = Date.parse(f.session.getSnapshot().expires_at); await f.session.authenticatedRequest(async () => assert.fail('Expired session performed a request')) }
    const deadline = f.session.getSnapshot().expires_at
    reply.resolve({ kind: 'success', parts: [snapshot], preview, part: snapshot,
      removed: { id: 9, service_record_id: 8, deleted: true }, deadline: stamp(60) })
    assert.equal((await pending).kind, 'cancelled')
    assert.deepEqual(f.store.getSnapshot().parts, [])
    assert.equal(f.store.getSnapshot().draft.name, '')
    assert.equal(f.store.getSnapshot().preview, null)
    assert.equal(f.session.getSnapshot().expires_at, deadline)
    f.store.dispose()
  })
}

for (const deadline of [undefined, 'malformed', stamp(-1), stamp(29), stamp(30), stamp(31)]) test(`successful current response handles deadline ${deadline}`, async () => {
  const f = await loaded({ listServiceParts: async () => ({ kind: 'success', parts: [snapshot], deadline }) })
  assert.equal(f.store.getSnapshot().status, 'ready')
  assert.equal(f.session.getSnapshot().expires_at, deadline === stamp(31) ? stamp(31) : stamp(30))
  assert.equal(f.calls.session, 1)
  f.store.dispose()
})

test('deadline equality clears parts and drafts without polling or expiry-triggered requests', async (t) => {
  t.mock.timers.enable({ apis: ['setTimeout'] })
  let clock = now
  const f = await loaded({}, () => clock)
  f.store.edit('name', 'Private draft')
  const stop = f.session.watchExpiry()
  clock = Date.parse(f.session.getSnapshot().expires_at)
  t.mock.timers.tick(clock - now)
  assert.equal(f.session.getSnapshot().user, null)
  assert.deepEqual(f.store.getSnapshot().parts, [])
  assert.equal(f.store.getSnapshot().draft.name, '')
  t.mock.timers.tick(8 * 60 * 60000)
  assert.equal(f.calls.session, 1)
  assert.equal(f.calls.list.length, 1)
  assert.equal(f.calls.add.length, 0)
  stop(); f.store.dispose()
})

for (const kind of ['guest', 'authentication-unavailable']) test(`${kind} clears private drafts and previews`, async () => {
  const f = await loaded({ addServicePart: async () => ({ kind }) })
  f.store.edit('name', 'Private draft'); await f.store.submit()
  assert.deepEqual(f.store.getSnapshot().parts, [])
  assert.equal(f.store.getSnapshot().draft.name, '')
  assert.equal(f.store.getSnapshot().preview, null)
  assert.notEqual(f.session.getSnapshot().status, 'authenticated')
  f.store.dispose()
})

test('superseded IDs and late failures cannot overwrite a new service draft', async () => {
  const reply = deferred(), f = await loaded({ addServicePart: () => reply.promise })
  f.store.edit('name', 'Old draft'); const pending = f.store.submit()
  f.store.depart(); await f.store.load('7', '10'); f.store.edit('name', 'New draft')
  const deadline = f.session.getSnapshot().expires_at
  reply.resolve({ kind: 'stale-preview', message: 'Old conflict', deadline: stamp(60) })
  assert.equal((await pending).kind, 'cancelled')
  assert.equal(f.store.getSnapshot().draft.name, 'New draft')
  assert.equal(f.store.getSnapshot().serviceId, '10')
  assert.equal(f.session.getSnapshot().expires_at, deadline)
  f.store.dispose()
})
test('competing loads cannot restore the earlier service or its newer-looking deadline', async () => {
  const reply = deferred()
  let calls = 0
  const f = await fixture({ listServiceParts: async (vid, sid) => ++calls === 1 ? reply.promise :
    { kind: 'success', parts: [{ ...snapshot, service_record_id: Number(sid) }], deadline: stamp() } })
  const first = f.store.load('7', '8')
  await f.store.load('7', '10')
  reply.resolve({ kind: 'success', parts: [snapshot], deadline: stamp(60) })
  assert.equal((await first).kind, 'cancelled')
  assert.equal(f.store.getSnapshot().parts[0].service_record_id, 10)
  assert.equal(f.session.getSnapshot().expires_at, stamp())
  f.store.dispose()
})
for (const kind of ['invalid', 'unavailable', 'forbidden', 'unexpected']) test(`${kind} errors never extend session deadlines`, async () => {
  const f = await loaded({ lookupServicePart: async () => ({ kind, errors: {}, deadline: stamp(60) }) })
  selectCatalog(f.store)
  const deadline = f.session.getSnapshot().expires_at
  await f.store.lookup()
  assert.equal(f.session.getSnapshot().expires_at, deadline)
  assert.equal(f.store.getSnapshot().source, 'catalog')
  f.store.dispose()
})
for (const bad of [null, undefined, '0', '01', '+7', '7.0', '７', '2147483648']) test(`invalid route IDs gate saved parts before dispatch ${JSON.stringify(bad)}`, async () => {
  const f = await loaded()
  assert.equal((await f.store.load(bad, '8')).kind, 'invalid')
  assert.deepEqual(f.store.getSnapshot().parts, [])
  assert.equal(f.calls.list.length, 1)
  f.store.dispose()
})
