import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useSession } from './useSession.js'

export default function Account() {
  const { state, logout } = useSession()
  const navigate = useNavigate()
  const [feedback, setFeedback] = useState('')
  const request = useRef(null)
  const heading = useRef(null)
  const error = useRef(null)
  const pending = state.busy === 'logout'

  useEffect(() => {
    heading.current?.focus()
    return () => request.current?.abort()
  }, [])
  useEffect(() => { if (feedback && !pending) error.current?.focus() }, [feedback, pending])

  async function handleLogout() {
    if (request.current) return
    const controller = new AbortController()
    request.current = controller
    setFeedback('')
    try {
      const result = await logout(controller.signal)
      if (controller.signal.aborted) return
      if (result.kind === 'success') navigate('/login', { replace: true })
      else if (result.kind !== 'cancelled') setFeedback(result.message + ' Sign-out was not confirmed. Please try again.')
    } catch {
      if (!controller.signal.aborted) setFeedback("Sign-out was not confirmed. Please try again.")
    } finally {
      if (request.current === controller) request.current = null
    }
  }

  return (
    <section className="session-panel" aria-labelledby="account-title" aria-busy={pending}>
      <p className="eyebrow">Your account</p>
      <h1 id="account-title" ref={heading} tabIndex={-1}>Signed in.</h1>
      <p className="account-email">{state.user.email}</p>
      <p>Current session deadline: <time dateTime={state.expires_at}>{new Date(state.expires_at).toLocaleString()}</time>.</p>
      <p><Link to="/vehicles">Open your garage</Link></p>
      <button type="button" onClick={handleLogout} disabled={pending}>{pending ? 'Signing out' : 'Sign out'}</button>
      <p className="form-status" role="status" aria-live="polite" aria-atomic="true">
        {pending ? 'Signing out. Please wait.' : ''}
      </p>
      <p className="form-status field-error" role="alert" aria-atomic="true" ref={error} tabIndex={-1}>{feedback}</p>
    </section>
  )
}
