import { useState } from 'react'
import { Link, Route, Routes } from 'react-router-dom'
import { checkConnection } from './api.js'
import Register from './Register.jsx'
import Login from './Login.jsx'
import Account from './Account.jsx'
import RequireSession from './RequireSession.jsx'
import SessionProvider from './SessionContext.jsx'

const messages = {
  idle: 'Ready to check the connection.',
  checking: 'Checking the connection…',
  connected: 'Connected. GarageGuide is ready.',
  unavailable: 'Connection unavailable. Please try again.',
}

function ConnectionScreen() {
  const [status, setStatus] = useState('idle')

  async function handleCheck() {
    setStatus('checking')
    try {
      await checkConnection()
      setStatus('connected')
    } catch {
      setStatus('unavailable')
    }
  }

  return (
    <>
        <section className="intro" aria-labelledby="page-title">
          <p className="eyebrow">Getting started</p>
          <h1 id="page-title">Your garage starts here.</h1>
          <p>Check that GarageGuide can connect before getting started.</p>
        </section>
        <section className="connection" aria-labelledby="connection-title">
          <div>
            <h2 id="connection-title">Connection status</h2>
            <p role="status" aria-live="polite" aria-atomic="true" className={`status ${status}`}>
              {messages[status]}
            </p>
          </div>
          <button onClick={handleCheck} disabled={status === 'checking'}>
            {status === 'checking' ? 'Checking…' : status === 'unavailable' ? 'Try again' : 'Check connection'}
          </button>
        </section>
    </>
  )
}

export default function App() {
  return (
    <SessionProvider>
      <div className="shell">
        <header className="site-header">
          <Link className="brand" to="/">GarageGuide</Link>
          <nav className="site-nav" aria-label="Main navigation">
            <Link to="/">Connection check</Link>
            <Link to="/register">Create account</Link>
            <Link to="/login">Sign in</Link>
            <Link to="/account">Account</Link>
          </nav>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<ConnectionScreen />} />
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/account" element={<RequireSession><Account /></RequireSession>} />
          </Routes>
        </main>
        <footer>GarageGuide · Project foundation</footer>
      </div>
    </SessionProvider>
  )
}
