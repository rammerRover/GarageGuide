import {
  createMaintenanceSchedule, getMaintenanceStatus, uncertainScheduleSave, updateMaintenanceSchedule,
} from './api.js'
import { parseSessionDeadline } from './sessionDeadline.js'
import { prepareScheduleInput, scheduleDraft, scheduleFields } from './scheduleValidation.js'
import { isVehicleId, vehicleIdMessage } from './vehicleValidation.js'

const defaultApi = { getMaintenanceStatus, createMaintenanceSchedule, updateMaintenanceSchedule }
const empty = (vehicleId = null) => ({
  vehicleId, vehicle: null, schedules: [], saved: null, draft: scheduleDraft(),
  statusSnapshot: null, saveConfirmation: '', refreshFailed: false,
  status: 'idle', pending: false, review: null, uncertain: false, inspected: false,
  message: '', errors: {}, focusVersion: 0,
})
const sameContext = (first, second) => first === second || Boolean(first && second &&
  first.generation === second.generation && first.location === second.location && first.user === second.user)

export function createScheduleStore(session, api = defaultApi, now = Date.now) {
  let state = empty(), active = null, disposed = false, departed = false
  const listeners = new Set()
  const context = () => {
    const value = session.getSnapshot()
    return value.status === 'authenticated' && value.visible && !value.busy && value.checkedFor !== null &&
      value.user && Date.parse(value.expires_at) > now()
      ? { generation: value.generation, location: value.checkedFor, user: value.user.id } : null
  }
  let bound = context()
  const publish = (changes) => {
    state = { ...state, ...changes }
    for (const listener of listeners) listener()
  }
  const feedback = (changes) => publish({ pending: false, focusVersion: state.focusVersion + 1, ...changes })
  function clear(vehicleId = state.vehicleId) {
    active?.abort()
    active = null
    publish(empty(vehicleId))
  }
  function synchronize() {
    const next = context()
    if (!sameContext(bound, next)) { bound = next; clear() }
  }
  const unsubscribe = session.subscribe(synchronize)
  function ready() {
    synchronize()
    return !disposed && !departed && bound && !active && isVehicleId(state.vehicleId)
  }

  async function run(operation, details, scheduleId) {
    const { vehicleId } = state
    const controller = new AbortController(), started = bound
    const current = () => !disposed && !departed && active === controller && !controller.signal.aborted && sameContext(started, context())
    const loading = operation === 'load'
    active = controller
    publish({ pending: true, status: loading ? 'loading' : 'saving', message: '', errors: {}, review: null,
      ...(loading ? { statusSnapshot: null, refreshFailed: false } : { saveConfirmation: '' }) })
    const result = await session.authenticatedRequest(async (signal) => {
      const reply = loading ? await api.getMaintenanceStatus(vehicleId, signal)
        : scheduleId === null
          ? await api.createMaintenanceSchedule(vehicleId, details, signal)
          : await api.updateMaintenanceSchedule(vehicleId, scheduleId, details, signal)
      if (signal.aborted || !current()) return { kind: 'cancelled' }
      if (reply.kind !== 'success') return reply
      const deadline = parseSessionDeadline(reply.deadline)
      const latest = session.getSnapshot().expires_at
      // Ignore missing, stale, invalid, or expired headers for the current request.
      return { ...reply, deadline: deadline && Date.parse(deadline) > Date.parse(latest) ? deadline : latest }
    }, controller.signal)
    if (!current()) { synchronize(); return { kind: 'cancelled' } }
    active = null

    if (result.kind === 'success' && loading) {
      const snapshot = result.snapshot
      const schedules = snapshot.schedules.map((entry) => entry.schedule)
      const saved = state.saved && (schedules.find((item) => item.id === state.saved.id) ?? null)
      const missing = state.saved && !saved
      feedback({ status: 'ready', vehicle: snapshot.vehicle, schedules, saved,
        statusSnapshot: snapshot, inspected: state.uncertain,
        draft: missing ? scheduleDraft() : state.draft,
        message: missing ? 'The schedule you were editing is no longer available.' : state.uncertain
          ? 'Schedules reloaded. Compare the saved values with your draft.'
          : state.saveConfirmation ? '' : 'Schedules loaded.' })
    } else if (result.kind === 'success') {
      const byId = new Map(state.schedules.map((item) => [item.id, item]))
      byId.set(result.schedule.id, result.schedule)
      publish({ status: 'ready', statusSnapshot: null, schedules: [...byId.values()].sort((a, b) => a.id - b.id),
        saved: null, draft: scheduleDraft(), saveConfirmation: scheduleId === null ? 'Schedule created.' : 'Schedule saved.' })
      if (ready() && state.vehicleId === vehicleId && sameContext(started, bound)) await run('load')
    } else if (result.kind === 'duplicate') {
      feedback({ status: 'duplicate', review: result.matches, message: result.matches.length
        ? 'Review the current matches before saving.' : 'No matching schedules remain. Review your draft and choose Save schedule again.' })
    } else if (result.kind === 'not-found') {
      feedback({ ...empty(vehicleId), focusVersion: state.focusVersion + 1, status: 'not-found', message: result.message,
        saveConfirmation: state.saveConfirmation, refreshFailed: Boolean(loading && state.saveConfirmation) })
    } else if (!loading && ['uncertain', 'network', 'unexpected', 'cancelled', 'unavailable'].includes(result.kind)) {
      feedback({ status: 'uncertain', uncertain: true, inspected: false, message: uncertainScheduleSave })
    } else if (loading && state.saveConfirmation) {
      feedback({ status: result.kind, refreshFailed: true, message: 'Maintenance status could not be refreshed.' })
    } else {
      feedback({ status: result.kind, errors: result.errors ?? {}, message: result.message ?? 'Please try again.' })
    }
    return result
  }

  function change(field, value) {
    if (!ready() || !state.vehicle || !scheduleFields.includes(field) || state.draft[field] === value) return false
    publish({ draft: { ...state.draft, [field]: value }, review: null, errors: {},
      ...(state.uncertain || state.refreshFailed ? {} : { message: '', status: 'ready', saveConfirmation: '' }) })
    return true
  }

  function submit(separate = false) {
    if (!ready() || !state.vehicle || state.uncertain || separate !== Boolean(state.review?.length)) return
    const { details, errors, invalid, unchanged } = prepareScheduleInput(state.draft, state.saved)
    if (invalid || unchanged) {
      feedback({ status: invalid ? 'invalid' : 'ready', errors, message: invalid ? 'Check the highlighted fields.' : 'No changes to save.' })
      return
    }
    if (separate) details.reviewed_duplicate_ids = state.review.map((item) => item.id)
    return run('save', details, state.saved ? String(state.saved.id) : null)
  }

  return {
    getSnapshot: () => state,
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener) },
    load(vehicleId) {
      if (disposed) return
      departed = false
      clear(vehicleId)
      if (!isVehicleId(vehicleId)) { feedback({ status: 'invalid-address', message: vehicleIdMessage }); return }
      if (ready()) return run('load')
    },
    reload() {
      if (ready()) {
        if (state.uncertain) publish({ inspected: false })
        if (!state.refreshFailed) publish({ saveConfirmation: '' })
        return run('load')
      }
    },
    change,
    copyReading(field) {
      const value = field === 'baseline_mileage' ? state.vehicle?.mileage :
        field === 'baseline_hours' ? state.vehicle?.operating_hours : null
      return typeof value === 'string' && change(field, value)
    },
    beginEdit(id) {
      if (!ready() || state.uncertain) return false
      const saved = state.review?.find((item) => item.id === id) ?? state.schedules.find((item) => item.id === id)
      if (!saved) return false
      publish({ saved, draft: scheduleDraft(saved), review: null, errors: {},
        ...(state.refreshFailed ? {} : { message: '', status: 'ready', saveConfirmation: '' }) })
      return true
    },
    clearDraft() {
      if (!ready() || state.uncertain) return false
      publish({ saved: null, draft: scheduleDraft(), review: null, errors: {},
        ...(state.refreshFailed ? {} : { message: '', status: 'ready', saveConfirmation: '' }) })
      return true
    },
    submit: () => submit(),
    saveSeparate: () => submit(true),
    acknowledgeInspection() {
      if (!ready() || !state.uncertain || !state.inspected) return false
      feedback({ uncertain: false, inspected: false, status: 'ready', message: 'You can review or clear your draft before saving.' })
      return true
    },
    depart() { departed = true; clear() },
    dispose() { disposed = true; clear(); unsubscribe(); listeners.clear() },
  }
}
