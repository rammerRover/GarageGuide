import { useState } from 'react'
import { checkConnection } from './api.js'

const messages = {
  idle: 'Ready to check the connection.',
  checking: 'Checking the connection…',
  connected: 'Connected. GarageGuide is ready.',
  unavailable: 'Connection unavailable. Please try again.',
}

export default function App() {
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
    <div className="shell">
      <header><a className="brand" href="/">GarageGuide</a></header>
      <main>
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
      </main>
      <footer>GarageGuide · Project foundation</footer>
    </div>
  )
}
