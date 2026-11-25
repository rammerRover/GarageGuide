import { useEffect, useRef, useState, useSyncExternalStore } from 'react'
import { Link, useParams } from 'react-router-dom'
import { describeMaintenanceLimit, maintenanceReminders, maintenanceTriggers, readingTimestampWarnings, statusLabels } from './maintenanceStatus.js'
import { createScheduleStore } from './scheduleState.js'
import { scheduleFields, schedulePairs } from './scheduleValidation.js'
import { useSession } from './useSession.js'

const labels = {
  name: 'Task name', interval_days: 'Interval (days)', baseline_date: 'Baseline date',
  interval_miles: 'Interval (miles)', baseline_mileage: 'Baseline mileage (miles)',
  interval_hours: 'Interval (hours)', baseline_hours: 'Baseline operating hours',
  source_notes: 'Source notes (optional)',
}
const pairLabels = ['Calendar', 'Mileage', 'Operating hours']

export default function MaintenanceSchedulesPage() {
  const { vehicleId } = useParams()
  const { sessionStore } = useSession()
  const [resource, setResource] = useState(null)
  useEffect(() => {
    const store = createScheduleStore(sessionStore)
    setResource({ store, vehicleId })
    return () => store.dispose()
  }, [sessionStore, vehicleId])
  if (!resource || resource.vehicleId !== vehicleId) return <p role="status">Loading maintenance schedules.</p>
  return <ScheduleView store={resource.store} vehicleId={vehicleId} />
}

function ScheduleValues({ schedule }) {
  return <dl className="schedule-values">
    {schedulePairs.filter((pair) => pair.some((field) => schedule[field] !== null)).flat().map((field) =>
      <div key={field}><dt>{labels[field]}</dt><dd>{schedule[field] ?? 'Not set'}</dd></div>)}
    {schedule.source_notes !== null && <div><dt>Source notes</dt><dd>{schedule.source_notes}</dd></div>}
  </dl>
}

function ScheduleStatus({ entry, vehicle }) {
  const triggers = maintenanceTriggers(entry.limits)
  return <div className="schedule-status">
    <p><strong>{statusLabels[entry.status]}</strong></p>
    {triggers.length > 0 && <p>Triggered by {triggers.join(', ')}.</p>}
    <ul>
      {entry.limits.map((limit) => {
        const { label, status, target, remaining, savedReading, issue } = describeMaintenanceLimit(limit, entry.schedule, vehicle)
        return <li key={limit.kind}>
          <h4>{label}</h4>
          <p>{status}</p>
          <dl>
            <div><dt>Due target</dt><dd>{target}</dd></div>
            <div><dt>Remaining</dt><dd>{remaining}</dd></div>
            {savedReading && <div><dt>Last saved {label.toLowerCase()}</dt><dd>{savedReading}</dd></div>}
          </dl>
          {issue && <p className="field-hint">{issue}</p>}
        </li>
      })}
    </ul>
  </div>
}

function StatusSummary({ snapshot }) {
  const reminders = maintenanceReminders(snapshot.schedules)
  const hasReadingLimits = snapshot.schedules.some((entry) => entry.limits.some((limit) => limit.kind !== 'days'))
  const changedAt = snapshot.vehicle.readings_updated_at
  return <>
    {snapshot.schedules.length > 0 &&
      <p>Status as of <time dateTime={snapshot.as_of_date}>{snapshot.as_of_date}</time></p>}
    {hasReadingLimits && <div className="schedule-reading-advisory">
      <p><strong>Readings last changed</strong> {changedAt ?
        <time dateTime={changedAt}>{new Date(changedAt).toLocaleString()}</time> : 'Unrecorded'}</p>
      {snapshot.readings_timestamp_warning && <p>{readingTimestampWarnings[snapshot.readings_timestamp_warning]}</p>}
    </div>}
    {reminders.length > 0 && <section className="schedule-reminders" aria-labelledby="schedule-reminders-title">
      <h2 id="schedule-reminders-title">Maintenance reminders</h2>
      <ul>
        {reminders.map(({ schedule, status }) => <li key={schedule.id}>
          <button type="button" className="schedule-reminder-link"
            onClick={() => document.getElementById(`schedule-heading-${schedule.id}`)?.focus()}>{schedule.name}</button>
          <span>{statusLabels[status]}</span>
        </li>)}
      </ul>
    </section>}
  </>
}

function ScheduleField({ field, state, store, inputs }) {
  const id = `schedule-${field}`
  const error = state.errors[field]
  const props = {
    id, name: field, value: state.draft[field],
    onChange: (event) => store.change(field, event.target.value),
    ref: (node) => { inputs.current[field] = node },
    'aria-invalid': Boolean(error), 'aria-describedby': error ? `${id}-error` : undefined,
  }
  const reading = ['interval_miles', 'interval_hours', 'baseline_mileage', 'baseline_hours'].includes(field)
  return <div className="form-field">
    <label htmlFor={id}>{labels[field]}</label>
    {field === 'source_notes' ? <textarea {...props} rows={3} /> :
      <input {...props} type={field === 'baseline_date' ? 'date' : 'text'} required={field === 'name'}
        inputMode={reading ? 'decimal' : field === 'interval_days' ? 'numeric' : undefined} />}
    {error && <p id={`${id}-error`} className="field-error">{error}</p>}
  </div>
}

function ScheduleView({ store, vehicleId }) {
  const state = useSyncExternalStore(store.subscribe, store.getSnapshot)
  const heading = useRef(null)
  const feedback = useRef(null)
  const reviewHeading = useRef(null)
  const inputs = useRef({})
  const focused = useRef(0)
  useEffect(() => {
    heading.current?.focus()
    void store.load(vehicleId)
    const depart = () => store.depart()
    window.addEventListener('pagehide', depart)
    return () => { store.depart(); window.removeEventListener('pagehide', depart) }
  }, [store, vehicleId])
  useEffect(() => {
    if (state.pending || state.focusVersion === focused.current) return
    focused.current = state.focusVersion
    const first = scheduleFields.find((field) => state.errors[field])
    const target = first ? inputs.current[first] : state.review?.length ? reviewHeading.current : feedback.current
    target?.focus()
  }, [state.pending, state.focusVersion, state.review, state.errors])

  function startEdit(id) {
    if (store.beginEdit(id)) requestAnimationFrame(() => inputs.current.name?.focus())
  }

  const statusById = new Map(state.statusSnapshot?.schedules.map((entry) => [entry.schedule.id, entry]))
  const pendingMessage = state.status === 'saving' ? 'Saving schedule.' :
    state.saveConfirmation ? 'Refreshing maintenance status.' : 'Loading schedules.'

  return <section aria-labelledby="schedule-page-title">
    <div className="intro">
      <h1 id="schedule-page-title" ref={heading} tabIndex={-1}>Maintenance schedules</h1>
      <Link to={state.vehicle ? `/vehicles/${state.vehicle.id}` : '/vehicles'}>{state.vehicle ? 'Back to vehicle' : 'Back to garage'}</Link>
      {state.vehicle && <p>{state.vehicle.year} {state.vehicle.make} {state.vehicle.model}</p>}
    </div>
    <p className="form-status" ref={feedback} tabIndex={-1} role="status" aria-atomic="true">
      {[state.saveConfirmation, state.pending ? pendingMessage : state.message].filter(Boolean).join(' ')}
    </p>
    {state.vehicle && <>
      {state.statusSnapshot && <StatusSummary snapshot={state.statusSnapshot} />}
      <h2 className="schedule-section-title">Saved schedules</h2>
      {state.schedules.length === 0 ? <p>No maintenance schedules yet.</p> :
        <ul className="vehicle-list schedule-list">{state.schedules.map((schedule) =>
          <li key={schedule.id} className="vehicle-card">
            <h3 id={`schedule-heading-${schedule.id}`} tabIndex={-1}>{schedule.name}</h3>
            {statusById.has(schedule.id) && <ScheduleStatus entry={statusById.get(schedule.id)} vehicle={state.vehicle} />}
            <ScheduleValues schedule={schedule} />
            <button type="button" disabled={state.pending || state.uncertain}
              aria-label={`Edit ${schedule.name}, task ${schedule.id}`} onClick={() => startEdit(schedule.id)}>Edit</button>
          </li>)}</ul>}
      <form noValidate className="registration schedule-form" aria-labelledby="schedule-editor-title"
        onSubmit={(event) => { event.preventDefault(); void store.submit() }}>
        <h2 id="schedule-editor-title">{state.saved ? `Edit ${state.saved.name}` : 'Add a schedule'}</h2>
        <p id="schedule-interval-hint">Fill in both fields to enable an interval. Clear both to disable it. Keep at least one interval.</p>
        <fieldset disabled={state.pending}>
          <legend className="visually-hidden">Schedule details</legend>
          <ScheduleField field="name" state={state} store={store} inputs={inputs} />
          {schedulePairs.map(([interval, baseline], index) => {
            const current = index === 1 ? state.vehicle.mileage : state.vehicle.operating_hours
            return <fieldset className="schedule-pair" key={interval} aria-describedby="schedule-interval-hint">
              <legend>{pairLabels[index]}</legend>
              <ScheduleField field={interval} state={state} store={store} inputs={inputs} />
              <ScheduleField field={baseline} state={state} store={store} inputs={inputs} />
              {index > 0 && <div>
                <p className="field-hint">{index === 1 ? 'Last saved mileage' : 'Last saved operating hours'}: {current ?? 'Not recorded'}</p>
                <button type="button" disabled={current === null}
                  onClick={() => { store.copyReading(baseline); inputs.current[baseline]?.focus() }}>
                  {index === 1 ? 'Copy current mileage' : 'Copy current hours'}
                </button>
              </div>}
            </fieldset>
          })}
          <ScheduleField field="source_notes" state={state} store={store} inputs={inputs} />
          <div className="profile-actions">
            <button type="submit" disabled={state.uncertain || Boolean(state.review?.length)}>Save schedule</button>
            {state.saved && <button type="button" disabled={state.uncertain} onClick={() => {
              if (store.clearDraft()) inputs.current.name?.focus()
            }}>Cancel edit</button>}
          </div>
        </fieldset>
      </form>
    </>}
    {state.review?.length > 0 && <>
      <section className="session-panel schedule-review" aria-labelledby="schedule-review-title">
        <h2 id="schedule-review-title" ref={reviewHeading} tabIndex={-1}>Review matching schedules</h2>
        <p>Open a match to replace this draft, or keep the draft and save it as a separate task.</p>
        <ul>{state.review.map((match) => <li key={match.id}>
          <h3>{match.name} (task {match.id})</h3>
          <ScheduleValues schedule={match} />
          <button type="button" onClick={() => startEdit(match.id)} aria-label={`Open ${match.name}, task ${match.id}`}>Open schedule</button>
        </li>)}</ul>
        <button type="button" onClick={() => { void store.saveSeparate() }}>Save as separate task</button>
      </section>
    </>}
    {!state.pending && !['idle', 'invalid-address'].includes(state.status) &&
      <div className="profile-actions">
        <button type="button" onClick={() => { void store.reload() }}>
          {state.refreshFailed ? 'Retry status refresh' : state.vehicle ? 'Reload saved schedules' : 'Try again'}
        </button>
        {state.uncertain && state.inspected && <button type="button" onClick={() => store.acknowledgeInspection()}>
          I reviewed the saved schedules
        </button>}
      </div>}
  </section>
}
