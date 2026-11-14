import { parseSessionDeadline } from './sessionDeadline.js'

export const vehicleFields = ['year', 'make', 'model', 'vehicle_type', 'engine', 'mileage', 'operating_hours']
const readingMessage = 'Enter a nonnegative decimal string with at most one decimal place, up to 99999999999.9.'
const fieldMessages = {
  year: 'Enter a model year from 1886 through next calendar year.',
  make: 'Enter nonblank text with valid Unicode and no NUL.',
  model: 'Enter nonblank text with valid Unicode and no NUL.',
  vehicle_type: 'Enter nonblank text with valid Unicode and no NUL.',
  engine: 'Enter valid Unicode characters without NUL.',
  mileage: readingMessage, operating_hours: readingMessage,
}
const typeMessages = {
  missing: 'Field required.', string_type: 'Enter text.', int_type: 'Enter a whole model year.',
  extra_forbidden: 'Unexpected fields are not allowed.', json_invalid: 'Provide valid JSON.',
  model_type: 'Provide a JSON object.', model_attributes_type: 'Provide a JSON object.',
  value_error: 'Enter a valid value.',
}
const safeText = (value) => typeof value === 'string' && value.isWellFormed() && !value.includes('\0')
const publicReading = (value) => value === null || (typeof value === 'string' && /^(?:0|[1-9][0-9]{0,10})\.[0-9]$/.test(value))

export function prepareVehicleInput(values) {
  const errors = {}
  const details = {}
  if (!values || typeof values !== 'object' || Array.isArray(values) ||
      Object.keys(values).some((key) => !vehicleFields.includes(key))) return { errors, invalid: true }
  const year = typeof values.year === 'string' && /^[0-9]+$/.test(values.year.trim()) ? Number(values.year.trim()) : values.year
  if (!Number.isInteger(year) || year < 1886 || year > 32767) errors.year = fieldMessages.year
  else details.year = year
  for (const name of ['make', 'model', 'vehicle_type', 'engine']) {
    const value = values[name] ?? (name === 'engine' ? '' : null)
    if (!safeText(value) || (name !== 'engine' && !value.trim())) errors[name] = fieldMessages[name]
    else details[name] = value.trim() || null
  }
  for (const name of ['mileage', 'operating_hours']) {
    const value = values[name]
    if (value == null || (typeof value === 'string' && !value.trim())) details[name] = null
    else if (typeof value !== 'string' || !/^[0-9]+(?:\.[0-9])?$/.test(value.trim())) errors[name] = readingMessage
    else {
      const [integer, fraction = '0'] = value.trim().split('.')
      const digits = integer.replace(/^0+(?=[0-9])/, '')
      if (digits.length > 11) errors[name] = readingMessage
      else details[name] = `${digits}.${fraction}`
    }
  }
  return { details, errors, invalid: Object.keys(errors).length > 0 }
}

export function isPublicVehicle(value) {
  const names = ['id', ...vehicleFields, 'readings_updated_at', 'created_at']
  return value && typeof value === 'object' && !Array.isArray(value) &&
    Object.keys(value).length === names.length && names.every((name) => Object.hasOwn(value, name)) &&
    Number.isSafeInteger(value.id) && value.id > 0 && Number.isInteger(value.year) && value.year >= 1 && value.year <= 32767 &&
    ['make', 'model', 'vehicle_type'].every((name) => safeText(value[name]) && value[name].trim() === value[name] && value[name].length > 0) &&
    (value.engine === null || (safeText(value.engine) && value.engine.trim() === value.engine && value.engine.length > 0)) &&
    publicReading(value.mileage) && publicReading(value.operating_hours) &&
    (value.readings_updated_at === null || Boolean(parseSessionDeadline(value.readings_updated_at))) &&
    Boolean(parseSessionDeadline(value.created_at))
}

export function parseVehicleErrors(detail) {
  if (!Array.isArray(detail) || !detail.length) return null
  const errors = {}
  for (const entry of detail) {
    if (!entry || typeof entry !== 'object' || Array.isArray(entry) ||
        Object.keys(entry).length !== 3 || !['loc', 'msg', 'type'].every((key) => Object.hasOwn(entry, key)) ||
        !Array.isArray(entry.loc) || entry.loc[0] !== 'body' || typeof entry.type !== 'string' || !Object.hasOwn(typeMessages, entry.type)) return null
    const field = entry.loc.length === 2 && vehicleFields.includes(entry.loc[1]) ? entry.loc[1] : null
    if (!field && entry.loc.length !== 1) return null
    const expected = entry.type === 'value_error' && field ? fieldMessages[field] : typeMessages[entry.type]
    if (entry.msg !== expected) return null
    if (field) errors[field] ??= entry.msg
  }
  return errors
}
