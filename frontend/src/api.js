export async function checkConnection() {
  const response = await fetch('/api/health/db', {
    credentials: 'same-origin',
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
      credentials: 'same-origin',
      headers: {
        Accept: 'application/json', 'Content-Type': 'application/json',
        'X-GarageGuide-CSRF': '1',
      },
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

const authenticationUnavailable = {
  kind: 'unavailable', message: "We couldn't confirm your session. Please try again.",
}
const authenticationUnexpected = {
  kind: 'unexpected', message: "We couldn't confirm the request. Please try again.",
}

function isAwareTimestamp(value) {
  return typeof value === 'string' &&
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value) &&
    Number.isFinite(Date.parse(value))
}

function publicSession(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data) ||
      Object.keys(data).length !== 2 || !Object.hasOwn(data, 'user') ||
      !Object.hasOwn(data, 'expires_at') || !isPublicAccount(data.user) ||
      data.user.email !== data.user.email.trim().toLowerCase() ||
      !/^[^\s@]+@[^\s@]+$/.test(data.user.email) ||
      !isAwareTimestamp(data.user.created_at) || !isAwareTimestamp(data.expires_at)) return null
  return {
    user: { id: data.user.id, email: data.user.email, created_at: data.user.created_at },
    expires_at: data.expires_at,
  }
}

function authenticationResult(action, status, data) {
  if (status === 200 && action !== 'logout') {
    const session = publicSession(data)
    return session ? { kind: 'success', session } : authenticationUnexpected
  }
  if (!data || typeof data !== 'object' || Array.isArray(data) ||
      Object.keys(data).length !== 1 || !Object.hasOwn(data, 'detail')) return authenticationUnexpected
  if (status === 401 && action === 'login' && data.detail === 'Invalid email or password.') {
    return { kind: 'invalid', message: 'Invalid email or password.', errors: {} }
  }
  if (status === 401 && action === 'session' && data.detail === 'Not authenticated.') {
    return { kind: 'guest' }
  }
  if (status === 422 && action === 'login') {
    const result = validationResult(data.detail)
    if (result.kind !== 'invalid' || Object.keys(result.errors).some((name) =>
      !['email', 'password'].includes(name))) return authenticationUnexpected
    return result
  }
  if (status === 403 && data.detail === 'Request not allowed.') {
    return { kind: 'forbidden', message: 'The request was not accepted. Refresh the page and try again.' }
  }
  if (status === 503 && data.detail === 'Authentication unavailable. Please try again.') {
    return { kind: 'unavailable', message: 'Authentication unavailable. Please try again.' }
  }
  return authenticationUnexpected
}

async function authenticationRequest(action, details, signal) {
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
    if (controller.signal.aborted) return { kind: 'cancelled' }
    const mutation = action !== 'session'
    const response = await fetch(`/api/auth/${action}`, {
      method: mutation ? 'POST' : 'GET', credentials: 'same-origin', signal: controller.signal,
      headers: mutation ? {
        Accept: 'application/json', 'Content-Type': 'application/json', 'X-GarageGuide-CSRF': '1',
      } : { Accept: 'application/json' },
      ...(mutation ? { body: JSON.stringify(details) } : {}),
    })
    if (action === 'logout' && response.status === 204) {
      const body = await response.text()
      controller.signal.throwIfAborted()
      return body === '' ? { kind: 'success' } : authenticationUnexpected
    }
    const body = await response.json()
    controller.signal.throwIfAborted()
    return authenticationResult(action, response.status, body)
  } catch (error) {
    if (signal?.aborted) return { kind: 'cancelled' }
    if (timedOut) {
      return {
        kind: 'network', message: 'The request timed out. It may already have completed. Please check before trying again.',
      }
    }
    if (error instanceof TypeError || error?.name === 'AbortError') {
      return { kind: 'network', message: "We couldn't confirm the request. Check your connection and try again." }
    }
    return authenticationUnexpected
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', cancel)
  }
}

export function loginAccount(details, signal) {
  return authenticationRequest('login', details, signal)
}

export async function getSession(signal) {
  const result = await authenticationRequest('session', undefined, signal)
  return ['success', 'guest', 'cancelled'].includes(result.kind) ? result : authenticationUnavailable
}

export function logoutAccount(signal) {
  return authenticationRequest('logout', {}, signal)
}
