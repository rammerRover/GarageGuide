import { createSessionStore } from '../src/sessionState.js'
import { createServiceHistoryStore, createServiceRecordStore } from '../src/serviceState.js'
import { prepareServiceInput } from '../src/serviceValidation.js'

export const now = Date.parse('2026-11-18T12:00:00Z')
export const stamp = (minutes = 31) => new Date(now + minutes * 60000).toISOString()
export const record = { id: 8, vehicle_id: 7, service_date: '2026-11-17', service_type: 'maintenance',
  description: 'Synthetic maintenance', mileage: '0.0', operating_hours: null, cost: '0.00', notes: null, created_at: stamp(-60) }
export const input = { service_date: record.service_date, service_type: record.service_type, description: record.description }
export function deferred() { let resolve; const promise = new Promise((done) => { resolve = done }); return { promise, resolve } }
export const success = (changes = {}, deadline = stamp()) => ({ kind: 'success', record: { ...record, ...changes }, deadline })
export const publicSession = (id = 1) => ({ kind: 'success', session: {
  user: { id, email: `synthetic-${id}@example.com`, created_at: stamp(-60) }, expires_at: stamp(30),
} })
export async function fixture(mode = 'record', overrides = {}, clock = () => now) {
  const calls = { session: 0, list: [], detail: [], create: [], update: [], remove: [] }
  const session = createSessionStore({
    getSession: async () => { calls.session += 1; return publicSession() },
    loginAccount: async (data) => publicSession(data?.id ?? 1), logoutAccount: async () => ({ kind: 'success' }),
  }, clock)
  await session.enter('vehicle', '/vehicles/7')
  const defaults = {
    listServices: async () => ({ kind: 'success', services: [record], deadline: stamp() }),
    getService: async (vehicleId, serviceId) => success({ id: Number(serviceId), vehicle_id: Number(vehicleId) }),
    createService: async () => success(),
    updateService: async (vehicleId, serviceId, saved, draft) => success({ ...prepareServiceInput(draft, saved).details, id: Number(serviceId), vehicle_id: Number(vehicleId) }),
    removeService: async () => ({ kind: 'success', removed: { id: 8, vehicle_id: 7, deleted: true }, deadline: stamp() }),
  }
  const api = {}
  for (const [name, key] of Object.entries({ listServices: 'list', getService: 'detail', createService: 'create', updateService: 'update', removeService: 'remove' })) {
    api[name] = (...args) => { calls[key].push(args); return (overrides[name] ?? defaults[name])(...args) }
  }
  const store = (mode === 'record' ? createServiceRecordStore : createServiceHistoryStore)(session, api, clock)
  return { store, session, calls }
}
export async function loaded(mode = 'record', overrides, clock) {
  const f = await fixture(mode, overrides, clock)
  await f.store.load('7', mode === 'record' ? '8' : null)
  return f
}
