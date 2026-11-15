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
const publicReading = (value) => value === null || (typeof value === 'string' && value === value.trim() && /^(?:0|[1-9][0-9]{0,10})\.[0-9]$/.test(value))
export const vehicleIdMessage = 'Enter a vehicle ID from 1 through 2147483647 using digits without leading zeroes.'
const confirmationMessage = 'Provide confirmation values only for supplied reading fields.'
const emptyPatchMessage = 'Provide at least one editable vehicle field.'
const cannotClearMessage = 'This field cannot be cleared.'
const readingFields = ['mileage', 'operating_hours']

export function isVehicleId(value) {
  return typeof value === 'string' && value.length >= 1 && value.length <= 10 &&
    value[0] !== '0' && !/[^0-9]/.test(value) && (value.length < 10 || value <= '2147483647')
}

function normalizeReading(value) {
  if (value == null || (typeof value === 'string' && !value.trim())) return null
  if (typeof value !== 'string' || !/^[0-9]+(?:\.[0-9])?$/.test(value.trim())) return undefined
  const [integer, fraction = '0'] = value.trim().split('.')
  const digits = integer.replace(/^0+(?=[0-9])/, '')
  return digits.length <= 11 ? `${digits}.${fraction}` : undefined
}

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
    const value = normalizeReading(values[name])
    if (value === undefined) errors[name] = readingMessage
    else details[name] = value
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

export function parseVehicleErrors(detail, { patch = false } = {}) {
  if (!Array.isArray(detail) || !detail.length) return null
  const errors = {}
  for (const entry of detail) {
    if (!entry || typeof entry !== 'object' || Array.isArray(entry) ||
        Object.keys(entry).length !== 3 || !['loc', 'msg', 'type'].every((key) => Object.hasOwn(entry, key)) ||
        !Array.isArray(entry.loc) || typeof entry.type !== 'string' || !Object.hasOwn(typeMessages, entry.type)) return null
    if (patch && entry.type === 'value_error') {
      if (entry.loc.length === 2 && entry.loc[0] === 'path' && entry.loc[1] === 'vehicle_id' && entry.msg === vehicleIdMessage) {
        errors.vehicle_id = vehicleIdMessage
        continue
      }
      if (entry.loc.length === 2 && entry.loc[0] === 'body' && entry.loc[1] === 'reading_confirmation' && entry.msg === confirmationMessage) {
        errors.reading_confirmation = confirmationMessage
        continue
      }
      if (entry.loc.length === 1 && entry.loc[0] === 'body' && entry.msg === emptyPatchMessage) continue
      if (entry.loc.length === 2 && entry.loc[0] === 'body' &&
          ['year', 'make', 'model', 'vehicle_type'].includes(entry.loc[1]) && entry.msg === cannotClearMessage) {
        errors[entry.loc[1]] = cannotClearMessage
        continue
      }
    }
    if (entry.loc[0] !== 'body') return null
    const field = entry.loc.length === 2 && vehicleFields.includes(entry.loc[1]) ? entry.loc[1] : null
    if (!field && entry.loc.length !== 1) return null
    const expected = entry.type === 'value_error' && field ? fieldMessages[field] : typeMessages[entry.type]
    if (entry.msg !== expected) return null
    if (field) errors[field] ??= entry.msg
  }
  return errors
}

export function vehicleDraft(vehicle) {
  return Object.fromEntries(vehicleFields.map((name) => [name, vehicle[name] === null ? '' : String(vehicle[name])]))
}

export function prepareVehiclePatch(current, values, confirmation) {
  const errors = {}
  const details = {}
  if (!isPublicVehicle(current) || !values || typeof values !== 'object' || Array.isArray(values) ||
      Object.keys(values).some((name) => !vehicleFields.includes(name))) return { invalid: true, errors }
  for (const name of vehicleFields) {
    if (!Object.hasOwn(values, name)) continue
    let value = values[name]
    if (value === undefined) { errors[name] = fieldMessages[name]; continue }
    if (name === 'year') {
      value = typeof value === 'string' && /^[0-9]+$/.test(value.trim()) ? Number(value.trim()) : value
      // Skip the supplied-year policy only when this field will be omitted.
      if (Number.isInteger(value) && value === current.year) continue
      if (!Number.isInteger(value) || value < 1886 || value > 32767) { errors.year = fieldMessages.year; continue }
    } else if (readingFields.includes(name)) {
      value = normalizeReading(value)
      if (value === undefined) { errors[name] = readingMessage; continue }
    } else {
      if (name === 'engine' && value === null) value = ''
      if (!safeText(value) || (name !== 'engine' && !value.trim())) { errors[name] = fieldMessages[name]; continue }
      value = value.trim() || null
    }
    if (value !== current[name]) details[name] = value
  }
  if (confirmation !== undefined) {
    if (!confirmation || typeof confirmation !== 'object' || Array.isArray(confirmation)) errors.reading_confirmation = confirmationMessage
    else {
      const acknowledged = {}
      for (const [name, value] of Object.entries(confirmation)) {
        const normalized = normalizeReading(value)
        if (!readingFields.includes(name) || !Object.hasOwn(details, name) || typeof normalized !== 'string') {
          errors.reading_confirmation = confirmationMessage
        } else acknowledged[name] = normalized
      }
      if (Object.keys(acknowledged).length) details.reading_confirmation = acknowledged
    }
  }
  const unchanged = Object.keys(details).length === 0 && Object.keys(errors).length === 0
  return { details, errors, invalid: Object.keys(errors).length > 0, unchanged }
}

export function parseReadingConfirmation(data, submitted) {
  if (!submitted || typeof submitted !== 'object' || Array.isArray(submitted) ||
      !data || typeof data !== 'object' || Array.isArray(data) || Object.keys(data).length !== 3 ||
      !['detail', 'fields', 'current_readings'].every((name) => Object.hasOwn(data, name)) ||
      data.detail !== 'Reading changes require confirmation.' || !Array.isArray(data.fields)) return null
  const fields = readingFields.filter((name) => data.fields.includes(name))
  const readings = data.current_readings
  if (fields.length !== data.fields.length || fields.some((name, index) => data.fields[index] !== name) ||
      !readings || typeof readings !== 'object' || Array.isArray(readings) ||
      Object.keys(readings).length !== fields.length) return null
  for (const name of fields) {
    if (!Object.hasOwn(readings, name) || !Object.hasOwn(submitted, name) ||
        readings[name] === null || !publicReading(readings[name])) return null
    const proposed = submitted[name]
    if (proposed !== null && (!publicReading(proposed) ||
        proposed.replace('.', '').padStart(12, '0') >= readings[name].replace('.', '').padStart(12, '0'))) return null
  }
  if (!fields.length && !Object.keys(submitted.reading_confirmation ?? {}).length) return null
  return { fields: [...fields], currentReadings: { ...readings } }
}
