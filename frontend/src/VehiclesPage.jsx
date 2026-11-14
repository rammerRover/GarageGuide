import { useEffect, useMemo, useRef, useSyncExternalStore } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useSession } from './useSession.js'
import { createVehicleStore } from './vehicleState.js'

export default function VehiclesPage() {
  const { authenticatedRequest } = useSession()
  const store = useMemo(() => createVehicleStore(authenticatedRequest), [authenticatedRequest])
  const state = useSyncExternalStore(store.subscribe, store.getSnapshot)
  const heading = useRef(null)
  const error = useRef(null)
  const { state: navigation } = useLocation()
  const created = navigation?.vehicleCreated === true

  useEffect(() => {
    heading.current?.focus()
    void store.load()
    return () => store.dispose()
  }, [store])
  useEffect(() => { if (state.message && state.status !== 'success') error.current?.focus() }, [state.message, state.status])

  return (
    <section aria-labelledby="garage-title" aria-busy={state.pending}>
      <div className="intro">
        <p className="eyebrow">Your vehicles</p>
        <h1 id="garage-title" ref={heading} tabIndex={-1}>Your garage.</h1>
        <p>Record your vehicles and their current mileage or operating hours.</p>
        <nav className="site-nav" aria-label="Garage navigation">
          <Link to="/vehicles/new">Add vehicle</Link>
          <Link to="/account">Back to account</Link>
        </nav>
      </div>
      <p role="status" aria-live="polite" aria-atomic="true">
        {created && 'Vehicle created successfully. '}
        {state.pending ? 'Loading your garage. Please wait.' : state.status === 'success' && !state.vehicles.length ? 'No vehicles recorded yet. Add your first vehicle when you are ready.' : state.status === 'success' ? 'Your garage is ready.' : ''}
      </p>
      {state.message && state.status !== 'success' && (
        <div className="session-panel">
          <p className="field-error" role="alert" ref={error} tabIndex={-1}>{state.message}</p>
          <button type="button" onClick={() => { void store.load() }} disabled={state.pending}>Try again</button>
        </div>
      )}
      {state.status === 'success' && state.vehicles.length > 0 && (
        <ul className="vehicle-list">
          {state.vehicles.map((vehicle) => (
            <li key={vehicle.id} className="vehicle-card">
              <h2>{vehicle.year} {vehicle.make} {vehicle.model}</h2>
              <dl>
                <div><dt>Vehicle type</dt><dd>{vehicle.vehicle_type}</dd></div>
                <div><dt>Engine</dt><dd>{vehicle.engine ?? 'Not recorded'}</dd></div>
                <div><dt>Current mileage (miles)</dt><dd>{vehicle.mileage ?? 'Not recorded'}</dd></div>
                <div><dt>Current operating hours</dt><dd>{vehicle.operating_hours ?? 'Not recorded'}</dd></div>
              </dl>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
