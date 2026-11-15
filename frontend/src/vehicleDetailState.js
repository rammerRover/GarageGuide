import { getVehicle, updateVehicle, uncertainVehicleUpdate } from './api.js'
import { parseSessionDeadline } from './sessionDeadline.js'
import {
  isPublicVehicle, isVehicleId, parseReadingConfirmation, prepareVehiclePatch, vehicleDraft,
  vehicleFields, vehicleIdMessage,
} from './vehicleValidation.js'

export const vehicleReloadWarning = 'Reloading discards your unsaved changes and reading confirmation. Reload this vehicle?'
const reviewMessage = 'Reload this vehicle and review its current values before saving again.'
const initial = (vehicleId = null, authenticationGeneration = null) => ({
  vehicleId, authenticationGeneration, requestGeneration: 0, status: 'idle',
  vehicle: null, draft: {}, editing: false, confirmation: null, pending: false,
  errors: {}, message: '', reloadRequired: false, reloadPrompt: false, focusVersion: 0,
})
const sameContext = (a, b) => a === b || Boolean(a && b &&
  a.generation === b.generation && a.location === b.location && a.user === b.user)

// The page supplies the existing session store without duplicating session policy.
export function createVehicleDetailStore(session, api = { getVehicle, updateVehicle }, now = Date.now) {
  let state = initial()
  let active = null
  let generation = 0
  let disposed = false
  let departed = false
  const listeners = new Set()
  const context = () => {
    const snapshot = session.getSnapshot()
    return snapshot.status === 'authenticated' && snapshot.visible && !snapshot.busy &&
      snapshot.checkedFor !== null && Number.isSafeInteger(snapshot.generation) && snapshot.user &&
      parseSessionDeadline(snapshot.expires_at) && Date.parse(snapshot.expires_at) > now()
      ? { generation: snapshot.generation, location: snapshot.checkedFor, user: snapshot.user.id } : null
  }
  let bound = context()
  const publish = (changes) => {
    state = { ...state, ...changes, requestGeneration: generation }
    for (const listener of listeners) listener()
  }
  const cancel = () => { active?.controller.abort(); active = null; generation += 1 }
  const clear = (vehicleId = state.vehicleId) => {
    cancel()
    publish({ ...initial(vehicleId, session.getSnapshot().generation), status: bound ? 'idle' : 'gated' })
  }
  const synchronize = () => {
    const next = context()
    if (sameContext(bound, next)) return
    bound = next
    clear()
  }
  const unsubscribe = session.subscribe(synchronize)
  const current = (request) => !disposed && !departed && active === request &&
    !request.controller.signal.aborted && request.generation === generation &&
    request.vehicleId === state.vehicleId && sameContext(request.context, context())
  const failedResponse = (mutation) => ({
    kind: mutation ? 'uncertain' : 'unexpected', uncertain: mutation,
    message: mutation ? uncertainVehicleUpdate : "We couldn't confirm the vehicle response. Please try again.",
  })

  async function run(mutation, confirmation) {
    synchronize()
    if (disposed || departed || !isVehicleId(state.vehicleId)) return { kind: 'cancelled' }
    if (!bound) {
      // Let the existing expiry check clear identity without invoking a data API.
      const snapshot = session.getSnapshot()
      if (snapshot.status === 'authenticated' && Date.parse(snapshot.expires_at) <= now()) {
        await session.authenticatedRequest(async () => ({ kind: 'cancelled' }))
      }
      return { kind: 'cancelled' }
    }
    if (mutation && (state.pending || !state.vehicle || !state.editing || state.reloadRequired)) return { kind: 'cancelled' }
    const committed = state.vehicle
    const draft = { ...state.draft }
    const prepared = mutation ? prepareVehiclePatch(committed, draft, confirmation) : null
    if (prepared?.invalid || prepared?.unchanged) {
      const result = prepared.invalid
        ? { kind: 'invalid', errors: prepared.errors, message: 'Check the highlighted fields.' }
        : { kind: 'unchanged', errors: {}, message: 'No changes to save.' }
      publish({ status: result.kind, errors: result.errors, message: result.message, focusVersion: state.focusVersion + 1 })
      return result
    }
    cancel()
    const request = { controller: new AbortController(), generation, vehicleId: state.vehicleId, context: bound }
    active = request
    publish({ status: mutation ? 'saving' : 'loading', pending: true, errors: {}, message: '', confirmation: null, reloadPrompt: false })
    let result
    try {
      result = await session.authenticatedRequest(async (signal) => {
        const received = mutation
          ? await api.updateVehicle(request.vehicleId, committed, draft, confirmation, signal)
          : await api.getVehicle(request.vehicleId, signal)
        if (!current(request)) return { kind: 'cancelled' }
        if (received.kind !== 'success') return received
        if (!isPublicVehicle(received.vehicle) || String(received.vehicle.id) !== request.vehicleId) return failedResponse(mutation)
        const deadline = parseSessionDeadline(received.deadline)
        const latest = session.getSnapshot().expires_at
        if (!deadline || Date.parse(deadline) <= now() || Date.parse(deadline) < Date.parse(latest)) return failedResponse(mutation)
        return { ...received, deadline: Date.parse(deadline) === Date.parse(latest) ? latest : deadline }
      }, request.controller.signal)
    } catch {
      result = failedResponse(mutation)
    }
    if (!current(request)) return { kind: 'cancelled' }
    active = null
    if (result.kind === 'success') {
      publish({ vehicle: result.vehicle, draft: vehicleDraft(result.vehicle), editing: false,
        status: 'ready', pending: false, confirmation: null, reloadRequired: false,
        message: mutation ? 'Vehicle saved.' : 'Vehicle loaded.', focusVersion: state.focusVersion + 1 })
    } else if (result.kind === 'confirmation-required' && mutation) {
      const snapshot = parseReadingConfirmation({ detail: 'Reading changes require confirmation.',
        fields: result.fields, current_readings: result.currentReadings }, prepared.details)
      if (!snapshot) result = failedResponse(true)
      else {
        const needsReload = confirmation !== undefined
        publish({ pending: false, status: needsReload ? 'reload-required' : 'confirmation-required',
          confirmation: needsReload ? null : snapshot, reloadRequired: needsReload,
          message: needsReload ? reviewMessage : 'Review and confirm the reading changes.', focusVersion: state.focusVersion + 1 })
        return result
      }
    } else if (result.kind === 'not-found') {
      publish({ ...initial(state.vehicleId, state.authenticationGeneration), status: 'not-found',
        message: 'Vehicle not found.', focusVersion: state.focusVersion + 1 })
      return result
    }
    if (result.kind !== 'success') {
      const uncertain = mutation && (result.uncertain || ['network', 'uncertain', 'unexpected', 'cancelled', 'unavailable'].includes(result.kind))
      const reloadRequired = result.kind === 'reload-required' || uncertain
      publish({ pending: false, status: uncertain ? 'uncertain' : result.kind, confirmation: null,
        errors: result.errors ?? {}, reloadRequired, message: uncertain ? uncertainVehicleUpdate : result.message ?? '',
        focusVersion: state.focusVersion + 1 })
    }
    return result
  }

  return {
    getSnapshot: () => state,
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener) },
    load(vehicleId) {
      if (disposed) return Promise.resolve({ kind: 'cancelled' })
      if (!isVehicleId(vehicleId)) {
        clear(null)
        publish({ status: 'invalid', errors: { vehicle_id: vehicleIdMessage }, message: 'Check the vehicle ID.' })
        return Promise.resolve({ kind: 'invalid' })
      }
      if (state.vehicleId === vehicleId && state.vehicle) return Promise.resolve({ kind: 'cancelled' })
      departed = false
      clear(vehicleId)
      return run(false)
    },
    beginEdit() {
      synchronize()
      if (disposed || !bound || !state.vehicle || state.pending || state.reloadRequired) return false
      if (!state.editing) publish({ editing: true, draft: vehicleDraft(state.vehicle), status: 'editing', errors: {}, message: '' })
      return true
    },
    edit(name, value) {
      synchronize()
      if (disposed || !bound || !state.editing || state.pending || !vehicleFields.includes(name)) return false
      if (state.draft[name] === value) return true
      const errors = { ...state.errors }
      delete errors[name]
      delete errors.reading_confirmation
      publish({ draft: { ...state.draft, [name]: value }, errors, confirmation: null, reloadPrompt: false,
        status: state.reloadRequired ? 'reload-required' : 'editing', message: state.reloadRequired ? reviewMessage : '' })
      return true
    },
    submit() {
      if (state.confirmation) return Promise.resolve({ kind: 'cancelled' })
      return run(true)
    },
    confirm() {
      if (!state.confirmation || state.pending || state.reloadRequired) return Promise.resolve({ kind: 'cancelled' })
      return run(true, { ...state.confirmation.currentReadings })
    },
    cancelConfirmation() {
      if (state.pending || disposed) return
      publish({ confirmation: null, status: state.reloadRequired ? 'reload-required' : 'editing', message: state.reloadRequired ? reviewMessage : '' })
    },
    cancelEdit() {
      if (state.pending || disposed || !state.vehicle) return
      publish({ draft: vehicleDraft(state.vehicle), editing: false, errors: {}, confirmation: null,
        status: state.reloadRequired ? 'reload-required' : 'ready', message: state.reloadRequired ? reviewMessage : '' })
    },
    requestReload() {
      synchronize()
      if (disposed || !bound || !isVehicleId(state.vehicleId) || state.pending) return false
      publish({ reloadPrompt: true, message: vehicleReloadWarning })
      return true
    },
    cancelReload() {
      if (!state.reloadPrompt || disposed) return
      publish({ reloadPrompt: false, message: state.reloadRequired ? reviewMessage : '' })
    },
    reload() {
      if (disposed || !state.reloadPrompt || state.pending) return Promise.resolve({ kind: 'cancelled' })
      clear()
      return run(false)
    },
    depart() { departed = true; clear(null) },
    dispose() {
      if (disposed) return
      clear(null)
      disposed = true
      unsubscribe()
      listeners.clear()
    },
  }
}
