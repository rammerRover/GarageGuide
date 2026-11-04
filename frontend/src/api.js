export async function checkConnection() {
  const response = await fetch('/api/health/db', {
    signal: AbortSignal.timeout(10000),
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) throw new Error('Connection unavailable')
  const result = await response.json()
  if (result.status !== 'ok' || result.database !== 'connected' || result.schema !== 'ready') {
    throw new Error('Unexpected connection response')
  }
}

const fieldNames = new Set(['email', 'password', 'password_confirmation'])
const safeMessages = new Set([
  'Field required.', 'Enter text.', 'Enter a valid value.', 'Provide valid JSON.',
  'Provide a JSON object.', 'Enter a valid email address.',
  'Enter valid Unicode characters.', 'Use between 15 and 128 characters.',
  'Passwords must match.', 'Enter valid credentials.',
])
const unexpected = {
  kind: 'unexpected', message: "We couldn't confirm registration. Please try again.",
}

function isPublicAccount(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) return false
  const keys = Object.keys(data)
  return keys.length === 3 && ['id', 'email', 'created_at'].every((key) => keys.includes(key)) &&
    Number.isSafeInteger(data.id) && data.id > 0 &&
    typeof data.email === 'string' && data.email.trim().length > 0 &&
    typeof data.created_at === 'string' && data.created_at.includes('T') &&
    /(?:Z|[+-]\d{2}:\d{2})$/.test(data.created_at) &&
    !Number.isNaN(Date.parse(data.created_at))
}

function validationResult(detail) {
  if (!Array.isArray(detail) || detail.length === 0) return unexpected
  const errors = {}
  for (const entry of detail) {
    if (!entry || typeof entry !== 'object' || Object.keys(entry).length !== 3 ||
        !['loc', 'msg', 'type'].every((key) => Object.hasOwn(entry, key)) ||
        !Array.isArray(entry.loc) || entry.loc[0] !== 'body' ||
        typeof entry.type !== 'string' || !safeMessages.has(entry.msg)) return unexpected
    if (entry.loc.length === 2 && fieldNames.has(entry.loc[1])) {
      errors[entry.loc[1]] ??= entry.msg
    } else if (entry.loc.length !== 1) {
      return unexpected
    }
  }
  return { kind: 'invalid', errors, message: 'Check your details and try again.' }
}

function registrationResult(status, data) {
  if (status === 201) return isPublicAccount(data) ? { kind: 'success' } : unexpected
  if (!data || typeof data !== 'object' || Array.isArray(data) ||
      Object.keys(data).length !== 1 || !Object.hasOwn(data, 'detail')) return unexpected
  if (status === 422) return validationResult(data.detail)
  if (status === 409 && data.detail === 'An account with this email already exists.') {
    return {
      kind: 'invalid', errors: { email: 'An account with this email already exists.' },
      message: 'An account with this email already exists.',
    }
  }
  if (status === 503 && data.detail === 'Registration unavailable. Please try again.') {
    return { kind: 'unavailable', message: 'Registration unavailable. Please try again.' }
  }
  return unexpected
}

export async function registerAccount(details, signal) {
  const controller = new AbortController()
  let timedOut = false
  const cancel = () => controller.abort()
  signal?.addEventListener('abort', cancel, { once: true })
  if (signal?.aborted) cancel()
  const timer = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, 10000)
  try {
    const response = await fetch('/api/auth/register', {
      method: 'POST', signal: controller.signal,
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify(details),
    })
    const data = await response.json()
    return registrationResult(response.status, data)
  } catch (error) {
    if (signal?.aborted) return { kind: 'cancelled' }
    if (timedOut) {
      return { kind: 'network', message: 'The request timed out. Your account may already have been created.' }
    }
    if (error instanceof TypeError || error?.name === 'AbortError') {
      return { kind: 'network', message: "We couldn't confirm registration. Check your connection and try again." }
    }
    return unexpected
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', cancel)
  }
}
