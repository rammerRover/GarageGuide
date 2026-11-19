import { useEffect, useRef, useState, useSyncExternalStore } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useSession } from './useSession.js'
import { createVehicleDetailStore, vehicleReloadWarning } from './vehicleDetailState.js'
import { prepareVehiclePatch, vehicleFields } from './vehicleValidation.js'

const labels = {
  year: 'Model year', make: 'Make', model: 'Model', vehicle_type: 'Vehicle type',
  engine: 'Engine (optional)', mileage: 'Current mileage (miles)', operating_hours: 'Current operating hours',
}
const hints = {
  year: 'If changing the year, use 1886 through next calendar year. An unchanged older year is retained.',
  vehicle_type: 'Free text, for example Car, Motorcycle, Dirt bike, ATV, or RZR.',
  engine: 'Leave blank to clear the engine.',
  mileage: 'Leave blank for Not recorded. Enter 0 for confirmed zero; use at most one decimal place.',
  operating_hours: 'Leave blank for Not recorded. Enter 0 for confirmed zero; use at most one decimal place.',
}
const timestamp = (value) => value === null ? 'Not recorded' : value

export default function VehicleDetailPage() {
  const { vehicleId } = useParams()
  const { sessionStore } = useSession()
  const [resource, setResource] = useState(null)
  useEffect(() => {
    // Subscribe only after mount. Each StrictMode effect setup owns a fresh store.
    const store = createVehicleDetailStore(sessionStore)
    setResource({ store, vehicleId })
    return () => store.dispose()
  }, [sessionStore, vehicleId])
  if (!resource || resource.vehicleId !== vehicleId) return <p role="status">Loading your vehicle. Please wait.</p>
  return <VehicleDetailView store={resource.store} vehicleId={vehicleId} />
}

function VehicleDetailView({ store, vehicleId }) {
  const state = useSyncExternalStore(store.subscribe, store.getSnapshot)
  const heading = useRef(null)
  const feedback = useRef(null)
  const confirmationHeading = useRef(null)
  const reloadHeading = useRef(null)
  const inputs = useRef({})
  const editButton = useRef(null)
  const focused = useRef(0)

  useEffect(() => {
    heading.current?.focus()
    void store.load(vehicleId)
    const depart = () => store.depart()
    window.addEventListener('pagehide', depart)
    return () => {
      store.depart()
      window.removeEventListener('pagehide', depart)
    }
  }, [store, vehicleId])

  useEffect(() => {
    if (state.pending || state.focusVersion === focused.current) return
    focused.current = state.focusVersion
    const first = vehicleFields.find((name) => state.errors[name])
    const target = first ? inputs.current[first] : state.confirmation ? confirmationHeading.current : feedback.current
    target?.focus()
  }, [state.focusVersion, state.pending, state.errors, state.confirmation])

  function beginEdit() {
    if (store.beginEdit()) requestAnimationFrame(() => inputs.current.year?.focus())
  }
  function cancelEdit() {
    store.cancelEdit()
    requestAnimationFrame(() => editButton.current?.focus())
  }
  const vehicle = state.vehicle
  const prepared = vehicle && state.editing ? prepareVehiclePatch(vehicle, state.draft) : null
  const proposed = (name) => prepared?.details?.[name] ?? 'Not recorded'
  // RequireSession remounts the private subtree for every location/session generation.
  // The store also independently rejects results for old IDs and authentication.
  return (
    <section aria-labelledby="vehicle-profile-title" aria-busy={state.pending}>
      <div className="intro">
        <p className="eyebrow">Your garage</p>
        <h1 id="vehicle-profile-title" ref={heading} tabIndex={-1}>Vehicle profile.</h1>
        <Link to="/vehicles">Back to garage</Link>
      </div>
      <p className="form-status" role="status" aria-live="polite" aria-atomic="true">
        {state.pending ? state.editing ? 'Saving your vehicle. Please wait.' : 'Loading your vehicle. Please wait.' : ''}
      </p>
      <p className={`form-status ${state.status === 'ready' ? '' : 'field-error'}`}
        ref={feedback} tabIndex={-1} role="status" aria-live="polite" aria-atomic="true">{state.message}</p>
      {vehicle && !state.editing && (
        <div className="vehicle-card vehicle-profile">
          <h2>{vehicle.year} {vehicle.make} {vehicle.model}</h2>
          <p><Link to={`/vehicles/${vehicle.id}/services`}>Service history</Link></p>
          <dl>
            <div><dt>Vehicle ID</dt><dd>{vehicle.id}</dd></div>
            {vehicleFields.map((name) => <div key={name}><dt>{labels[name]}</dt><dd>{vehicle[name] ?? 'Not recorded'}</dd></div>)}
            <div><dt>Created at</dt><dd>{timestamp(vehicle.created_at)}</dd></div>
            <div><dt>Readings updated at</dt><dd>{timestamp(vehicle.readings_updated_at)}</dd></div>
          </dl>
          <button type="button" ref={editButton} disabled={state.pending || state.reloadRequired}
            onClick={beginEdit}>Edit vehicle</button>
        </div>
      )}
      {vehicle && state.editing && (
        <form className="registration vehicle-form" noValidate aria-label="Edit vehicle" aria-busy={state.pending}
          onSubmit={(event) => { event.preventDefault(); void store.submit() }}>
          <fieldset disabled={state.pending}>
            <legend>Vehicle details</legend>
            {vehicleFields.map((name) => (
              <div className="form-field" key={name}>
                <label htmlFor={`profile-${name}`}>{labels[name]}</label>
                {hints[name] && <p className="field-hint" id={`profile-${name}-hint`}>{hints[name]}</p>}
                <input id={`profile-${name}`} name={name} type="text" autoComplete="off"
                  inputMode={name === 'year' ? 'numeric' : ['mileage', 'operating_hours'].includes(name) ? 'decimal' : 'text'}
                  value={state.draft[name]} onChange={(event) => store.edit(name, event.target.value)}
                  required={['year', 'make', 'model', 'vehicle_type'].includes(name)}
                  ref={(node) => { inputs.current[name] = node }} aria-invalid={Boolean(state.errors[name])}
                  aria-describedby={[hints[name] ? `profile-${name}-hint` : '', state.errors[name] ? `profile-${name}-error` : ''].filter(Boolean).join(' ') || undefined} />
                {state.errors[name] && <p id={`profile-${name}-error`} className="field-error">{state.errors[name]}</p>}
              </div>
            ))}
            <div className="profile-actions">
              <button type="submit" disabled={state.pending || state.reloadRequired || Boolean(state.confirmation) || prepared?.unchanged}>
                {state.pending ? 'Saving vehicle' : 'Save changes'}</button>
              <button type="button" onClick={cancelEdit}>Cancel edit</button>
            </div>
          </fieldset>
          {state.confirmation && (
            <section className="session-panel reading-confirmation" aria-labelledby="reading-confirmation-title">
              <h2 id="reading-confirmation-title" ref={confirmationHeading} tabIndex={-1}>Confirm reading changes.</h2>
              <p>These changes lower or clear recorded readings. Review each change before confirming.</p>
              <ul>{state.confirmation.fields.map((name) => (
                <li key={name}>{labels[name]}: current {state.confirmation.currentReadings[name]}; proposed {proposed(name)}.</li>
              ))}</ul>
              <div className="profile-actions">
                <button type="button" disabled={state.pending} onClick={() => { void store.confirm() }}>Confirm and save changes</button>
                <button type="button" disabled={state.pending} onClick={() => {
                  store.cancelConfirmation(); inputs.current.mileage?.focus()
                }}>Cancel confirmation</button>
              </div>
            </section>
          )}
        </form>
      )}
      {!state.pending && !['invalid', 'not-found', 'gated'].includes(state.status) && (
        <div className="profile-actions">
          <button type="button" onClick={() => {
            if (store.requestReload()) requestAnimationFrame(() => reloadHeading.current?.focus())
          }}>{vehicle ? 'Reload vehicle' : 'Try again'}</button>
        </div>
      )}
      {state.reloadPrompt && (
        <section className="session-panel" aria-labelledby="vehicle-reload-title">
          <h2 id="vehicle-reload-title" ref={reloadHeading} tabIndex={-1}>Reload and review.</h2>
          <p>{vehicleReloadWarning}</p>
          <div className="profile-actions">
            <button type="button" disabled={state.pending} onClick={() => { void store.reload() }}>Discard draft and reload</button>
            <button type="button" disabled={state.pending} onClick={() => { store.cancelReload(); feedback.current?.focus() }}>Keep current draft</button>
          </div>
        </section>
      )}
    </section>
  )
}
