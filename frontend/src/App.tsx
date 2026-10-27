import { useState, useEffect, useCallback } from 'react'
import './App.css'

interface HealthData {
  status: string
  mode: string
}

export function App() {
  const [health, setHealth] = useState<HealthData | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [latency, setLatency] = useState<number | null>(null)
  const [lastChecked, setLastChecked] = useState<Date | null>(null)

  const checkHealth = useCallback(async () => {
    setLoading(true)
    setError(null)
    const startTime = performance.now()
    try {
      const res = await fetch('/api/health')
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }
      const data: HealthData = await res.json()
      const endTime = performance.now()
      setLatency(Math.round(endTime - startTime))
      setHealth(data)
      setLastChecked(new Date())
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to connect to backend'
      setError(message)
      setHealth(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    checkHealth()
  }, [checkHealth])

  return (
    <div className="container">
      <header className="header">
        <div className="badge-pill">Meta AI Hackathon • Indie Track</div>
        <h1 className="title">
          Screen<span className="accent">Guard</span>
        </h1>
        <p className="subtitle">
          Real-Time Multimodal AI Supervisor Agent for High-Stakes Business Workflows
        </p>
      </header>

      <main className="main-content">
        <section className="card health-card">
          <div className="card-header">
            <div className="card-title-group">
              <span className={`status-indicator ${loading ? 'pending' : health?.status === 'ok' ? 'online' : 'offline'}`} />
              <h2>Backend Health Diagnostic</h2>
            </div>
            <button 
              className="refresh-btn" 
              onClick={checkHealth} 
              disabled={loading}
              title="Query /api/health"
            >
              {loading ? 'Probing...' : 'Check Health'}
            </button>
          </div>

          <div className="card-body">
            {loading && (
              <div className="state-box loading">
                <div className="spinner" />
                <span>Querying <code>/api/health</code>...</span>
              </div>
            )}

            {!loading && error && (
              <div className="state-box error">
                <div className="error-icon">!</div>
                <div>
                  <strong>Backend Connection Failed</strong>
                  <p>{error}</p>
                  <small>Make sure the FastAPI server is running at <code>http://127.0.0.1:8000</code>.</small>
                </div>
              </div>
            )}

            {!loading && health && (
              <div className="health-details">
                <div className="metrics-grid">
                  <div className="metric-box">
                    <span className="metric-label">STATUS</span>
                    <span className="metric-value status-badge">{health.status.toUpperCase()}</span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-label">RUNTIME MODE</span>
                    <span className="metric-value mode-badge">{health.mode.toUpperCase()}</span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-label">LATENCY</span>
                    <span className="metric-value">{latency !== null ? `${latency} ms` : '—'}</span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-label">LAST CHECKED</span>
                    <span className="metric-value time-val">
                      {lastChecked ? lastChecked.toLocaleTimeString() : '—'}
                    </span>
                  </div>
                </div>

                <div className="json-preview">
                  <div className="json-header">Raw Response (<code>/api/health</code>)</div>
                  <pre>{JSON.stringify(health, null, 2)}</pre>
                </div>
              </div>
            )}
          </div>
        </section>

        <section className="card info-card">
          <h3>System Architecture Overview</h3>
          <div className="pipeline-steps">
            <div className="step-item">
              <span className="step-num">01</span>
              <h4>Observe</h4>
              <p>Differential screen capture at max 1024px with 32x32 hash change-detection.</p>
            </div>
            <div className="step-item">
              <span className="step-num">02</span>
              <h4>Verify</h4>
              <p>Meta Muse Spark reasoning &amp; SAM 3.1 element localization.</p>
            </div>
            <div className="step-item">
              <span className="step-num">03</span>
              <h4>Decide</h4>
              <p>Strict deterministic step engine: ADVANCE, WARN, ASK, STOP.</p>
            </div>
            <div className="step-item">
              <span className="step-num">04</span>
              <h4>Act</h4>
              <p>Proactive operator warnings to prevent costly skipped or wrong steps.</p>
            </div>
          </div>
        </section>
      </main>

      <footer className="footer">
        <span>ScreenGuard v0.1.0 • Phase 0 Scaffold Ready</span>
      </footer>
    </div>
  )
}

export default App
