import { isServiceId, serviceIdMessage, trimServiceText } from './serviceValidation.js'
import { vehicleIdMessage } from './vehicleValidation.js'

export const isServicePartId = isServiceId
export const snapshotIdMessage = 'Enter a part snapshot ID from 1 through 2147483647 using digits without leading zeroes.'
export const partMessages = {
  source: 'Choose manual or catalog entry.', name: 'Enter nonblank text with valid Unicode and no NUL.',
  part_number: 'Enter valid Unicode characters without NUL.', manufacturer: 'Enter valid Unicode characters without NUL.',
  quantity: 'Enter a whole number from 1 through 2147483647.', notes: 'Enter valid Unicode characters without NUL.',
  preview: 'Look up and review a catalog part before saving.', confirm_removal: 'Confirm removal with true.',
}
export const catalogMissingMessage = 'Catalog part not found. Look it up again or enter the part manually.'
export const catalogConflictMessage = 'Catalog part changed or is no longer available. Look it up again or enter the part manually.'
export const partFields = ['name', 'part_number', 'manufacturer', 'quantity', 'notes']
export const previewFields = ['id', 'manufacturer', 'part_number', 'name', 'category']
const text = (value) => typeof value === 'string' && value.isWellFormed() && !value.includes('\0')
const nonblank = (value) => text(value) && trimServiceText(value).length > 0
const integer = (value) => Number.isInteger(value) && value >= 1 && value <= 2147483647
export const exactPartShape = (value, fields) => Boolean(value && typeof value === 'object' && !Array.isArray(value) &&
  Object.keys(value).length === fields.length && fields.every((field) => Object.hasOwn(value, field)))

export function isCatalogPreview(value) {
  return exactPartShape(value, previewFields) && integer(value.id) && previewFields.slice(1).every((field) => nonblank(value[field]))
}

export function isPartSnapshot(value) {
  return exactPartShape(value, ['id', 'service_record_id', 'part_id', ...partFields]) &&
    integer(value.id) && integer(value.service_record_id) && (value.part_id === null || integer(value.part_id)) &&
    nonblank(value.name) && integer(value.quantity) &&
    ['part_number', 'manufacturer', 'notes'].every((field) => value[field] === null || text(value[field]))
}

export function isPartList(value, vehicleId, serviceId) {
  return exactPartShape(value, ['vehicle_id', 'service_record_id', 'parts']) &&
    integer(value.vehicle_id) && String(value.vehicle_id) === vehicleId &&
    integer(value.service_record_id) && String(value.service_record_id) === serviceId &&
    Array.isArray(value.parts) && value.parts.every((part) => isPartSnapshot(part) && String(part.service_record_id) === serviceId) &&
    new Set(value.parts.map((part) => part.id)).size === value.parts.length
}

export function isPartRemoval(value, serviceId, snapshotId) {
  return exactPartShape(value, ['id', 'service_record_id', 'deleted']) && integer(value.id) &&
    String(value.id) === snapshotId && integer(value.service_record_id) && String(value.service_record_id) === serviceId && value.deleted === true
}

export const partDraft = () => ({ name: '', part_number: '', manufacturer: '', quantity: '1', notes: '' })
const optional = (value) => value === undefined || value === null ? null : text(value) ? trimServiceText(value) || null : undefined
const quantity = (value) => value === undefined ? 1 : integer(value) ? value :
  typeof value === 'string' && /^[0-9]+$/.test(value) && integer(Number(value)) ? Number(value) : undefined

export function preparePartLookup(values) {
  const errors = {}
  if (!values || typeof values !== 'object' || Array.isArray(values) ||
      Object.keys(values).some((field) => !['manufacturer', 'part_number'].includes(field))) return { invalid: true, errors }
  for (const field of ['manufacturer', 'part_number']) if (!nonblank(values[field])) errors[field] = partMessages.name
  return Object.keys(errors).length ? { invalid: true, errors } : {
    invalid: false, details: { manufacturer: values.manufacturer, part_number: values.part_number },
  }
}

export function preparePartInput(values) {
  const errors = {}
  if (!values || typeof values !== 'object' || Array.isArray(values) || !['manual', 'catalog'].includes(values.source)) {
    return { invalid: true, errors: { source: partMessages.source } }
  }
  const allowed = values.source === 'manual' ? ['source', ...partFields] : ['source', 'preview', 'quantity', 'notes']
  if (Object.keys(values).some((field) => !allowed.includes(field))) return { invalid: true, errors }
  const details = { source: values.source, quantity: quantity(values.quantity), notes: optional(values.notes) }
  if (details.quantity === undefined) errors.quantity = partMessages.quantity
  if (details.notes === undefined) errors.notes = partMessages.notes
  if (values.source === 'manual') {
    if (!nonblank(values.name)) errors.name = partMessages.name
    else details.name = trimServiceText(values.name)
    for (const field of ['part_number', 'manufacturer']) {
      details[field] = optional(values[field])
      if (details[field] === undefined) errors[field] = partMessages[field]
    }
  } else if (!isCatalogPreview(values.preview)) errors.preview = partMessages.preview
  else details.preview = { ...values.preview }
  return Object.keys(errors).length ? { invalid: true, errors } : { invalid: false, details }
}

export function matchesPartInput(part, details) {
  if (!isPartSnapshot(part)) return false
  const identity = details.source === 'catalog' ? { part_id: details.preview.id, name: details.preview.name,
    part_number: details.preview.part_number, manufacturer: details.preview.manufacturer } : {
    part_id: null, name: details.name, part_number: details.part_number, manufacturer: details.manufacturer,
  }
  return Object.entries({ ...identity, quantity: details.quantity, notes: details.notes }).every(([field, value]) => part[field] === value)
}

export function parsePartErrors(entries) {
  const types = { missing: 'Field required.', string_type: 'Enter text.', extra_forbidden: 'Unexpected fields are not allowed.',
    json_invalid: 'Provide valid JSON.', model_type: 'Provide a JSON object.', model_attributes_type: 'Provide a JSON object.', value_error: 'Enter a valid value.' }
  const allowedMessages = new Set([...Object.values(types), ...Object.values(partMessages), vehicleIdMessage, serviceIdMessage, snapshotIdMessage])
  if (!Array.isArray(entries) || !entries.length) return null
  const errors = {}
  for (const entry of entries) {
    if (!exactPartShape(entry, ['loc', 'msg', 'type']) || !Array.isArray(entry.loc) ||
        !entry.loc.every((value) => typeof value === 'string') || typeof entry.type !== 'string' ||
        !Object.hasOwn(types, entry.type) || !allowedMessages.has(entry.msg)) return null
    const [root, field, nested] = entry.loc
    if (root === 'path' && entry.loc.length === 2 && ['vehicle_id', 'service_id', 'snapshot_id'].includes(field)) errors[field] ??= entry.msg
    else if (root === 'body' && entry.loc.length === 1) continue
    else if (root === 'body' && entry.loc.length === 2 && Object.hasOwn(partMessages, field)) errors[field] ??= entry.msg
    else if (root === 'body' && entry.loc.length === 3 && field === 'preview' && previewFields.includes(nested)) errors.preview ??= entry.msg
    else return null
  }
  return errors
}
