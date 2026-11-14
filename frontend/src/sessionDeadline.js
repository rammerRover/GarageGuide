export function parseSessionDeadline(value) {
  if (typeof value !== 'string') return null
  const parts = value.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|([+-])(\d{2}):(\d{2}))$/)
  if (!parts || !Number.isFinite(Date.parse(value))) return null
  const [, y, m, d, h, minute, second, , offsetHour, offsetMinute] = parts
  const year = Number(y)
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  if (year < 1 || Number(m) < 1 || Number(m) > 12 || Number(d) < 1 || Number(d) > days[Number(m) - 1] ||
      Number(h) > 23 || Number(minute) > 59 || Number(second) > 59 ||
      (offsetHour && (Number(offsetHour) > 23 || Number(offsetMinute) > 59))) return null
  return value
}
