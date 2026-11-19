import { parseSessionDeadline } from './sessionDeadline.js'
import { isVehicleId, vehicleIdMessage } from './vehicleValidation.js'

export const isServiceId = isVehicleId
export const serviceIdMessage = 'Enter a service ID from 1 through 2147483647 using digits without leading zeroes.'
export const serviceFields = ['service_date', 'service_type', 'description', 'mileage', 'operating_hours', 'cost', 'notes']
export const serviceTypes = ['maintenance', 'repair', 'inspection', 'diagnostic']
const text = (value) => typeof value === 'string' && value.isWellFormed() && !value.includes('\0')
const object = (value) => value && typeof value === 'object' && !Array.isArray(value)
export const serviceMessages = {
  service_date: 'Enter a valid service date on or before today using YYYY-MM-DD.',
  service_type: 'Choose maintenance, repair, inspection, or diagnostic.',
  description: 'Enter nonblank text with valid Unicode and no NUL.',
  mileage: 'Enter a nonnegative decimal string with at most one decimal place, up to 99999999999.9.',
  operating_hours: 'Enter a nonnegative decimal string with at most one decimal place, up to 99999999999.9.',
  cost: 'Enter a nonnegative decimal string with at most two decimal places, up to 9999999999.99.',
  notes: 'Enter valid Unicode characters without NUL.',
  confirm_removal: 'Confirm removal with true.',
}
const types = {
  missing: 'Field required.', string_type: 'Enter text.', extra_forbidden: 'Unexpected fields are not allowed.',
  json_invalid: 'Provide valid JSON.', model_type: 'Provide a JSON object.',
  model_attributes_type: 'Provide a JSON object.', value_error: 'Enter a valid value.',
}

export function isServiceDate(value) {
  if (typeof value !== 'string' || !/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(value)) return false
  const [year, month, day] = value.split('-').map(Number)
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)
  return year >= 1 && month >= 1 && month <= 12 && day >= 1 &&
    day <= [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
}

// Decimal strings only: no binary floating-point conversion of readings or USD.
function decimal(value, cost = false) {
  if (value === null || (typeof value === 'string' && !value.trim())) return null
  const places = cost ? 2 : 1
  if (typeof value !== 'string' || !(cost ? /^[0-9]+(?:\.[0-9]{1,2})?$/ : /^[0-9]+(?:\.[0-9])?$/).test(value.trim())) return undefined
  const [whole, fraction = ''] = value.trim().split('.')
  const digits = whole.replace(/^0+(?=[0-9])/, '')
  return digits.length <= (cost ? 10 : 11) ? `${digits}.${fraction.padEnd(places, '0')}` : undefined
}

export function isPublicService(record) {
  const keys = ['id', 'vehicle_id', ...serviceFields, 'created_at']
  if (!object(record) || Object.keys(record).length !== keys.length || !keys.every((key) => Object.hasOwn(record, key)) ||
      ![record.id, record.vehicle_id].every((id) => Number.isInteger(id) && isVehicleId(String(id))) ||
      !isServiceDate(record.service_date) || !serviceTypes.includes(record.service_type) ||
      !text(record.description) || !record.description.trim() || record.description.trim() !== record.description ||
      !(record.notes === null || (text(record.notes) && record.notes.trim() && record.notes.trim() === record.notes)) ||
      !parseSessionDeadline(record.created_at)) return false
  return ['mileage', 'operating_hours', 'cost'].every((key) => record[key] === null ||
    (typeof record[key] === 'string' && decimal(record[key], key === 'cost') === record[key]))
}

export function serviceDraft(record) {
  return Object.fromEntries(serviceFields.map((key) => [key, record?.[key] ?? '']))
}

export function prepareServiceInput(values, current = null) {
  const details = {}, errors = {}
  if (!object(values) || Object.keys(values).some((key) => !serviceFields.includes(key)) ||
      (current !== null && !isPublicService(current))) return { invalid: true, errors }
  for (const key of serviceFields) {
    if (!Object.hasOwn(values, key)) {
      if (!current && ['service_date', 'service_type', 'description'].includes(key)) errors[key] = 'Field required.'
      continue
    }
    let value = values[key]
    if (key === 'service_date') {
      // The backend's injectable local calendar decides "today", not the browser clock.
      if (!isServiceDate(value)) { errors[key] = serviceMessages[key]; continue }
    } else if (key === 'service_type') {
      if (!serviceTypes.includes(value)) { errors[key] = serviceMessages[key]; continue }
    } else if (['mileage', 'operating_hours', 'cost'].includes(key)) {
      value = decimal(value, key === 'cost')
      if (value === undefined) { errors[key] = serviceMessages[key]; continue }
    } else {
      if (key === 'notes' && value === null) value = ''
      if (!text(value) || (key === 'description' && !value.trim())) { errors[key] = serviceMessages[key]; continue }
      value = value.trim() || null
    }
    if (!current || value !== current[key]) details[key] = value
  }
  return { details, errors, invalid: Object.keys(errors).length > 0, unchanged: Boolean(current) && !Object.keys(details).length && !Object.keys(errors).length }
}

export function parseServiceErrors(detail, operation) {
  if (!Array.isArray(detail) || !detail.length) return null
  const errors = {}
  for (const entry of detail) {
    if (!object(entry) || Object.keys(entry).length !== 3 || !['loc', 'msg', 'type'].every((key) => Object.hasOwn(entry, key)) ||
        !Array.isArray(entry.loc) || typeof entry.type !== 'string' || !Object.hasOwn(types, entry.type)) return null
    const [where, field] = entry.loc
    if (where === 'path' && entry.loc.length === 2 && ['vehicle_id', 'service_id'].includes(field)) {
      const message = field === 'vehicle_id' ? vehicleIdMessage : serviceIdMessage
      if (entry.type !== 'value_error' || entry.msg !== message) return null
      errors[field] = message
      continue
    }
    const fields = operation === 'remove' ? ['confirm_removal'] : serviceFields
    if (where !== 'body' || !['create', 'update', 'remove'].includes(operation) ||
        (entry.loc.length !== 1 && !(entry.loc.length === 2 && fields.includes(field)))) return null
    const allowed = entry.type === 'value_error'
      ? [field ? serviceMessages[field] : types.value_error,
        ...(operation === 'update' && !field ? ['Provide at least one editable service field.'] : []),
        ...(operation === 'update' && ['service_date', 'service_type', 'description'].includes(field) ? ['This field cannot be cleared.'] : [])]
      : [types[entry.type]]
    if (!allowed.includes(entry.msg)) return null
    if (field) errors[field] ??= entry.msg
  }
  return errors
}
