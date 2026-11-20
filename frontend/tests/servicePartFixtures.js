import { createSessionStore } from '../src/sessionState.js'
import { createServicePartsStore } from '../src/servicePartState.js'
import { now, stamp, publicSession, deferred } from './serviceFixtures.js'

export { now, stamp, publicSession, deferred }
export const preview = { id: 22, manufacturer: 'Maker', part_number: 'EX-123', name: 'Catalog filter', category: 'Filters' }
export const snapshot = { id: 9, service_record_id: 8, part_id: null, name: 'Filter', part_number: null, manufacturer: null, quantity: 1, notes: null }
export const manual = { source: 'manual', name: 'Filter', part_number: null, manufacturer: null, quantity: 1, notes: null }
export const catalog = { source: 'catalog', preview, quantity: 1, notes: null }

export async function fixture(overrides = {}, clock = () => now) {
  const calls = { session: 0, list: [], lookup: [], add: [], remove: [] }
  const session = createSessionStore({
    getSession: async () => { calls.session += 1; return publicSession() },
    loginAccount: async (data) => publicSession(data?.id ?? 1), logoutAccount: async () => ({ kind: 'success' }),
  }, clock)
  await session.enter('parts', '/vehicles/7/services/8')
  let saved = [snapshot], nextId = 10
  const defaults = {
    listServiceParts: async (vid, sid) => ({ kind: 'success', parts: saved.map((part) => ({ ...part, service_record_id: Number(sid) })), deadline: stamp() }),
    lookupServicePart: async () => ({ kind: 'success', preview, deadline: stamp() }),
    addServicePart: async (vid, sid, details) => {
      const identity = details.source === 'catalog' ? { part_id: details.preview.id, name: details.preview.name,
        part_number: details.preview.part_number, manufacturer: details.preview.manufacturer } :
        { name: details.name, part_number: details.part_number, manufacturer: details.manufacturer }
      const part = { ...snapshot, ...identity, id: nextId++, service_record_id: Number(sid), quantity: details.quantity, notes: details.notes }
      saved = [...saved, part]
      return { kind: 'success', part, deadline: stamp() }
    },
    removeServicePart: async (vid, sid, id) => {
      saved = saved.filter((part) => String(part.id) !== id)
      return { kind: 'success', removed: { id: Number(id), service_record_id: Number(sid), deleted: true }, deadline: stamp() }
    },
  }
  const api = {}
  for (const [name, key] of Object.entries({ listServiceParts: 'list', lookupServicePart: 'lookup', addServicePart: 'add', removeServicePart: 'remove' })) {
    api[name] = (...args) => { calls[key].push(args); return (overrides[name] ?? defaults[name])(...args) }
  }
  const store = createServicePartsStore(session, api, clock)
  return { store, session, calls }
}

export async function loaded(overrides, clock) {
  const result = await fixture(overrides, clock)
  await result.store.load('7', '8')
  return result
}

export function selectCatalog(store) {
  store.chooseSource('catalog')
  store.editLookup('manufacturer', preview.manufacturer)
  store.editLookup('part_number', preview.part_number)
}
