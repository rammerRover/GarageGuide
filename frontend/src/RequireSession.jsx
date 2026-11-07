import { useEffect, useRef } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useSession } from './useSession.js'

function SessionGate({ unavailable, message, retry }) {
  const heading = useRef(null)
  useEffect(() => { heading.current?.focus() }, [unavailable])
  return (
    <section className="session-panel" aria-labelledby="session-gate-title" aria-busy={!unavailable}>
      <h1 id="session-gate-title" ref={heading} tabIndex={-1}>
        {unavailable ? 'Session unavailable.' : 'Checking your session.'}
      </h1>
      <p role="status" aria-live="polite" aria-atomic="true">
        {unavailable ? message : 'Please wait while we confirm your session.'}
      </p>
      {unavailable && <button type="button" onClick={() => { void retry() }}>Try again</button>}
    </section>
  )
}

export default function RequireSession({ children }) {
  const { state, recheck } = useSession()
  const location = useLocation()
  if (!state.visible || state.checkedFor !== location.key || state.status === 'loading') {
    return <SessionGate />
  }
  if (state.status === 'guest') return <Navigate to="/login" replace />
  if (state.status === 'unavailable') {
    return <SessionGate unavailable message={state.notice} retry={recheck} />
  }
  return children
}
