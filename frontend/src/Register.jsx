import { useEffect, useRef, useState } from 'react'
import { registerAccount } from './api.js'
import { validateRegistrationFields } from './credentialValidation.js'


const fieldNames = ['email', 'password', 'password_confirmation']
const fieldLabels = {
  email: 'Email address', password: 'Password', password_confirmation: 'Confirm password',
}

export default function Register() {
  const [fields, setFields] = useState({ email: '', password: '', password_confirmation: '' })
  const [errors, setErrors] = useState({})
  const [feedback, setFeedback] = useState(null)
  const [pending, setPending] = useState(false)
  const [focusRequest, setFocusRequest] = useState(null)
  const requestRef = useRef(null)
  const inputs = useRef({})
  const headingRef = useRef(null)
  const errorRef = useRef(null)
  const statusRef = useRef(null)

  useEffect(() => {
    headingRef.current?.focus()
    function discardDocumentCredentials() {
      requestRef.current?.abort()
      requestRef.current = null
      for (const name of ['password', 'password_confirmation']) {
        if (inputs.current[name]) inputs.current[name].value = ''
      }
      setFields((current) => ({ ...current, password: '', password_confirmation: '' }))
      setPending(false)
      setErrors({})
      setFeedback(null)
      setFocusRequest(null)
    }
    function handlePageShow(event) {
      if (event.persisted) discardDocumentCredentials()
    }
    window.addEventListener('pagehide', discardDocumentCredentials)
    window.addEventListener('pageshow', handlePageShow)
    return () => {
      // Password state belongs to this page and is discarded on unmount.
      requestRef.current?.abort()
      window.removeEventListener('pagehide', discardDocumentCredentials)
      window.removeEventListener('pageshow', handlePageShow)
    }
  }, [])

  useEffect(() => {
    if (pending || !focusRequest) return
    const target = inputs.current[focusRequest.field] ??
      (focusRequest.success ? statusRef.current : errorRef.current)
    target?.focus()
  }, [focusRequest, pending])

  function clearPasswords() {
    setFields((current) => ({ ...current, password: '', password_confirmation: '' }))
  }

  function updateField(event) {
    const { name, value } = event.target
    setFields((current) => ({ ...current, [name]: value }))
    setErrors((current) => {
      const next = { ...current }
      delete next[name]
      if (name === 'password') delete next.password_confirmation
      return next
    })
    setFeedback(null)
    setFocusRequest(null)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (requestRef.current) return
    setFeedback(null)
    const invalid = validateRegistrationFields(fields)
    setErrors(invalid)
    if (Object.keys(invalid).length) {
      setFeedback({ kind: 'error', message: 'Check the highlighted fields.' })
      setFocusRequest({ field: fieldNames.find((name) => invalid[name]) })
      return
    }
    const controller = new AbortController()
    requestRef.current = controller
    setPending(true)
    try {
      const result = await registerAccount(fields, controller.signal)
      if (controller.signal.aborted) return
      if (result.kind === 'success') {
        clearPasswords()
        setFeedback({ kind: 'success', message: 'Account created successfully.' })
        setFocusRequest({ success: true })
      } else if (result.kind !== 'cancelled') {
        const correctable = result.kind === 'invalid' || result.kind === 'network'
        if (!correctable) clearPasswords()
        setErrors(result.errors ?? {})
        setFeedback({
          kind: 'error',
          message: result.message + (correctable ? '' : ' Re-enter your passwords to try again.'),
        })
        setFocusRequest({ field: fieldNames.find((name) => result.errors?.[name]) })
      }
    } catch {
      if (!controller.signal.aborted) {
        clearPasswords()
        setFeedback({ kind: 'error', message: "We couldn't confirm registration. Re-enter your passwords to try again." })
        setFocusRequest({})
      }
    } finally {
      if (requestRef.current === controller) {
        requestRef.current = null
        if (!controller.signal.aborted) setPending(false)
      }
    }
  }

  return (
    <>
      <section className="intro" aria-labelledby="register-title">
        <p className="eyebrow">Get started</p>
        <h1 id="register-title" ref={headingRef} tabIndex={-1}>Create your account.</h1>
        <p>Keep your vehicle maintenance records together in GarageGuide.</p>
      </section>
      <form className="registration" method="post" action="/api/auth/register"
        onSubmit={handleSubmit} noValidate aria-labelledby="register-title" aria-busy={pending}>
        <fieldset disabled={pending}>
          <legend className="visually-hidden">Account details</legend>
          {fieldNames.map((name) => {
            const errorId = `register-${name}-error`
            const hintId = name === 'password' ? 'register-password-hint' : undefined
            return (
              <div className="form-field" key={name}>
                <label htmlFor={`register-${name}`}>{fieldLabels[name]}</label>
                {hintId && <p className="field-hint" id={hintId}>Use 15 to 128 characters. Spaces are allowed; case is preserved.</p>}
                <input id={`register-${name}`} name={name}
                  ref={(node) => { inputs.current[name] = node }}
                  type={name === 'email' ? 'email' : 'password'}
                  autoComplete={name === 'email' ? 'email' : 'new-password'}
                  value={fields[name]} onChange={updateField} required
                  aria-invalid={Boolean(errors[name])}
                  aria-describedby={[hintId, errors[name] ? errorId : null].filter(Boolean).join(' ') || undefined} />
                {errors[name] && <p className="field-error" id={errorId}>{errors[name]}</p>}
              </div>
            )
          })}
          <button type="submit" disabled={pending}>{pending ? 'Creating account' : 'Create account'}</button>
        </fieldset>
        <p className="form-status connected" ref={statusRef} role="status" aria-live="polite" aria-atomic="true" tabIndex={-1}>
          {pending ? 'Creating your account. Please wait.' : feedback?.kind === 'success' ? feedback.message : ''}
        </p>
        <p className="form-status field-error" ref={errorRef} role="alert" aria-atomic="true" tabIndex={-1}>
          {feedback?.kind === 'error' ? feedback.message : ''}
        </p>
      </form>
    </>
  )
}
