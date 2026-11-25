import { exactScheduleShape, isOwnedScheduleList } from './scheduleValidation.js'
import { isServiceDate } from './serviceValidation.js'
import { isPublicVehicle } from './vehicleValidation.js'

export const statusLabels = {
  upcoming: 'Upcoming', due: 'Due', overdue: 'Overdue', needs_information: 'Needs information',
}
export const readingTimestampWarnings = {
  missing: 'The time of the last reading change is unavailable.',
  future: 'The recorded time of the last reading change is in the future.',
  at_least_30_days_old: 'The saved readings last changed at least 30 days ago.',
}
const reminderPriority = { overdue: 0, due: 1, needs_information: 2 }
const kinds = {
  days: { label: 'Calendar', interval: 'interval_days', unit: 'days' },
  mileage: { label: 'Mileage', interval: 'interval_miles', reading: 'mileage', unit: 'mi' },
  hours: { label: 'Operating hours', interval: 'interval_hours', reading: 'operating_hours', unit: 'hours' },
}
const issues = ['missing_reading', 'below_baseline', 'invalid_baseline']
const validDate = (value) => isServiceDate(value) && value.length === 10
const exactReading = (value) => typeof value === 'string' && /^-?(?:0|[1-9][0-9]{0,11})\.[0-9]$/.test(value) && value !== '-0.0'
const isStatus = (value) => typeof value === 'string' && Object.hasOwn(statusLabels, value)

function isLimit(limit, kind, schedule) {
  if (!exactScheduleShape(limit, ['kind', 'status', 'due_value', 'remaining', 'issue']) || limit.kind !== kind ||
      !isStatus(limit.status)) return false
  const { due_value: target, remaining, issue } = limit
  if (issue !== null && (!issues.includes(issue) || (kind === 'days' && issue !== 'invalid_baseline'))) return false
  if ((limit.status === 'needs_information') !== (issue !== null) ||
      (remaining === null) !== (issue !== null)) return false
  if (issue === 'invalid_baseline') return target === null
  if (kind === 'days') return Number.isSafeInteger(remaining) &&
    (target === null ? validDate(schedule.baseline_date) && remaining > 0 : validDate(target))
  return exactReading(target) && !target.startsWith('-') && (remaining === null || exactReading(remaining))
}

export function isMaintenanceStatusSnapshot(data, vehicleId) {
  if (!exactScheduleShape(data, ['vehicle', 'as_of_date', 'readings_timestamp_warning', 'schedules']) ||
      !isPublicVehicle(data.vehicle) || String(data.vehicle.id) !== vehicleId || !validDate(data.as_of_date) ||
      (data.readings_timestamp_warning !== null && (typeof data.readings_timestamp_warning !== 'string' ||
       !Object.hasOwn(readingTimestampWarnings, data.readings_timestamp_warning))) ||
      !Array.isArray(data.schedules)) return false
  if (!isOwnedScheduleList(data.schedules.map((entry) => entry?.schedule), vehicleId)) return false
  return data.schedules.every((entry) => {
    if (!exactScheduleShape(entry, ['schedule', 'status', 'limits']) || !isStatus(entry.status) ||
        !Array.isArray(entry.limits)) return false
    const enabled = Object.keys(kinds).filter((kind) => entry.schedule[kinds[kind].interval] !== null)
    return enabled.length === entry.limits.length && entry.limits.every((limit, index) => isLimit(limit, enabled[index], entry.schedule))
  })
}

export function maintenanceReminders(entries) {
  return entries.filter((entry) => Object.hasOwn(reminderPriority, entry.status))
    .sort((left, right) => reminderPriority[left.status] - reminderPriority[right.status] ||
      left.schedule.id - right.schedule.id)
}

export function maintenanceTriggers(limits) {
  return limits.filter(({ status }) => status === 'due' || status === 'overdue')
    .map(({ kind, status }) => `${kinds[kind].label} (${statusLabels[status]})`)
}

export function describeMaintenanceLimit(limit, schedule, vehicle) {
  const { label, reading, unit } = kinds[limit.kind]
  const target = limit.due_value === null ?
    limit.kind === 'days' && limit.issue === null ? `${schedule.baseline_date} + ${schedule.interval_days} days` : 'Unavailable'
    : reading ? `${limit.due_value} ${unit}` : limit.due_value
  const issue = {
    missing_reading: 'The last saved reading is unavailable.',
    below_baseline: 'The last saved reading is below the baseline.',
    invalid_baseline: 'Review the baseline for this limit.',
  }[limit.issue]
  return {
    label,
    status: reading && limit.issue === null ? `${statusLabels[limit.status]} based on the last saved reading` : statusLabels[limit.status],
    target,
    remaining: limit.remaining === null ? 'Unavailable' : `${limit.remaining} ${unit}`,
    savedReading: reading && (vehicle[reading] === null ? 'Not recorded' : `${vehicle[reading]} ${unit}`),
    issue,
  }
}
