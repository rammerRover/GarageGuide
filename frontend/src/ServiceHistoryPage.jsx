import { useEffect, useRef, useState, useSyncExternalStore } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { useSession } from './useSession.js'
import { createServiceHistoryStore } from './serviceState.js'
import { serviceFields } from './serviceValidation.js'
import ServiceFields from './ServiceFields.jsx'
import ServiceValues from './ServiceValues.jsx'

export default function ServiceHistoryPage() {
  const { vehicleId } = useParams()
  const { sessionStore } = useSession()
  const [resource, setResource] = useState(null)
  useEffect(() => {
    const store = createServiceHistoryStore(sessionStore)
    setResource({ store, vehicleId })
    return () => store.dispose()
  }, [sessionStore, vehicleId])
  if (!resource || resource.vehicleId !== vehicleId) return <p role="status">Loading service history. Please wait.</p>
  return <ServiceHistoryView store={resource.store} vehicleId={vehicleId} />
}

function ServiceHistoryView({ store, vehicleId }) {
  const state = useSyncExternalStore(store.subscribe, store.getSnapshot)
  const location = useLocation()
  const heading = useRef(null), feedback = useRef(null), inputs = useRef({}), focused = useRef(0), reloadHeading = useRef(null)
  useEffect(() => {
    heading.current?.focus()
    void store.load(vehicleId)
    const depart = () => store.depart()
    window.addEventListener('pagehide', depart)
    return () => { store.depart(); window.removeEventListener('pagehide', depart) }
  }, [store, vehicleId])
  useEffect(() => {
    if (state.pending || focused.current === state.focusVersion) return
    focused.current = state.focusVersion
    const first = serviceFields.find((name) => state.errors[name])
    ;(first ? inputs.current[first] : feedback.current)?.focus()
  }, [state.focusVersion, state.pending, state.errors])
  const uncertain = Boolean(state.uncertainOperation)
  const blocked = state.pending || uncertain || (state.created && state.status !== 'ready')
  return <section aria-labelledby="service-history-title" aria-busy={state.pending}>
    <div className="intro">
      <p className="eyebrow">Your vehicle</p>
      <h1 id="service-history-title" tabIndex={-1} ref={heading}>Service history.</h1>
      <Link to={`/vehicles/${vehicleId}`}>Back to vehicle</Link>
      <p>Record dated work for this vehicle. Service readings are historical snapshots and do not change its current readings.</p>
    </div>
    <p className="form-status" role="status" aria-live="polite" aria-atomic="true">{state.pending ? 'Working on service history. Please wait.' : ''}</p>
    <p className="form-status" tabIndex={-1} ref={feedback} role="status" aria-live="polite" aria-atomic="true">{state.message ||
      (location.state?.serviceRemoved === true && state.loaded ? 'Service record removed. History reloaded.' : '')}</p>
    {state.loaded && <>
      <h2 className="service-section-title">Saved service records</h2>
      {!state.records.length ? <p>No service records yet.</p> : <ul className="vehicle-list service-list">
        {state.records.map((record) => <li className="vehicle-card" key={record.id}>
          <h3><Link to={`/vehicles/${record.vehicle_id}/services/${record.id}`}>{record.service_date} — {record.service_type}</Link></h3>
          <ServiceValues record={record} />
        </li>)}
      </ul>}
      <form className="registration service-form" noValidate aria-labelledby="service-create-title" aria-busy={state.pending}
        onSubmit={(event) => { event.preventDefault(); void store.submit() }}>
        <h2 id="service-create-title">Add a service record</h2>
        <fieldset disabled={state.pending}>
          <legend className="visually-hidden">New service details</legend>
          <ServiceFields prefix="new-service" state={state} store={store} inputs={inputs} />
          <button type="submit" disabled={blocked}>{state.pending ? 'Working…' : 'Create service record'}</button>
        </fieldset>
        {blocked && !state.pending && <p>Reload and inspect the history before submitting another record.</p>}
        <p>Leaving this page discards the temporary form.</p>
      </form>
    </>}
    {!state.pending && !['invalid', 'not-found', 'gated'].includes(state.status) && <div className="profile-actions">
      <button type="button" onClick={() => { if (store.requestReload()) requestAnimationFrame(() => reloadHeading.current?.focus()) }}>
        {state.loaded ? 'Reload history and inspect' : 'Try again'}</button>
    </div>}
    {state.reloadPrompt && <section className="session-panel" aria-labelledby="service-history-reload-title">
      <h2 id="service-history-reload-title" ref={reloadHeading} tabIndex={-1}>Reload and inspect history.</h2>
      <p>{uncertain ? 'Inspect the date, type, description, readings, and cost. An absent entry does not prove creation failed: the original request may still finish. Resubmitting can create a duplicate.' : 'Reload saved records. Your temporary creation draft will be retained.'}</p>
      <div className="profile-actions">
        <button type="button" disabled={state.pending} onClick={() => { void store.reload() }}>Reload history</button>
        <button type="button" disabled={state.pending} onClick={() => { store.cancelReload(); feedback.current?.focus() }}>Keep current view</button>
      </div>
    </section>}
    {uncertain && state.inspected && !state.pending && <section className="session-panel" aria-labelledby="duplicate-risk-title">
      <h2 id="duplicate-risk-title">Review before resubmitting.</h2>
      <p>Even if no matching entry appeared, the original request may still finish. Another submission can create a duplicate.</p>
      <button type="button" onClick={() => {
        if (store.acknowledgeCreateRisk()) requestAnimationFrame(() => inputs.current.service_date?.focus())
      }}>I inspected history and understand the duplicate risk</button>
      <p>This only unlocks the form. It does not submit another request.</p>
    </section>}
  </section>
}
