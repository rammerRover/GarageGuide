import { createVehicle, listVehicles } from './api.js'

const initial = () => ({ status: 'idle', vehicles: [], errors: {}, message: '', pending: false, focusVersion: 0 })

export function createVehicleStore(authenticatedRequest, api = { createVehicle, listVehicles }) {
  let state = initial()
  let active = null
  const listeners = new Set()
  const publish = (changes) => {
    state = { ...state, ...changes }
    for (const listener of listeners) listener()
  }
  const cancel = () => { active?.abort(); active = null }

  async function run(kind, details) {
    if (kind === 'create' && state.pending) return { kind: 'cancelled' }
    cancel()
    const request = new AbortController()
    active = request
    publish({ status: 'loading', pending: true, vehicles: [], errors: {}, message: '' })
    let result
    try {
      result = await authenticatedRequest(
        (signal) => kind === 'create' ? api.createVehicle(details, signal) : api.listVehicles(signal), request.signal,
      )
    } catch {
      result = { kind: 'unexpected', message: "We couldn't confirm the request. Check your garage before submitting again." }
    }
    if (active !== request || request.signal.aborted) return { kind: 'cancelled' }
    active = null
    if (result.kind === 'cancelled' || result.kind === 'guest' || result.kind === 'authentication-unavailable') {
      publish({ pending: false, status: 'idle', vehicles: [] })
    } else if (result.kind === 'success') {
      publish({ pending: false, status: 'success', vehicles: result.vehicles ?? [], message: kind === 'create' ? 'Vehicle created.' : '' })
    } else {
      publish({ pending: false, status: result.kind, errors: result.errors ?? {}, message: result.message, focusVersion: state.focusVersion + 1 })
    }
    return result
  }

  return {
    getSnapshot: () => state,
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener) },
    load: () => run('list'),
    submit: (details) => run('create', details),
    invalid(errors) { publish({ errors, status: 'invalid', message: 'Check the highlighted fields.', focusVersion: state.focusVersion + 1 }) },
    correct(name) {
      const errors = { ...state.errors }
      delete errors[name]
      publish({ errors, ...(state.status === 'invalid' ? { message: '' } : {}) })
    },
    dispose() { cancel(); state = initial() },
  }
}
