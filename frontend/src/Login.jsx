import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { validateLoginFields } from './credentialValidation.js'
import { useSession } from './useSession.js'

const names = ['email', 'password']

export default function Login() {
  const { state, login } = useSession()
  const navigate = useNavigate()
  const [fields, setFields] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [feedback, setFeedback] = useState('')
  const [pending, setPending] = useState(false)
  const [focusRequest, setFocusRequest] = useState(null)
  const inputs = useRef({})
  const heading = useRef(null)
  const error = useRef(null)
  const request = useRef(null)

  useEffect(() => {
    heading.current?.focus()
    const discard = () => {
      request.current?.abort()
      request.current = null
      if (inputs.current.password) inputs.current.password.value = ''
      setFields((current) => ({ ...current, password: '' }))
      setPending(false)
      setErrors({})
      setFeedback('')
      setFocusRequest(null)
    }
    const restore = (event) => { if (event.persisted) discard() }
    window.addEventListener('pagehide', discard)
    window.addEventListener('pageshow', restore)
    return () => {
      request.current?.abort()
      window.removeEventListener('pagehide', discard)
      window.removeEventListener('pageshow', restore)
    }
  }, [])

  useEffect(() => {
    if (!pending && focusRequest) (inputs.current[focusRequest.field] ?? error.current)?.focus()
  }, [focusRequest, pending])

  function updateField(event) {
    const { name, value } = event.target
    setFields((current) => ({ ...current, [name]: value }))
    setErrors((current) => { const next = { ...current }; delete next[name]; return next })
    setFeedback('')
    setFocusRequest(null)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (request.current) return
    setFeedback('')
    const invalid = validateLoginFields(fields)
    setErrors(invalid)
    if (Object.keys(invalid).length) {
      setFeedback('Check the highlighted fields.')
      setFocusRequest({ field: names.find((name) => invalid[name]) })
      return
    }
    const controller = new AbortController()
    request.current = controller
    setPending(true)
    try {
      const result = await login(fields, controller.signal)
      if (controller.signal.aborted) return
      if (result.kind === 'success') {
        setFields((current) => ({ ...current, password: '' }))
        navigate('/account', { replace: true })
      } else if (result.kind !== 'cancelled') {
        const correctable = result.kind === 'invalid' || result.kind === 'network'
        if (!correctable) setFields((current) => ({ ...current, password: '' }))
        setErrors(result.errors ?? {})
        setFeedback(result.message + (correctable ? '' : ' Re-enter your password to try again.'))
        setFocusRequest({ field: names.find((name) => result.errors?.[name]) })
      }
    } catch {
      if (!controller.signal.aborted) {
        setFields((current) => ({ ...current, password: '' }))
        setFeedback("We couldn't confirm sign-in. Re-enter your password to try again.")
        setFocusRequest({})
      }
    } finally {
      if (request.current === controller) {
        request.current = null
        if (!controller.signal.aborted) setPending(false)
      }
    }
  }

  return (
    <>
      <section className="intro" aria-labelledby="login-title">
        <p className="eyebrow">Welcome back</p>
        <h1 id="login-title" ref={heading} tabIndex={-1}>Sign in to GarageGuide.</h1>
        <p>Use your account email and password.</p>
        <p role="status" aria-live="polite" aria-atomic="true">{state.notice}</p>
      </section>
      <form className="registration" method="post" action="/api/auth/login" onSubmit={handleSubmit}
        noValidate aria-labelledby="login-title" aria-busy={pending}>
        <fieldset disabled={pending}>
          <legend className="visually-hidden">Sign-in details</legend>
          {names.map((name) => {
            const errorId = `login-${name}-error`
            return (
              <div className="form-field" key={name}>
                <label htmlFor={`login-${name}`}>{name === 'email' ? 'Email address' : 'Password'}</label>
                <input id={`login-${name}`} name={name} type={name === 'email' ? 'email' : 'password'}
                  autoComplete={name === 'email' ? 'email' : 'current-password'}
                  ref={(node) => { inputs.current[name] = node }}
                  value={fields[name]} onChange={updateField} required
                  aria-invalid={Boolean(errors[name])} aria-describedby={errors[name] ? errorId : undefined} />
                {errors[name] && <p className="field-error" id={errorId}>{errors[name]}</p>}
              </div>
            )
          })}
          <button type="submit" disabled={pending}>{pending ? 'Signing in' : 'Sign in'}</button>
        </fieldset>
        <p className="form-status" role="status" aria-live="polite" aria-atomic="true">
          {pending ? 'Signing in. Please wait.' : ''}
        </p>
        <p className="form-status field-error" role="alert" aria-atomic="true" ref={error} tabIndex={-1}>{feedback}</p>
      </form>
    </>
  )
}
