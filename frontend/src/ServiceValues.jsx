export default function ServiceValues({ record }) {
  const values = {
    'Service date': record.service_date, 'Service type': record.service_type, Description: record.description,
    'Service mileage (miles)': record.mileage, 'Service operating hours': record.operating_hours,
    'Total service cost (USD)': record.cost === null ? null : `USD ${record.cost}`, Notes: record.notes,
  }
  return <dl className="service-values">{Object.entries(values).map(([label, value]) => (
    <div key={label}><dt>{label}</dt><dd>{value ?? 'Not recorded'}</dd></div>
  ))}</dl>
}
