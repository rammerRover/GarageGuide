import { useEffect, useRef, useSyncExternalStore } from 'react'
import { partFields } from './servicePartValidation.js'

const labels = { name: 'Part name', part_number: 'Part number (optional)', manufacturer: 'Manufacturer (optional)',
  quantity: 'Quantity', notes: 'Part notes (optional)' }
const hints = { name: 'Describe the part used. Manual entry does not need a catalog match.',
  part_number: 'Leave blank if not recorded.', manufacturer: 'Leave blank if not recorded.',
  quantity: 'Use a whole number from 1 through 2147483647.', notes: 'Optional historical notes. Blank means Not recorded.' }
const recorded = (value) => value === null ? 'Not recorded' : value === '' ? 'Empty recorded value' : value

function PartField({ name, prefix, label, hint, value, error, onChange, inputs, required = false }) {
  const id = `${prefix}-${name}`
  const props = { id, name, value, required, autoComplete: 'off',
    ref: (node) => { inputs.current[name] = node }, onChange: (event) => onChange(name, event.target.value),
    'aria-invalid': Boolean(error), 'aria-describedby': [hint ? `${id}-hint` : '', error ? `${id}-error` : ''].filter(Boolean).join(' ') || undefined }
  return <div className="form-field">
    <label htmlFor={id}>{label}</label>
    {hint && <p id={`${id}-hint`} className="field-hint">{hint}</p>}
    {name === 'notes' ? <textarea {...props} rows={3} /> : <input {...props} type="text" inputMode={name === 'quantity' ? 'numeric' : 'text'} />}
    {error && <p id={`${id}-error`} className="field-error">{error}</p>}
  </div>
}

export default function ServiceParts({ store, vehicleId, serviceId, disabled, canAct }) {
  const state = useSyncExternalStore(store.subscribe, store.getSnapshot)
  const feedback = useRef(null), inputs = useRef({}), focused = useRef(0), previewHeading = useRef(null)
  const removalHeading = useRef(null), reloadHeading = useRef(null), reloadButton = useRef(null), lookupButton = useRef(null)
  const removalButtons = useRef(new Map())
  useEffect(() => { if (!disabled) void store.load(vehicleId, serviceId) }, [store, vehicleId, serviceId, disabled])
  useEffect(() => {
    const depart = () => store.depart()
    window.addEventListener('pagehide', depart)
    return () => { store.depart(); window.removeEventListener('pagehide', depart) }
  }, [store])
  useEffect(() => {
    if (state.pending || focused.current === state.focusVersion) return
    focused.current = state.focusVersion
    const fields = state.source === 'catalog' ? ['manufacturer', 'part_number', 'quantity', 'notes'] : partFields
    const field = [...fields, 'preview', 'confirm_removal'].find((name) => state.errors[name])
    const target = state.confirmation ? removalHeading.current : field === 'preview' ? lookupButton.current : field ? inputs.current[field] ?? feedback.current :
      state.status === 'review' ? previewHeading.current : state.message ? feedback.current : null
    target?.focus()
  }, [state.focusVersion, state.pending, state.errors, state.confirmation, state.source, state.status, state.message])
  const act = (action) => { if (canAct()) return action() }
  const blocked = disabled || state.pending || Boolean(state.confirmation || state.reloadPrompt || state.uncertainOperation) || state.refreshRequired
  const selected = state.parts.find((part) => String(part.id) === state.confirmation)
  return <section className="service-parts" aria-labelledby="parts-used-title" aria-busy={state.pending}>
    <h2 id="parts-used-title">Parts used</h2>
    <p>Historical snapshots of the parts used for this service. To correct one, remove it and add it again. Part entries do not change the service cost or vehicle readings.</p>
    <p role="status" aria-live="polite" aria-atomic="true" className="form-status">{state.pending ? 'Working on parts used. Please wait.' : ''}</p>
    <p role="status" aria-live="polite" aria-atomic="true" className="form-status" tabIndex={-1} ref={feedback}>{state.message}</p>
    {disabled && <p>Finish or cancel the current service action before changing parts.</p>}
    {state.status === 'not-found' && <p>This service may no longer be available. Reload parts to check, or return to service history.</p>}
    {state.loaded && <>
      {!state.parts.length ? <p>No parts recorded for this service.</p> : <ul className="vehicle-list parts-list">
        {state.parts.map((part) => <li className="vehicle-card" key={part.id}>
          <h3>{part.name}</h3>
          <dl className="part-values">
            <div><dt>Manufacturer</dt><dd>{recorded(part.manufacturer)}</dd></div>
            <div><dt>Part number</dt><dd>{recorded(part.part_number)}</dd></div>
            <div><dt>Quantity</dt><dd>{part.quantity}</dd></div>
            <div><dt>Notes</dt><dd>{recorded(part.notes)}</dd></div>
          </dl>
          {part.part_id === null && <p className="field-hint">No current catalog reference. These saved details remain part of the service history.</p>}
          <button type="button" disabled={blocked} ref={(node) => { if (node) removalButtons.current.set(String(part.id), node); else removalButtons.current.delete(String(part.id)) }}
            aria-label={`Remove ${part.name} snapshot`} onClick={() => act(() => store.requestRemoval(String(part.id)))}>Remove snapshot</button>
        </li>)}
      </ul>}
      <fieldset className="part-source" disabled={blocked}>
        <legend>Part entry method</legend>
        <label><input type="radio" name="part-source" value="manual" checked={state.source === 'manual'} onChange={() => act(() => store.chooseSource('manual'))} /> Manual entry</label>
        <label><input type="radio" name="part-source" value="catalog" checked={state.source === 'catalog'} onChange={() => act(() => store.chooseSource('catalog'))} /> Exact catalog lookup</label>
      </fieldset>
      {state.source === 'catalog' && <form className="registration part-form" aria-label="Exact catalog lookup" noValidate onSubmit={(event) => { event.preventDefault(); act(() => { void store.lookup() }) }}>
        <fieldset disabled={blocked}>
          <legend>Find an exact catalog entry</legend>
          <p>Enter the exact, case-sensitive manufacturer and part number. Lookup does not confirm vehicle compatibility.</p>
          {['manufacturer', 'part_number'].map((name) => <PartField key={name} prefix="part-lookup" name={name} label={name === 'manufacturer' ? 'Catalog manufacturer' : 'Catalog part number'}
            value={state.lookupPair[name]} error={state.errors[name]} inputs={inputs} required onChange={(field, value) => act(() => store.editLookup(field, value))} />)}
          <button type="submit" ref={lookupButton} aria-describedby={state.errors.preview ? 'part-preview-error' : undefined}>Look up catalog part</button>
          {state.errors.preview && <p id="part-preview-error" className="field-error">{state.errors.preview}</p>}
        </fieldset>
      </form>}
      {['catalog-missing', 'stale-preview'].includes(state.status) && <div className="profile-actions">
        <button type="button" disabled={blocked} onClick={() => act(() => { if (store.chooseSource('manual')) requestAnimationFrame(() => inputs.current.name?.focus()) })}>Switch to manual entry</button>
        <p>Review the exact pair and select Look up catalog part again, or explicitly switch to manual entry.</p>
      </div>}
      {state.preview && <section className="session-panel catalog-preview" aria-labelledby="part-preview-title">
        <h3 id="part-preview-title" tabIndex={-1} ref={previewHeading}>Review catalog details before saving</h3>
        <dl className="part-values">
          <div><dt>Name</dt><dd>{state.preview.name}</dd></div>
          <div><dt>Manufacturer</dt><dd>{state.preview.manufacturer}</dd></div>
          <div><dt>Part number</dt><dd>{state.preview.part_number}</dd></div>
          <div><dt>Category</dt><dd>{state.preview.category}</dd></div>
        </dl>
        <p>The server rechecks this entry when you save and copies its stored details. Category is for review only. No vehicle fitment is confirmed.</p>
      </section>}
      <form className="registration part-form" aria-label="Add a part snapshot" noValidate onSubmit={(event) => { event.preventDefault(); act(() => { void store.submit() }) }}>
        <fieldset disabled={blocked}>
          <legend>Add a {state.source === 'manual' ? 'manual' : 'catalog-backed'} part snapshot</legend>
          {(state.source === 'manual' ? partFields : ['quantity', 'notes']).map((name) => <PartField key={name} prefix="part-entry" name={name} label={labels[name]} hint={hints[name]}
            value={state.draft[name]} error={state.errors[name]} inputs={inputs} required={name === 'name' || name === 'quantity'} onChange={(field, value) => act(() => store.edit(field, value))} />)}
          <button type="submit" disabled={blocked || (state.source === 'catalog' && !state.preview)}>Add part snapshot</button>
          {state.source === 'catalog' && !state.preview && <p>Look up and review a catalog entry before adding it.</p>}
          <p>Leaving this service page discards temporary part entry and the reviewed preview.</p>
        </fieldset>
      </form>
    </>}
    {state.refreshRequired && !state.pending && <p>Reload and inspect the saved list before another change.</p>}
    {state.confirmation && <section className="session-panel" aria-labelledby="part-removal-title">
      <h3 id="part-removal-title" tabIndex={-1} ref={removalHeading}>Confirm snapshot removal</h3>
      <p>{selected?.name}</p>
      <p>Remove only this saved part snapshot? The service and catalog entry will remain. This cannot be undone.</p>
      <div className="profile-actions">
        <button type="button" disabled={disabled || state.pending} onClick={() => act(() => { void store.confirmRemoval() })}>Permanently remove snapshot</button>
        <button type="button" disabled={state.pending} onClick={() => { const id = state.confirmation; store.cancelRemoval(); requestAnimationFrame(() => removalButtons.current.get(id)?.focus()) }}>Cancel removal</button>
      </div>
    </section>}
    {!state.pending && state.status !== 'gated' && <div className="profile-actions">
      <button type="button" ref={reloadButton} disabled={disabled || Boolean(state.confirmation || state.reloadPrompt)} onClick={() => act(() => { if (store.requestReload()) requestAnimationFrame(() => reloadHeading.current?.focus()) })}>
        {state.loaded ? 'Reload and inspect parts' : 'Try loading parts again'}</button>
    </div>}
    {state.reloadPrompt && <section className="session-panel" aria-labelledby="part-reload-title">
      <h3 id="part-reload-title" ref={reloadHeading} tabIndex={-1}>Reload and inspect saved parts</h3>
      <p>{state.message}</p>
      <p>Your temporary entry is retained. The reviewed catalog preview will be cleared. Reloading does not retry an addition or removal.</p>
      <div className="profile-actions">
        <button type="button" disabled={disabled || state.pending} onClick={() => act(() => { void store.reload() })}>Reload saved parts</button>
        <button type="button" disabled={state.pending} onClick={() => { store.cancelReload(); requestAnimationFrame(() => reloadButton.current?.focus()) }}>Keep current view</button>
      </div>
    </section>}
    {state.uncertainOperation === 'add' && state.inspected && !state.pending && <section className="session-panel" aria-labelledby="part-duplicate-title">
      <h3 id="part-duplicate-title">Review before adding again</h3>
      <p>Even if the entry is absent after reload, the original request may still finish. Another submission can create a duplicate.</p>
      <button type="button" disabled={disabled} onClick={() => act(() => { if (store.acknowledgeAddRisk()) requestAnimationFrame(() => inputs.current[state.source === 'manual' ? 'name' : 'manufacturer']?.focus()) })}>I inspected saved parts and understand the duplicate risk</button>
      <p>This only unlocks the form. It does not send another request.</p>
    </section>}
  </section>
}
