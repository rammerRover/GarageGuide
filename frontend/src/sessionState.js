import { matchRoutes } from 'react-router-dom'
import { accountRoute } from './accountRoute.js'
import { getSession, loginAccount, logoutAccount } from './api.js'

const unavailableMessage = "We couldn't confirm your session. Please try again."

export function createSessionStore(api = { getSession, loginAccount, logoutAccount }, now = Date.now) {
  let state = {
    status: 'loading', user: null, expires_at: null, checkedFor: null,
    notice: '', busy: null, visible: true,
  }
  let route = null
  let active = null
  let needsRecheck = false
  const listeners = new Set()
  const publish = (changes) => {
    state = { ...state, ...changes }
    for (const listener of listeners) listener()
  }
  const cancel = () => {
    active?.controller.abort()
    active = null
  }
  const begin = (kind, externalSignal) => {
    cancel()
    const request = { kind, controller: new AbortController() }
    request.signal = externalSignal ? AbortSignal.any([request.controller.signal, externalSignal]) : request.controller.signal
    active = request
    return request
  }
  const current = (request) => active === request && !request.signal.aborted
  const endSession = () => {
    cancel()
    needsRecheck = false
    publish({
      status: 'guest', user: null, expires_at: null, checkedFor: route?.key ?? null,
      notice: 'Your session has ended. Please sign in again.', busy: null,
    })
  }
  const accept = (session) => {
    if (Date.parse(session.expires_at) <= now()) {
      endSession()
      return
    }
    publish({
      user: session.user, expires_at: session.expires_at,
      status: 'authenticated', checkedFor: route?.key ?? null, notice: '',
    })
  }

  async function recheck() {
    if (active && active.kind !== 'session') {
      needsRecheck = true
      publish({ checkedFor: null })
      return { kind: 'deferred' }
    }
    const request = begin('session')
    publish({ status: 'loading', checkedFor: null, busy: null })
    let result
    try {
      result = await api.getSession(request.signal)
    } catch {
      result = { kind: 'unavailable' }
    }
    if (!current(request)) return { kind: 'cancelled' }
    active = null
    if (result.kind === 'success') {
      accept(result.session)
    } else if (result.kind === 'guest') {
      const notice = state.user || route?.protected ? 'Your session has ended. Please sign in again.' :
        state.notice === 'You have signed out.' ? state.notice : ''
      publish({ status: 'guest', user: null, expires_at: null, checkedFor: route?.key ?? null, notice })
    } else {
      publish({ status: 'unavailable', checkedFor: route?.key ?? null, notice: unavailableMessage })
    }
    return result
  }

  async function mutate(kind, details, signal) {
    if (active && active.kind !== 'session') return { kind: 'cancelled' }
    const request = begin(kind, signal)
    publish({ busy: kind })
    let result
    try {
      result = kind === 'login' ? await api.loginAccount(details, request.signal) : await api.logoutAccount(request.signal)
    } catch {
      result = { kind: 'unexpected', message: "We couldn't confirm the request. Please try again." }
    }
    if (!current(request)) {
      if (active === request) {
        active = null
        publish({ busy: null })
        if (needsRecheck) {
          needsRecheck = false
          void recheck()
        }
      }
      return { kind: 'cancelled' }
    }
    active = null
    publish({ busy: null })
    if (result.kind === 'success' && kind === 'login') {
      accept(result.session)
    } else if (result.kind === 'success') {
      publish({ status: 'guest', user: null, expires_at: null, checkedFor: route?.key ?? null, notice: 'You have signed out.' })
    } else if (state.status === 'loading') {
      publish({ status: 'unavailable', checkedFor: route?.key ?? null, notice: unavailableMessage })
    }
    if (needsRecheck) {
      needsRecheck = false
      void recheck()
    }
    return result
  }

  return {
    getSnapshot: () => state,
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener) },
    recheck,
    login: (details, signal) => mutate('login', details, signal),
    logout: (signal) => mutate('logout', undefined, signal),
    watchExpiry() {
      const deadline = state.expires_at
      if (!deadline) return
      // Expiry is local gating only; session lookup would renew server idle time.
      const timer = setTimeout(() => {
        if (state.expires_at === deadline) endSession()
      }, Math.max(0, Date.parse(deadline) - now()))
      return () => clearTimeout(timer)
    },
    enter(key, pathname) {
      const uncertain = Boolean(active)
      cancel()
      needsRecheck = false
      route = { key, protected: Boolean(matchRoutes([accountRoute], { pathname })) }
      publish({ busy: null })
      if (route.protected || uncertain || state.status === 'loading') return recheck()
      publish({ checkedFor: key })
      return Promise.resolve()
    },
    hide() {
      publish({ visible: false, checkedFor: null })
    },
    resume() {
      publish({ visible: true })
      return recheck()
    },
    depart() {
      cancel()
      needsRecheck = false
      publish({ visible: false, checkedFor: null, busy: null })
    },
    dispose() { cancel(); needsRecheck = false },
  }
}
