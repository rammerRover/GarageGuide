import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useSession } from './useSession.js'
import { createVehicleStore } from './vehicleState.js'
import { prepareVehicleInput, vehicleFields } from './vehicleValidation.js'

const emptyFields = () => Object.fromEntries(vehicleFields.map((name) => [name, '']))
const labels = {
  year: 'Model year', make: 'Make', model: 'Model', vehicle_type: 'Vehicle type',
  engine: 'Engine (optional)', mileage: 'Current mileage in miles (optional)',
  operating_hours: 'Current operating hours (optional)',
}
const hints = {
  year: 'Use a model year from 1886 through next calendar year.',
  vehicle_type: 'Free text, for example Car, Motorcycle, Dirt bike, ATV, or RZR.',
  engine: 'Leave blank when not recorded.',
  mileage: 'Leave blank when not recorded. Enter 0 for a confirmed zero; use at most one decimal place.',
  operating_hours: 'Leave blank when not recorded. Enter 0 for a confirmed zero; use at most one decimal place.',
}

export default function CreateVehiclePage() {
  const { authenticatedRequest } = useSession()
  const store = useMemo(() => createVehicleStore(authenticatedRequest), [authenticatedRequest])
  const state = useSyncExternalStore(store.subscribe, store.getSnapshot)
  const [fields, setFields] = useState(emptyFields)
  const inputs = useRef({})
  const heading = useRef(null)
  const error = useRef(null)
  const focused = useRef(0)
  const mounted = useRef(false)
  const navigate = useNavigate()

  useEffect(() => {
    mounted.current = true
    heading.current?.focus()
    const discard = () => {
      store.dispose()
      for (const input of Object.values(inputs.current)) if (input) input.value = ''
      setFields(emptyFields())
    }
    window.addEventListener('pagehide', discard)
    return () => {
      mounted.current = false
      store.dispose()
      window.removeEventListener('pagehide', discard)
    }
  }, [store])
  useEffect(() => {
    if (!state.pending && state.focusVersion !== focused.current) {
      focused.current = state.focusVersion
      const first = vehicleFields.find((name) => state.errors[name])
      ;(inputs.current[first] ?? error.current)?.focus()
    }
  }, [state.focusVersion, state.pending, state.errors])

  function update(event) {
    const { name, value } = event.target
    setFields((current) => ({ ...current, [name]: value }))
    store.correct(name)
  }

  async function submit(event) {
    event.preventDefault()
    if (store.getSnapshot().pending) return
    const prepared = prepareVehicleInput(fields)
    if (prepared.invalid) { store.invalid(prepared.errors); return }
    const result = await store.submit(prepared.details)
    if (mounted.current && result.kind === 'success') {
      setFields(emptyFields())
      navigate('/vehicles', { state: { vehicleCreated: true } })
    }
  }

  return (
    <>
      <section className="intro" aria-labelledby="create-vehicle-title">
        <p className="eyebrow">Your garage</p>
        <h1 id="create-vehicle-title" ref={heading} tabIndex={-1}>Add a vehicle.</h1>
        <p>Mileage and operating hours are independent. You can record either, both, or neither.</p>
      </section>
      <form className="registration vehicle-form" method="post" action="/api/vehicles" onSubmit={submit}
        noValidate aria-labelledby="create-vehicle-title" aria-busy={state.pending}>
        <fieldset disabled={state.pending}>
          <legend className="visually-hidden">Vehicle details</legend>
          {vehicleFields.map((name) => (
            <div className="form-field" key={name}>
              <label htmlFor={`vehicle-${name}`}>{labels[name]}</label>
              {hints[name] && <p className="field-hint" id={`vehicle-${name}-hint`}>{hints[name]}</p>}
              <input id={`vehicle-${name}`} name={name} type="text" autoComplete="off"
                inputMode={name === 'year' ? 'numeric' : ['mileage', 'operating_hours'].includes(name) ? 'decimal' : 'text'}
                value={fields[name]} onChange={update} required={['year', 'make', 'model', 'vehicle_type'].includes(name)}
                ref={(node) => { inputs.current[name] = node }} aria-invalid={Boolean(state.errors[name])}
                aria-describedby={[hints[name] ? `vehicle-${name}-hint` : '', state.errors[name] ? `vehicle-${name}-error` : ''].filter(Boolean).join(' ') || undefined} />
              {state.errors[name] && <p id={`vehicle-${name}-error`} className="field-error">{state.errors[name]}</p>}
            </div>
          ))}
          <button type="submit" disabled={state.pending}>{state.pending ? 'Saving vehicle' : 'Save vehicle'}</button>
        </fieldset>
        <p className="form-status" role="status" aria-live="polite" aria-atomic="true">{state.pending ? 'Saving your vehicle. Please wait.' : ''}</p>
        <p className="form-status field-error" ref={error} tabIndex={-1} role="alert" aria-atomic="true">{state.message}</p>
        <p><Link to="/vehicles">{state.message && state.status !== 'invalid' ? 'Check your garage before submitting again' : 'Cancel and return to garage'}</Link></p>
      </form>
    </>
  )
}
