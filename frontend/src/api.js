export async function checkConnection() {
  const response = await fetch('/api/health/db', {
    signal: AbortSignal.timeout(10000),
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) throw new Error('Connection unavailable')
  const result = await response.json()
  if (result.status !== 'ok' || result.database !== 'connected' || result.schema !== 'ready') {
    throw new Error('Unexpected connection response')
  }
}
