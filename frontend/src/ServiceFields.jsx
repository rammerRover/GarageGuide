import { serviceFields, serviceTypes } from './serviceValidation.js'

const labels = {
  service_date: 'Service date', service_type: 'Service type', description: 'Description',
  mileage: 'Service mileage (miles, optional)', operating_hours: 'Service operating hours (optional)',
  cost: 'Total service cost (USD)', notes: 'Notes (optional)',
}
const hints = {
  service_date: 'Use YYYY-MM-DD, on or before today according to the server calendar.',
  description: 'Describe the maintenance, repair, inspection, or diagnostic work performed.',
  mileage: 'Historical snapshot only. Blank means Not recorded; 0 means confirmed zero. Use at most one decimal place.',
  operating_hours: 'Historical snapshot only. Blank means Not recorded; 0 means confirmed zero. Use at most one decimal place.',
  cost: 'Optional USD amount. Blank means Not recorded; 0 means confirmed free. Use at most two decimal places.',
  notes: 'Leave blank to clear optional notes.',
}

export default function ServiceFields({ prefix, state, store, inputs }) {
  return serviceFields.map((name) => {
    const id = `${prefix}-${name}`
    const props = {
      id, name, value: state.draft[name], autoComplete: 'off',
      onChange: (event) => store.edit(name, event.target.value),
      ref: (node) => { inputs.current[name] = node },
      required: ['service_date', 'service_type', 'description'].includes(name),
      'aria-invalid': Boolean(state.errors[name]),
      'aria-describedby': [hints[name] ? `${id}-hint` : '', state.errors[name] ? `${id}-error` : ''].filter(Boolean).join(' ') || undefined,
    }
    return <div className="form-field" key={name}>
      <label htmlFor={id}>{labels[name]}</label>
      {hints[name] && <p id={`${id}-hint`} className="field-hint">{hints[name]}</p>}
      {name === 'service_type' ? <select {...props}>
        <option value="">Choose a service type</option>
        {serviceTypes.map((type) => <option value={type} key={type}>{type[0].toUpperCase() + type.slice(1)}</option>)}
      </select> : ['description', 'notes'].includes(name) ? <textarea {...props} rows={name === 'description' ? 3 : 4} />
        : <input {...props} type="text" inputMode={['mileage', 'operating_hours', 'cost'].includes(name) ? 'decimal' : 'text'}
          placeholder={name === 'service_date' ? 'YYYY-MM-DD' : undefined} />}
      {state.errors[name] && <p id={`${id}-error`} className="field-error">{state.errors[name]}</p>}
    </div>
  })
}
