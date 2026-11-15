import { parseSessionDeadline } from './sessionDeadline.js'
import {
  isPublicVehicle, isVehicleId, parseReadingConfirmation, parseVehicleErrors,
  prepareVehicleInput, prepareVehiclePatch, vehicleIdMessage,
} from './vehicleValidation.js'

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

const uncertainVehicle = 'The vehicle may have been created. Check your garage before submitting again.'
const unexpectedVehicle = "We couldn't confirm the vehicle response."

function vehicleResult(method, response, data) {
  const successStatus = method === 'GET' ? 200 : 201
  const unexpected = {
    kind: method === 'POST' ? 'uncertain' : 'unexpected',
    message: `${unexpectedVehicle}${method === 'POST' ? ` ${uncertainVehicle}` : ' Please try again.'}`,
  }
  if (response.status === successStatus) {
    const deadline = parseSessionDeadline(response.headers.get('X-GarageGuide-Session-Expires-At'))
    if (!deadline) return unexpected
    if (method === 'POST') return isPublicVehicle(data) ? { kind: 'success', vehicle: data, deadline } : unexpected
    if (!data || typeof data !== 'object' || Array.isArray(data) || Object.keys(data).length !== 1 ||
        !Object.hasOwn(data, 'vehicles') || !Array.isArray(data.vehicles) || !data.vehicles.every(isPublicVehicle) ||
        new Set(data.vehicles.map((vehicle) => vehicle.id)).size !== data.vehicles.length) return unexpected
    return { kind: 'success', vehicles: data.vehicles, deadline }
  }
  if (!data || typeof data !== 'object' || Array.isArray(data) ||
      Object.keys(data).length !== 1 || !Object.hasOwn(data, 'detail')) return unexpected
  if (response.status === 422 && method === 'POST') {
    const errors = parseVehicleErrors(data.detail)
    return errors ? { kind: 'invalid', errors, message: 'Check your details and try again.' } : unexpected
  }
  if (response.status === 401 && data.detail === 'Not authenticated.') return { kind: 'guest' }
  if (response.status === 403 && data.detail === 'Request not allowed.') {
    return { kind: 'forbidden', message: 'The request was not accepted. Refresh the page and try again.' }
  }
  if (response.status === 503 && data.detail === 'Authentication unavailable. Please try again.') {
    return { kind: 'authentication-unavailable', message: "We couldn't confirm your session. Please try again." }
  }
  if (response.status === 503 && data.detail === 'Vehicles unavailable. Please try again.') {
    return { kind: 'unavailable', message: method === 'POST' ? `Vehicle creation is unavailable. ${uncertainVehicle}` : 'Your garage is unavailable. Please try again.' }
  }
  if (response.status === 500 && data.detail === 'Internal server error') {
    return { kind: 'unexpected', message: method === 'POST' ? `Vehicle creation was not confirmed. ${uncertainVehicle}` : 'Your garage could not be loaded. Please try again.' }
  }
  return unexpected
}

export const uncertainVehicleUpdate = 'The update may have completed. Reload this vehicle and check its current values before submitting again.'

function profileResult(method, response, data, vehicleId, submitted) {
  const mutation = method === 'PATCH'
  const unexpected = {
    kind: mutation ? 'uncertain' : 'unexpected', uncertain: mutation,
    message: mutation ? uncertainVehicleUpdate : "We couldn't confirm the vehicle response. Please try again.",
  }
  if (response.status === 200) {
    const deadline = parseSessionDeadline(response.headers.get('X-GarageGuide-Session-Expires-At'))
    return isPublicVehicle(data) && String(data.id) === vehicleId && deadline
      ? { kind: 'success', vehicle: data, deadline } : unexpected
  }
  if (response.status === 409 && mutation) {
    const confirmation = parseReadingConfirmation(data, submitted)
    return confirmation ? {
      kind: confirmation.fields.length ? 'confirmation-required' : 'reload-required', ...confirmation,
      message: confirmation.fields.length ? 'Review and confirm the reading changes.' : 'The readings changed. Reload this vehicle and review its current values before saving.',
    } : unexpected
  }
  if (!data || typeof data !== 'object' || Array.isArray(data) ||
      Object.keys(data).length !== 1 || !Object.hasOwn(data, 'detail')) return unexpected
  if (response.status === 422) {
    const errors = parseVehicleErrors(data.detail, { patch: true })
    if (!mutation && (!errors || data.detail.some((entry) =>
      entry.loc.length !== 2 || entry.loc[0] !== 'path' || entry.loc[1] !== 'vehicle_id'))) return unexpected
    return errors ? { kind: 'invalid', errors, message: 'Check your details and try again.' } : unexpected
  }
  if (response.status === 404 && data.detail === 'Vehicle not found.') return { kind: 'not-found', message: 'Vehicle not found.' }
  if (response.status === 401 && data.detail === 'Not authenticated.') return { kind: 'guest' }
  if (response.status === 403 && data.detail === 'Request not allowed.') {
    return { kind: 'forbidden', message: 'The request was not accepted. Refresh the page and try again.' }
  }
  if (response.status === 503 && data.detail === 'Authentication unavailable. Please try again.') {
    return { kind: 'authentication-unavailable', message: "We couldn't confirm your session. Please try again." }
  }
  if (response.status === 503 && data.detail === 'Vehicles unavailable. Please try again.') {
    return { kind: 'unavailable', uncertain: mutation, message: mutation ? uncertainVehicleUpdate : 'This vehicle is unavailable. Please try again.' }
  }
  if (response.status === 500 && data.detail === 'Internal server error') return unexpected
  return unexpected
}

async function vehicleRequest(method, details, signal, vehicleId = null) {
  const controller = new AbortController()
  let timedOut = false
  const cancel = () => controller.abort()
  signal?.addEventListener('abort', cancel, { once: true })
  if (signal?.aborted) cancel()
  const timer = setTimeout(() => { timedOut = true; controller.abort() }, 10000)
  try {
    if (controller.signal.aborted) return { kind: 'cancelled' }
    const response = await fetch(vehicleId === null ? '/api/vehicles' : `/api/vehicles/${vehicleId}`, {
      method, credentials: 'same-origin', signal: controller.signal,
      headers: method === 'GET' ? { Accept: 'application/json' } : {
        Accept: 'application/json', 'Content-Type': 'application/json', 'X-GarageGuide-CSRF': '1',
      },
      ...(method === 'POST' || method === 'PATCH' ? { body: JSON.stringify(details) } : {}),
    })
    const data = await response.json()
    controller.signal.throwIfAborted()
    return vehicleId === null ? vehicleResult(method, response, data) : profileResult(method, response, data, vehicleId, details)
  } catch (error) {
    if (signal?.aborted) return { kind: 'cancelled' }
    if (vehicleId !== null) {
      const mutation = method === 'PATCH'
      return {
        kind: timedOut || error instanceof TypeError || error?.name === 'AbortError' ? 'network' : mutation ? 'uncertain' : 'unexpected',
        uncertain: mutation, message: mutation ? uncertainVehicleUpdate : 'This vehicle could not be loaded. Check your connection and try again.',
      }
    }
    if (timedOut || error instanceof TypeError || error?.name === 'AbortError') {
      return { kind: 'network', message: method === 'POST' ? `${timedOut ? 'The request timed out.' : 'Creation could not be confirmed.'} ${uncertainVehicle}` : 'Your garage could not be loaded. Check your connection and try again.' }
    }
    return { kind: method === 'POST' ? 'uncertain' : 'unexpected', message: `${unexpectedVehicle}${method === 'POST' ? ` ${uncertainVehicle}` : ' Please try again.'}` }
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', cancel)
  }
}

export function listVehicles(signal) {
  return vehicleRequest('GET', undefined, signal)
}

export function createVehicle(details, signal) {
  const prepared = prepareVehicleInput(details)
  if (prepared.invalid) return Promise.resolve({ kind: 'invalid', errors: prepared.errors, message: 'Check your details and try again.' })
  return vehicleRequest('POST', prepared.details, signal)
}

export function getVehicle(vehicleId, signal) {
  if (!isVehicleId(vehicleId)) return Promise.resolve({ kind: 'invalid', errors: { vehicle_id: vehicleIdMessage }, message: 'Check the vehicle ID.' })
  return vehicleRequest('GET', undefined, signal, vehicleId)
}

export function updateVehicle(vehicleId, current, values, confirmation, signal) {
  if (!isVehicleId(vehicleId)) return Promise.resolve({ kind: 'invalid', errors: { vehicle_id: vehicleIdMessage }, message: 'Check the vehicle ID.' })
  if (!isPublicVehicle(current) || String(current.id) !== vehicleId) {
    return Promise.resolve({ kind: 'reload-required', message: 'Reload this vehicle before saving.' })
  }
  const prepared = prepareVehiclePatch(current, values, confirmation)
  if (prepared.invalid) return Promise.resolve({ kind: 'invalid', errors: prepared.errors, message: 'Check your details and try again.' })
  if (prepared.unchanged) return Promise.resolve({ kind: 'unchanged', message: 'No changes to save.' })
  return vehicleRequest('PATCH', prepared.details, signal, vehicleId)
}
