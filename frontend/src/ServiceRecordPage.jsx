import { useEffect, useRef, useState, useSyncExternalStore } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useSession } from './useSession.js'
import { createServiceRecordStore, serviceReloadWarning, serviceRemovalWarning } from './serviceState.js'
import { prepareServiceInput, serviceFields } from './serviceValidation.js'
import ServiceFields from './ServiceFields.jsx'
import ServiceValues from './ServiceValues.jsx'

export default function ServiceRecordPage() {
  const { vehicleId, serviceId } = useParams()
  const { sessionStore } = useSession()
  const [resource, setResource] = useState(null)
  useEffect(() => {
    const store = createServiceRecordStore(sessionStore)
    setResource({ store, vehicleId, serviceId })
    return () => store.dispose()
  }, [sessionStore, vehicleId, serviceId])
  if (!resource || resource.vehicleId !== vehicleId || resource.serviceId !== serviceId) return <p role="status">Loading service record. Please wait.</p>
  return <ServiceRecordView store={resource.store} vehicleId={vehicleId} serviceId={serviceId} />
}

function ServiceRecordView({ store, vehicleId, serviceId }) {
  const state = useSyncExternalStore(store.subscribe, store.getSnapshot)
  const navigate = useNavigate()
  const heading = useRef(null), feedback = useRef(null), inputs = useRef({}), focused = useRef(0)
  const removalHeading = useRef(null), reloadHeading = useRef(null), editButton = useRef(null), removalButton = useRef(null)
  useEffect(() => {
    heading.current?.focus()
    void store.load(vehicleId, serviceId)
    const depart = () => store.depart()
    window.addEventListener('pagehide', depart)
    return () => { store.depart(); window.removeEventListener('pagehide', depart) }
  }, [store, vehicleId, serviceId])
  useEffect(() => {
    if (state.status === 'removed') navigate(`/vehicles/${vehicleId}/services`, { replace: true, state: { serviceRemoved: true } })
  }, [state.status, navigate, vehicleId])
  useEffect(() => {
    if (state.pending || state.focusVersion === focused.current) return
    focused.current = state.focusVersion
    const first = serviceFields.find((name) => state.errors[name])
    const target = first ? inputs.current[first] : state.confirmation ? removalHeading.current : feedback.current
    target?.focus()
  }, [state.focusVersion, state.pending, state.errors, state.confirmation])
  const uncertain = Boolean(state.uncertainOperation)
  const prepared = state.record && state.editing ? prepareServiceInput(state.draft, state.record) : null
  return <section aria-labelledby="service-record-title" aria-busy={state.pending}>
    <div className="intro">
      <p className="eyebrow">Your vehicle</p>
      <h1 id="service-record-title" ref={heading} tabIndex={-1}>Service record.</h1>
      <Link to={`/vehicles/${vehicleId}/services`}>Back to service history</Link>
    </div>
    <p className="form-status" role="status" aria-live="polite" aria-atomic="true">{state.pending ? 'Working on this service record. Please wait.' : ''}</p>
    <p className="form-status" ref={feedback} tabIndex={-1} role="status" aria-live="polite" aria-atomic="true">{state.message}</p>
    {state.record && <>
      <div className="vehicle-card vehicle-profile">
        <h2>Saved service record</h2>
        <ServiceValues record={state.record} />
        <p>Created at {state.record.created_at}</p>
        <p>These are historical readings. Editing them does not update the vehicle’s current readings.</p>
        {!state.editing && <button type="button" ref={editButton} disabled={state.pending || uncertain || state.confirmation}
          onClick={() => { if (store.beginEdit()) requestAnimationFrame(() => inputs.current.service_date?.focus()) }}>Edit service record</button>}
      </div>
      {state.editing && <form className="registration service-form" aria-label="Edit service record" noValidate aria-busy={state.pending}
        onSubmit={(event) => { event.preventDefault(); void store.submit() }}>
        <fieldset disabled={state.pending || state.confirmation}>
          <legend>Service details</legend>
          <ServiceFields prefix="edit-service" state={state} store={store} inputs={inputs} />
          <div className="profile-actions">
            <button type="submit" disabled={state.pending || uncertain || prepared?.unchanged}>Save changes</button>
            <button type="button" onClick={() => { store.cancelEdit(); requestAnimationFrame(() => editButton.current?.focus()) }}>Cancel edit</button>
          </div>
        </fieldset>
      </form>}
      <div className="profile-actions">
        <button type="button" ref={removalButton} disabled={state.pending || uncertain || state.confirmation}
          onClick={() => store.requestRemoval()}>Remove service record</button>
      </div>
    </>}
    {state.confirmation && <section className="session-panel" aria-labelledby="service-removal-title">
      <h2 id="service-removal-title" ref={removalHeading} tabIndex={-1}>Confirm permanent removal.</h2>
      <p>{serviceRemovalWarning}</p>
      <div className="profile-actions">
        <button type="button" disabled={state.pending} onClick={() => { void store.confirmRemoval() }}>Permanently remove record</button>
        <button type="button" disabled={state.pending} onClick={() => { store.cancelRemoval(); removalButton.current?.focus() }}>Cancel removal</button>
      </div>
    </section>}
    {!state.pending && !['invalid', 'not-found', 'gated', 'removed'].includes(state.status) && <div className="profile-actions">
      <button type="button" onClick={() => { if (store.requestReload()) requestAnimationFrame(() => reloadHeading.current?.focus()) }}>
        {state.record || uncertain ? 'Reload and inspect record' : 'Try again'}</button>
    </div>}
    {state.reloadPrompt && <section className="session-panel" aria-labelledby="service-record-reload-title">
      <h2 id="service-record-reload-title" ref={reloadHeading} tabIndex={-1}>Reload and review.</h2>
      <p>{serviceReloadWarning}</p>
      {state.uncertainOperation === 'remove' && <p>A later not-found response shows only that the record is currently absent, not which request removed it.</p>}
      <div className="profile-actions">
        <button type="button" disabled={state.pending} onClick={() => { void store.reload() }}>Discard draft and reload</button>
        <button type="button" disabled={state.pending} onClick={() => { store.cancelReload(); feedback.current?.focus() }}>Keep current draft</button>
      </div>
    </section>}
  </section>
}
