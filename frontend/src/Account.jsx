import { useEffect, useState } from 'react'
import { supabase } from './lib/supabase'
import { getSessionHistory } from './lib/api'

export default function Account() {
  const [email, setEmail] = useState('')
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      setEmail(data.user?.email || '')
    })

    getSessionHistory()
      .then(res => setSessions(Array.isArray(res) ? res : []))
      .catch(err => console.error('getSessionHistory failed:', err))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen px-6 py-10">
      <div className="max-w-2xl mx-auto flex flex-col gap-8">
        <div>
          <span className="font-mono text-xs tracking-widest uppercase text-accent">
            Account
          </span>

          <h1 className="font-display text-3xl text-text mt-1">
            {email}
          </h1>
        </div>

        <div className="flex flex-col gap-3">
          <h2 className="font-body font-semibold text-text">
            Session History
          </h2>

          {loading && (
            <span className="font-mono text-sm text-text-muted">
              Loading…
            </span>
          )}

          {!loading && sessions.length === 0 && (
            <span className="font-body text-sm text-text-muted">
              No completed sessions yet.
            </span>
          )}

          {sessions.map(s => (
            <div
              key={s.id}
              className="bg-bg-card border border-border rounded-xl px-5 py-4 flex items-center justify-between"
            >
              <div className="flex flex-col">
                <span className="font-mono text-[10px] tracking-wider uppercase text-accent">
                  {s.mode}
                </span>

                <span className="font-body text-text">
                  {s.topic}
                </span>
              </div>

              <span className="font-display text-2xl text-accent">
                {s.session_evaluations?.[0]?.overall_score ?? '—'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}