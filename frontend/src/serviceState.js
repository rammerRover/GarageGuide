import { createService, getService, listServices, removeService, uncertainServiceMessages, updateService } from './api.js'
import { parseSessionDeadline } from './sessionDeadline.js'
import { isPublicService, isServiceId, prepareServiceInput, serviceDraft, serviceFields } from './serviceValidation.js'
import { isVehicleId } from './vehicleValidation.js'

export const serviceReloadWarning = 'Reloading discards your unsaved service changes and removal confirmation. Reload and inspect the saved record?'
export const serviceRemovalWarning = 'Permanently remove this record? It may include newer concurrent edits. Linked records prevent removal. This cannot be undone.'
const createRefreshWarning = 'Service record created, but history could not be reloaded. Reload history before adding another record.'
const empty = (vehicleId = null, serviceId = null, authenticationGeneration = null) => ({
  vehicleId, serviceId, authenticationGeneration, requestGeneration: 0, status: 'idle',
  records: [], record: null, draft: serviceDraft(), editing: false, confirmation: false, loaded: false,
  pending: false, errors: {}, message: '', focusVersion: 0, reloadPrompt: false,
  uncertainOperation: null, inspected: false, created: false, historyRefreshRequired: false,
})
const same = (a, b) => a === b || Boolean(a && b && a.generation === b.generation && a.location === b.location && a.user === b.user)

// Both lifecycles share the same private-request boundary; neither owns session policy.
function createStore(mode, session, api, now) {
  let state = empty(), active = null, generation = 0, disposed = false, departed = false
  const listeners = new Set()
  const context = () => {
    const value = session.getSnapshot()
    return value.status === 'authenticated' && value.visible && !value.busy && value.checkedFor !== null &&
      Number.isSafeInteger(value.generation) && value.user && parseSessionDeadline(value.expires_at) && Date.parse(value.expires_at) > now()
      ? { generation: value.generation, location: value.checkedFor, user: value.user.id } : null
  }
  let bound = context()
  const publish = (changes) => {
    state = { ...state, ...changes, requestGeneration: generation }
    for (const listener of listeners) listener()
  }
  const cancel = () => { active?.controller.abort(); active = null; generation += 1 }
  const clear = (vehicleId = state.vehicleId, serviceId = state.serviceId) => {
    cancel()
    publish({ ...empty(vehicleId, serviceId, session.getSnapshot().generation), status: bound ? 'idle' : 'gated' })
  }
  const synchronize = () => {
    const next = context()
    if (!same(bound, next)) { bound = next; clear() }
  }
  const unsubscribe = session.subscribe(synchronize)
  const current = (request) => !disposed && !departed && active === request && request.generation === generation &&
    !request.controller.signal.aborted && request.vehicleId === state.vehicleId && request.serviceId === state.serviceId && same(request.context, context())
  const failure = (operation) => ({ kind: operation === 'load' ? 'unexpected' : 'uncertain',
    uncertain: operation !== 'load', message: uncertainServiceMessages[operation] ?? 'Service history could not be loaded. Please try again.' })
  const validResult = (result, request, operation) => {
    if (operation === 'load' && mode === 'history') return Array.isArray(result.services) &&
      result.services.every((record) => isPublicService(record) && String(record.vehicle_id) === request.vehicleId) &&
      new Set(result.services.map((record) => record.id)).size === result.services.length
    if (operation === 'remove') return result.removed && Object.keys(result.removed).length === 3 &&
      result.removed.deleted === true && String(result.removed.id) === request.serviceId && String(result.removed.vehicle_id) === request.vehicleId &&
      Number.isInteger(result.removed.id) && Number.isInteger(result.removed.vehicle_id)
    return isPublicService(result.record) && String(result.record.vehicle_id) === request.vehicleId &&
      (operation === 'create' || String(result.record.id) === request.serviceId)
  }

  async function run(operation) {
    synchronize()
    if (disposed || departed || !isVehicleId(state.vehicleId) || (mode === 'record' && !isServiceId(state.serviceId))) return { kind: 'cancelled' }
    if (!bound) {
      const snapshot = session.getSnapshot()
      if (snapshot.status === 'authenticated' && Date.parse(snapshot.expires_at) <= now()) await session.authenticatedRequest(async () => ({ kind: 'cancelled' }))
      return { kind: 'cancelled' }
    }
    const mutation = operation !== 'load'
    if (state.pending || (mutation && state.uncertainOperation) || (operation === 'create' && state.historyRefreshRequired) || (operation === 'update' && (!state.editing || !state.record)) ||
        (operation === 'remove' && (!state.confirmation || !state.record))) return { kind: 'cancelled' }
    const committed = state.record, draft = { ...state.draft }
    if (operation === 'create' || operation === 'update') {
      const prepared = prepareServiceInput(draft, operation === 'update' ? committed : null)
      if (prepared.invalid || prepared.unchanged) {
        const result = { kind: prepared.invalid ? 'invalid' : 'unchanged', errors: prepared.errors, message: prepared.invalid ? 'Check the highlighted fields.' : 'No changes to save.' }
        publish({ status: result.kind, errors: result.errors, message: result.message, focusVersion: state.focusVersion + 1 })
        return result
      }
    }
    cancel()
    const request = { controller: new AbortController(), generation, vehicleId: state.vehicleId, serviceId: state.serviceId, context: bound }
    active = request
    publish({ pending: true, status: operation === 'load' ? 'loading' : 'saving', errors: {}, message: '', reloadPrompt: false, confirmation: false,
      ...(operation === 'create' ? { created: false } : {}) })
    let result
    try {
      result = await session.authenticatedRequest(async (signal) => {
        const received = operation === 'load' ? mode === 'history'
          ? await api.listServices(request.vehicleId, signal) : await api.getService(request.vehicleId, request.serviceId, signal)
          : operation === 'create' ? await api.createService(request.vehicleId, draft, signal)
            : operation === 'update' ? await api.updateService(request.vehicleId, request.serviceId, committed, draft, signal)
              : await api.removeService(request.vehicleId, request.serviceId, true, signal)
        // Check before returning success to authenticatedRequest: stale work cannot extend the session.
        if (!current(request)) return { kind: 'cancelled' }
        if (received.kind !== 'success') return received
        if (!validResult(received, request, operation)) return failure(operation)
        const latest = session.getSnapshot().expires_at
        const deadline = parseSessionDeadline(received.deadline)
        // Preserve the current deadline for absent/malformed/older/equal/expired headers.
        return { ...received, deadline: deadline && Date.parse(deadline) > now() && Date.parse(deadline) > Date.parse(latest) ? deadline : latest }
      }, request.controller.signal)
    } catch { result = failure(operation) }
    if (!current(request)) { synchronize(); return { kind: 'cancelled' } }
    active = null
    if (result.kind === 'success') {
      if (operation === 'create') {
        publish({ pending: false, created: true, historyRefreshRequired: true, draft: serviceDraft(), status: 'created', message: 'Service record created.' })
        // This GET follows a confirmed user mutation. Its failure must not invite another POST.
        await run('load')
        return !disposed && !departed && state.created && state.vehicleId === request.vehicleId && same(request.context, context())
          ? result : { kind: 'cancelled' }
      }
      if (operation === 'remove') {
        publish({ ...empty(state.vehicleId, state.serviceId, state.authenticationGeneration), status: 'removed', message: 'Service record removed.', focusVersion: state.focusVersion + 1 })
      } else if (mode === 'history') {
        publish({ pending: false, records: result.services, loaded: true, status: 'ready', historyRefreshRequired: false,
          inspected: Boolean(state.uncertainOperation), focusVersion: state.focusVersion + 1,
          message: state.uncertainOperation ? uncertainServiceMessages.create : state.created ? 'Service record created.' : '' })
      } else {
        publish({ pending: false, record: result.record, draft: serviceDraft(result.record), editing: false, status: 'ready',
          uncertainOperation: null, inspected: false, message: operation === 'update' ? 'Service record saved.' : 'Service record loaded.', focusVersion: state.focusVersion + 1 })
      }
    } else if (result.kind === 'not-found') {
      const absentRemoval = state.uncertainOperation === 'remove'
      publish({ ...empty(state.vehicleId, state.serviceId, state.authenticationGeneration), status: 'not-found',
        created: state.historyRefreshRequired, historyRefreshRequired: state.historyRefreshRequired,
        message: absentRemoval ? 'The record is currently absent. This does not establish which request removed it.'
          : state.historyRefreshRequired ? `${createRefreshWarning} ${result.message}` : result.message, focusVersion: state.focusVersion + 1 })
    } else if (['guest', 'authentication-unavailable'].includes(result.kind)) {
      clear()
    } else {
      const uncertain = mutation && (result.uncertain || ['uncertain', 'network', 'unexpected', 'cancelled', 'unavailable', 'reload-required'].includes(result.kind))
      publish({ pending: false, status: uncertain ? 'uncertain' : result.kind, errors: result.errors ?? {},
        uncertainOperation: uncertain ? operation : state.uncertainOperation,
        message: uncertain ? uncertainServiceMessages[operation] : state.historyRefreshRequired ? createRefreshWarning : result.message ?? '',
        focusVersion: state.focusVersion + 1 })
    }
    return result
  }

  return {
    getSnapshot: () => state,
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener) },
    load(vehicleId, serviceId = null) {
      if (disposed) return Promise.resolve({ kind: 'cancelled' })
      if (state.vehicleId === vehicleId && state.serviceId === serviceId && (state.uncertainOperation || state.record || state.created)) return Promise.resolve({ kind: 'cancelled' })
      // Route loads invalidate old identity/data, even when the next ID is invalid.
      departed = false
      clear(isVehicleId(vehicleId) ? vehicleId : null, mode === 'record' && isServiceId(serviceId) ? serviceId : null)
      if (!isVehicleId(vehicleId) || (mode === 'record' && !isServiceId(serviceId))) {
        publish({ status: 'invalid', message: 'Check the record address.' })
        return Promise.resolve({ kind: 'invalid' })
      }
      return run('load')
    },
    beginEdit() {
      synchronize()
      if (disposed || departed || !bound || state.pending || !state.record || state.uncertainOperation) return false
      publish({ editing: true, draft: serviceDraft(state.record), errors: {}, message: '', confirmation: false })
      return true
    },
    edit(field, value) {
      synchronize()
      if (disposed || departed || !bound || state.pending || !serviceFields.includes(field) || (mode === 'record' && !state.editing)) return false
      const errors = { ...state.errors }; delete errors[field]
      publish({ draft: { ...state.draft, [field]: value }, confirmation: false, errors })
      return true
    },
    submit() { return run(mode === 'history' ? 'create' : 'update') },
    requestRemoval() {
      synchronize()
      if (mode !== 'record' || disposed || departed || !bound || !state.record || state.pending || state.uncertainOperation) return false
      publish({ confirmation: true, message: serviceRemovalWarning, focusVersion: state.focusVersion + 1 })
      return true
    },
    cancelRemoval() { if (!disposed && !state.pending) publish({ confirmation: false, message: '' }) },
    confirmRemoval() { return mode === 'record' ? run('remove') : Promise.resolve({ kind: 'cancelled' }) },
    cancelEdit() {
      synchronize()
      if (disposed || !bound || state.pending || !state.record) return
      publish({ editing: false, draft: serviceDraft(state.record), errors: {}, confirmation: false,
        message: state.uncertainOperation ? uncertainServiceMessages[state.uncertainOperation] : '' })
    },
    requestReload() {
      synchronize()
      if (disposed || departed || !bound || state.pending || !isVehicleId(state.vehicleId)) return false
      publish({ reloadPrompt: true, message: mode === 'record' ? serviceReloadWarning : state.uncertainOperation ? uncertainServiceMessages.create : 'Reload service history?' })
      return true
    },
    cancelReload() { if (!disposed && !state.pending) publish({ reloadPrompt: false }) },
    reload() {
      if (disposed || !state.reloadPrompt || state.pending) return Promise.resolve({ kind: 'cancelled' })
      publish({ reloadPrompt: false, confirmation: false, ...(mode === 'record' ? { record: null, draft: serviceDraft(), editing: false } : {}) })
      return run('load')
    },
    acknowledgeCreateRisk() {
      synchronize()
      if (mode !== 'history' || disposed || !bound || state.pending || state.uncertainOperation !== 'create' || !state.inspected) return false
      publish({ uncertainOperation: null, inspected: false, message: 'Resubmitting can create a duplicate even when the entry was absent after reload. Submit only if you deliberately choose to risk a duplicate.' })
      return true
    },
    depart() { departed = true; clear(null, null) },
    dispose() { if (!disposed) { clear(null, null); disposed = true; unsubscribe(); listeners.clear() } },
  }
}

const requests = { createService, getService, listServices, removeService, updateService }
export const createServiceHistoryStore = (session, api = requests, now = Date.now) => createStore('history', session, api, now)
export const createServiceRecordStore = (session, api = requests, now = Date.now) => createStore('record', session, api, now)
