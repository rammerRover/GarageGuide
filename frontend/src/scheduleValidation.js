import { parseSessionDeadline } from './sessionDeadline.js'
import { isServiceDate, trimServiceText } from './serviceValidation.js'
import { isVehicleId, vehicleIdMessage } from './vehicleValidation.js'

export const schedulePairs = [
  ['interval_days', 'baseline_date'],
  ['interval_miles', 'baseline_mileage'],
  ['interval_hours', 'baseline_hours'],
]
export const scheduleFields = ['name', ...schedulePairs.flat(), 'source_notes']
export const scheduleIdMessage = 'Enter a schedule ID from 1 through 2147483647 using digits without leading zeroes.'
export const duplicateScheduleMessage = 'Review the matching schedules before saving a separate task.'
const decimalIntervalMessage = 'Enter a positive decimal string with at most one decimal place, up to 99999999999.9.'
const baselineReadingMessage = 'Enter a nonnegative decimal string with at most one decimal place, up to 99999999999.9.'
const fieldMessages = {
  name: 'Enter nonblank text.',
  interval_days: 'Enter a whole number from 1 through 2147483647.',
  interval_miles: decimalIntervalMessage,
  interval_hours: decimalIntervalMessage,
  baseline_date: 'Enter a valid baseline date on or before today using YYYY-MM-DD.',
  baseline_mileage: baselineReadingMessage,
  baseline_hours: baselineReadingMessage,
  source_notes: 'Enter valid Unicode characters without NUL.',
  reviewed_duplicate_ids: 'Provide distinct schedule IDs from the duplicate review.',
}
const completeMessages = {
  interval_days: 'Enable at least one maintenance interval.',
  baseline_date: 'Set both the day interval and its baseline date on or before today, or clear both.',
  baseline_mileage: 'Set both the mileage interval and its baseline, or clear both.',
  baseline_hours: 'Set both the operating-hour interval and its baseline, or clear both.',
}
const typeMessages = {
  missing: 'Field required.', extra_forbidden: 'Unexpected fields are not allowed.',
  json_invalid: 'Provide valid JSON.', model_type: 'Provide a JSON object.',
  model_attributes_type: 'Provide a JSON object.',
}
const object = (value) => value && typeof value === 'object' && !Array.isArray(value)
export const exactScheduleShape = (value, keys) => object(value) &&
  Object.keys(value).length === keys.length && keys.every((key) => Object.hasOwn(value, key))
const validText = (value) => typeof value === 'string' && value.isWellFormed() && !value.includes('\0')
const intId = (value) => Number.isInteger(value) && isVehicleId(String(value))
const reading = (value) => typeof value === 'string' && trimServiceText(value) === value &&
  /^(?:0|[1-9][0-9]{0,10})\.[0-9]$/.test(value)

export function isPublicSchedule(value) {
  return exactScheduleShape(value, ['id', 'vehicle_id', ...scheduleFields, 'created_at']) &&
    intId(value.id) && intId(value.vehicle_id) && validText(value.name) && value.name.length > 0 &&
    (value.source_notes === null || validText(value.source_notes)) && Boolean(parseSessionDeadline(value.created_at)) &&
    (value.interval_days === null || intId(value.interval_days)) &&
    (value.baseline_date === null || (isServiceDate(value.baseline_date) && value.baseline_date.length === 10)) &&
    ['interval_miles', 'interval_hours'].every((key) => value[key] === null || (reading(value[key]) && value[key] !== '0.0')) &&
    ['baseline_mileage', 'baseline_hours'].every((key) => value[key] === null || reading(value[key]))
}

export function isOwnedScheduleList(records, vehicleId, excludedId = null) {
  return Array.isArray(records) && records.every((record, index) =>
    isPublicSchedule(record) && String(record.vehicle_id) === vehicleId &&
    String(record.id) !== excludedId && (index === 0 || records[index - 1].id < record.id))
}

export function parseScheduleConflict(data, vehicleId, scheduleId) {
  return exactScheduleShape(data, ['code', 'detail', 'matches']) &&
    data.code === 'duplicate_schedule_name' && data.detail === duplicateScheduleMessage &&
    isOwnedScheduleList(data.matches, vehicleId, scheduleId) ? data.matches : null
}

export function scheduleDraft(record) {
  return Object.fromEntries(scheduleFields.map((key) => [key, String(record?.[key] ?? '')]))
}

function normalizeScheduleReading(raw) {
  if (!/^[0-9]+(?:\.[0-9])?$/.test(raw)) return undefined
  const [whole, fraction = '0'] = raw.split('.')
  const digits = whole.replace(/^0+(?=[0-9])/, '')
  return digits.length <= 11 ? `${digits}.${fraction}` : undefined
}

export function prepareScheduleInput(draft, current = null) {
  const values = {}, errors = {}
  const saved = scheduleDraft(current)
  for (const key of scheduleFields) {
    const raw = draft[key]
    const text = validText(raw) ? trimServiceText(raw) : null
    if (text === null || (key === 'name' && !text)) errors[key] = fieldMessages[key]
    else if (current && raw === saved[key]) values[key] = current[key]
    else if (!text) values[key] = null
    else if (key === 'name' || key === 'source_notes') values[key] = text
    else if (key === 'baseline_date') {
      // The server's local calendar decides whether a baseline date is in the future.
      if (isServiceDate(text)) values[key] = text
      else errors[key] = fieldMessages[key]
    } else if (key === 'interval_days') {
      if (isVehicleId(text)) values[key] = Number(text)
      else errors[key] = fieldMessages[key]
    } else {
      const decimal = normalizeScheduleReading(text)
      if (decimal === undefined || (key.startsWith('interval_') && decimal === '0.0')) errors[key] = fieldMessages[key]
      else values[key] = decimal
    }
  }
  for (const [interval, baseline] of schedulePairs) {
    if (!errors[interval] && !errors[baseline] && (values[interval] === null) !== (values[baseline] === null)) {
      errors[baseline] = completeMessages[baseline]
    }
  }
  if (schedulePairs.every(([interval, baseline]) => values[interval] === null && values[baseline] === null)) {
    errors.interval_days = completeMessages.interval_days
  }
  const details = Object.fromEntries(Object.entries(values).filter(([field, value]) => !current || value !== current[field]))
  return { details, errors, invalid: Object.keys(errors).length > 0, unchanged: Boolean(current) && Object.keys(details).length === 0 }
}

export function parseScheduleErrors(detail, mutation) {
  if (!Array.isArray(detail) || detail.length === 0) return null
  const errors = {}
  for (const entry of detail) {
    if (!exactScheduleShape(entry, ['loc', 'type', 'msg']) || !Array.isArray(entry.loc) || typeof entry.type !== 'string') return null
    const [where, field] = entry.loc
    if (where === 'path' && entry.loc.length === 2 && (field === 'vehicle_id' || (mutation && field === 'schedule_id'))) {
      const message = field === 'vehicle_id' ? vehicleIdMessage : scheduleIdMessage
      if (entry.type !== 'value_error' || entry.msg !== message) return null
      errors[field] = message
      continue
    }
    if (where !== 'body' || !mutation ||
        !(entry.loc.length === 1 || (entry.loc.length === 2 && typeof field === 'string' && Object.hasOwn(fieldMessages, field)))) return null
    const allowed = entry.type === 'value_error'
      ? field ? [fieldMessages[field], completeMessages[field]].filter(Boolean)
        : ['Enter a valid value.', 'Provide at least one editable schedule field.']
      : Object.hasOwn(typeMessages, entry.type) ? [typeMessages[entry.type]] : []
    if (!allowed.includes(entry.msg)) return null
    if (field) errors[field] ??= entry.msg
  }
  return errors
}
