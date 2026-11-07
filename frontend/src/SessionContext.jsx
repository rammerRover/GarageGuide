import { useEffect, useMemo, useSyncExternalStore } from 'react'
import { useLocation } from 'react-router-dom'
import { createSessionStore } from './sessionState.js'
import { SessionContext } from './useSession.js'

export default function SessionProvider({ children }) {
  const location = useLocation()
  const store = useMemo(() => createSessionStore(), [])
  const state = useSyncExternalStore(store.subscribe, store.getSnapshot)

  useEffect(() => {
    void store.enter(location.key, location.pathname === '/account')
  }, [store, location.key, location.pathname])

  useEffect(() => {
    const visibility = () => {
      if (document.visibilityState === 'hidden') store.hide()
      else void store.resume()
    }
    const depart = () => store.depart()
    const returnToDocument = (event) => { if (event.persisted) void store.resume() }
    document.addEventListener('visibilitychange', visibility)
    window.addEventListener('pagehide', depart)
    window.addEventListener('pageshow', returnToDocument)
    return () => {
      store.dispose()
      document.removeEventListener('visibilitychange', visibility)
      window.removeEventListener('pagehide', depart)
      window.removeEventListener('pageshow', returnToDocument)
    }
  }, [store])

  useEffect(() => {
    if (state.status !== 'authenticated' || !state.visible || state.busy) return
    // One expiry boundary check, never an interval that keeps idle sessions alive.
    const timer = setTimeout(() => { void store.recheck() }, Math.max(0, Date.parse(state.expires_at) - Date.now()))
    return () => clearTimeout(timer)
  }, [store, state.status, state.expires_at, state.visible, state.busy])

  const value = useMemo(() => ({ state, recheck: store.recheck, login: store.login, logout: store.logout }), [state, store])
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}
