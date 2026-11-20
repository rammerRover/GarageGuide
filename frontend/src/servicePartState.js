import { addServicePart, listServiceParts, lookupServicePart, removeServicePart, uncertainPartMessages } from './api.js'
import { parseSessionDeadline } from './sessionDeadline.js'
import { isServiceId } from './serviceValidation.js'
import { isVehicleId } from './vehicleValidation.js'
import {
  catalogConflictMessage, isCatalogPreview, isPartList, isPartRemoval, isPartSnapshot,
  isServicePartId, matchesPartInput, partDraft, partFields, preparePartInput, preparePartLookup,
} from './servicePartValidation.js'

export const partRemovalWarning = 'Remove only this saved part snapshot? The service and catalog entry will remain. This cannot be undone.'
export const partReloadWarning = 'Reload saved parts? Your temporary entry will be retained, but the reviewed catalog preview will be cleared.'
const refreshWarning = 'The change committed, but saved parts could not be reloaded. Reload and inspect the list before another change.'
const empty = (vehicleId = null, serviceId = null, authenticationGeneration = null) => ({
  vehicleId, serviceId, authenticationGeneration, requestGeneration: 0, source: 'manual',
  parts: [], draft: partDraft(), lookupPair: { manufacturer: '', part_number: '' }, preview: null,
  loaded: false, pending: false, status: 'idle', errors: {}, message: '', focusVersion: 0,
  confirmation: null, reloadPrompt: false, refreshRequired: false, lastMutation: null,
  uncertainOperation: null, uncertainSnapshotId: null, inspected: false,
})
const same = (a, b) => a === b || Boolean(a && b && a.generation === b.generation && a.location === b.location && a.user === b.user)
const requests = { addServicePart, listServiceParts, lookupServicePart, removeServicePart }
const write = (operation) => operation === 'add' || operation === 'remove'
const failure = (operation) => ({ kind: write(operation) ? 'uncertain' : 'unexpected', uncertain: write(operation),
  message: uncertainPartMessages[operation] ?? 'Service parts could not be loaded. Please try again.' })

export function createServicePartsStore(session, api = requests, now = Date.now) {
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
  const usable = () => !disposed && !departed && bound && isVehicleId(state.vehicleId) && isServiceId(state.serviceId)
  const validResult = (result, request) => {
    if (request.operation === 'load') return isPartList({ vehicle_id: Number(request.vehicleId), service_record_id: Number(request.serviceId), parts: result.parts }, request.vehicleId, request.serviceId)
    if (request.operation === 'lookup') return isCatalogPreview(result.preview) &&
      result.preview.manufacturer === request.details.manufacturer && result.preview.part_number === request.details.part_number
    if (request.operation === 'remove') return isPartRemoval(result.removed, request.serviceId, request.snapshotId)
    return matchesPartInput(result.part, request.details) && String(result.part.service_record_id) === request.serviceId
  }

  async function run(operation) {
    synchronize()
    if (!usable()) {
      if (!disposed && !departed && session.getSnapshot().status === 'authenticated' && Date.parse(session.getSnapshot().expires_at) <= now()) {
        await session.authenticatedRequest(async () => ({ kind: 'cancelled' }))
      }
      return { kind: 'cancelled' }
    }
    if (state.pending || (operation !== 'load' && !state.loaded) ||
        (write(operation) && (state.refreshRequired || state.uncertainOperation)) ||
        (operation === 'remove' && !state.confirmation)) return { kind: 'cancelled' }
    let prepared
    if (operation === 'lookup') prepared = preparePartLookup(state.lookupPair)
    if (operation === 'add') prepared = preparePartInput(state.source === 'manual' ? { source: 'manual', ...state.draft } :
      { source: 'catalog', preview: state.preview, quantity: state.draft.quantity, notes: state.draft.notes })
    if (prepared?.invalid) {
      const result = { kind: 'invalid', errors: prepared.errors, message: 'Check the highlighted fields.' }
      publish({ status: 'invalid', errors: result.errors, message: result.message, focusVersion: state.focusVersion + 1 })
      return result
    }
    cancel()
    const request = { operation, controller: new AbortController(), generation, vehicleId: state.vehicleId, serviceId: state.serviceId,
      context: bound, details: prepared?.details, snapshotId: state.confirmation }
    active = request
    publish({ pending: true, status: operation === 'load' ? 'loading' : 'working', errors: {}, message: '',
      confirmation: null, reloadPrompt: false, ...(operation === 'lookup' ? { preview: null } : {}) })
    let result
    try {
      result = await session.authenticatedRequest(async (signal) => {
        const received = operation === 'load' ? await api.listServiceParts(request.vehicleId, request.serviceId, signal) :
          operation === 'lookup' ? await api.lookupServicePart(request.vehicleId, request.serviceId, request.details, signal) :
            operation === 'add' ? await api.addServicePart(request.vehicleId, request.serviceId, request.details, signal) :
              await api.removeServicePart(request.vehicleId, request.serviceId, request.snapshotId, true, signal)
        if (!current(request)) return { kind: 'cancelled' }
        if (received.kind !== 'success') return received
        if (!validResult(received, request)) return failure(operation)
        const latest = session.getSnapshot().expires_at
        const deadline = parseSessionDeadline(received.deadline)
        return { ...received, deadline: deadline && Date.parse(deadline) > now() && Date.parse(deadline) > Date.parse(latest) ? deadline : latest }
      }, request.controller.signal)
    } catch { result = failure(operation) }
    if (!current(request)) { synchronize(); return { kind: 'cancelled' } }
    active = null
    if (result.kind === 'success') {
      if (write(operation)) {
        publish({ pending: false, status: 'saved', refreshRequired: true, lastMutation: operation,
          ...(operation === 'add' ? { draft: partDraft(), preview: null } : { parts: state.parts.filter((part) => String(part.id) !== request.snapshotId) }),
          message: operation === 'add' ? 'Part snapshot added.' : 'Part snapshot removed.' })
        await run('load')
        return !disposed && !departed && same(request.context, context()) && state.vehicleId === request.vehicleId &&
          state.serviceId === request.serviceId && state.lastMutation === operation ? result : { kind: 'cancelled' }
      }
      if (operation === 'lookup') {
        publish({ pending: false, preview: { ...result.preview }, status: 'review', message: 'Review these exact catalog details before adding the part.', focusVersion: state.focusVersion + 1 })
      } else {
        const uncertain = state.uncertainOperation
        const absent = uncertain === 'remove' && !result.parts.some((part) => String(part.id) === state.uncertainSnapshotId)
        publish({ pending: false, parts: result.parts, loaded: true, status: 'ready', refreshRequired: false,
          inspected: Boolean(uncertain), ...(uncertain === 'remove' ? { uncertainOperation: null, uncertainSnapshotId: null } : {}),
          message: uncertain === 'add' ? uncertainPartMessages.add : uncertain === 'remove' ? absent
            ? 'The snapshot is currently absent. This does not prove which request removed it.'
            : 'The snapshot is still present. Review it and confirm removal again if you choose.' :
              state.lastMutation === 'add' ? 'Part snapshot added. Saved parts reloaded.' : state.lastMutation === 'remove' ? 'Part snapshot removed. Saved parts reloaded.' : '',
          focusVersion: state.focusVersion + 1 })
      }
    } else if (result.kind === 'not-found') {
      publish({ ...empty(state.vehicleId, state.serviceId, state.authenticationGeneration), status: 'not-found',
        refreshRequired: state.refreshRequired, uncertainOperation: state.uncertainOperation, uncertainSnapshotId: state.uncertainSnapshotId,
        message: state.uncertainOperation ? `${uncertainPartMessages[state.uncertainOperation]} ${result.message}` : result.message,
        focusVersion: state.focusVersion + 1 })
    } else if (['guest', 'authentication-unavailable'].includes(result.kind)) {
      clear()
    } else if (result.kind === 'stale-preview' || result.kind === 'catalog-missing') {
      publish({ pending: false, preview: null, status: result.kind, errors: {},
        message: result.kind === 'stale-preview' ? catalogConflictMessage : result.message, focusVersion: state.focusVersion + 1 })
    } else if (result.kind === 'snapshot-missing') {
      publish({ pending: false, confirmation: null, refreshRequired: true, status: 'refresh-required',
        message: result.message, focusVersion: state.focusVersion + 1 })
    } else {
      const uncertain = write(operation) && (result.uncertain || ['uncertain', 'network', 'unexpected', 'cancelled', 'unavailable'].includes(result.kind))
      publish({ pending: false, status: uncertain ? 'uncertain' : result.kind, errors: result.errors ?? {},
        uncertainOperation: uncertain ? operation : state.uncertainOperation,
        uncertainSnapshotId: uncertain && operation === 'remove' ? request.snapshotId : state.uncertainSnapshotId,
        inspected: uncertain ? false : state.inspected,
        message: uncertain ? uncertainPartMessages[operation] : state.refreshRequired ? refreshWarning : result.message ?? '',
        focusVersion: state.focusVersion + 1 })
    }
    return result
  }

  return {
    getSnapshot: () => state,
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener) },
    load(vehicleId, serviceId) {
      if (disposed) return Promise.resolve({ kind: 'cancelled' })
      if (!departed && state.vehicleId === vehicleId && state.serviceId === serviceId && (state.loaded || state.uncertainOperation)) return Promise.resolve({ kind: 'cancelled' })
      departed = false
      clear(isVehicleId(vehicleId) ? vehicleId : null, isServiceId(serviceId) ? serviceId : null)
      if (!isVehicleId(vehicleId) || !isServiceId(serviceId)) {
        publish({ status: 'invalid', message: 'Check the record address.' })
        return Promise.resolve({ kind: 'invalid' })
      }
      return run('load')
    },
    chooseSource(source) {
      synchronize()
      if (!usable() || state.pending || state.uncertainOperation || !['manual', 'catalog'].includes(source)) return false
      publish({ source, preview: null, confirmation: null, errors: {}, message: '' })
      return true
    },
    edit(field, value) {
      synchronize()
      if (!usable() || state.pending || !partFields.includes(field) || (state.source === 'catalog' && !['quantity', 'notes'].includes(field))) return false
      const errors = { ...state.errors }; delete errors[field]
      publish({ draft: { ...state.draft, [field]: value }, errors, confirmation: null })
      return true
    },
    editLookup(field, value) {
      synchronize()
      if (!usable() || !['manufacturer', 'part_number'].includes(field) || (state.pending && active?.operation !== 'lookup')) return false
      if (state.pending) cancel()
      const errors = { ...state.errors }; delete errors[field]; delete errors.preview
      publish({ lookupPair: { ...state.lookupPair, [field]: value }, preview: null, pending: false, confirmation: null, errors, status: 'ready', message: '' })
      return true
    },
    lookup() { return state.source === 'catalog' ? run('lookup') : Promise.resolve({ kind: 'cancelled' }) },
    submit() { return run('add') },
    requestRemoval(snapshotId) {
      synchronize()
      if (!usable() || state.pending || state.refreshRequired || state.uncertainOperation || !isServicePartId(snapshotId) ||
          !state.parts.some((part) => isPartSnapshot(part) && String(part.id) === snapshotId)) return false
      publish({ confirmation: snapshotId, message: partRemovalWarning, focusVersion: state.focusVersion + 1 })
      return true
    },
    cancelRemoval() { if (!disposed && !state.pending) publish({ confirmation: null, message: '' }) },
    confirmRemoval() { return run('remove') },
    requestReload() {
      synchronize()
      if (!usable() || state.pending) return false
      publish({ reloadPrompt: true, message: state.uncertainOperation ? uncertainPartMessages[state.uncertainOperation] : partReloadWarning })
      return true
    },
    cancelReload() { if (!disposed && !state.pending) publish({ reloadPrompt: false }) },
    reload() {
      if (disposed || !state.reloadPrompt || state.pending) return Promise.resolve({ kind: 'cancelled' })
      publish({ reloadPrompt: false, confirmation: null, preview: null })
      return run('load')
    },
    acknowledgeAddRisk() {
      synchronize()
      if (!usable() || state.pending || state.uncertainOperation !== 'add' || !state.inspected) return false
      publish({ uncertainOperation: null, inspected: false, message: 'Another submission can create a duplicate even after an empty reload. This acknowledgment does not submit a request.' })
      return true
    },
    depart() { departed = true; clear(null, null) },
    dispose() { if (!disposed) { clear(null, null); disposed = true; unsubscribe(); listeners.clear() } },
  }
}
