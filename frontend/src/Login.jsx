import { useState } from 'react'
import { supabase } from './lib/supabase'

export default function Login({ onLoggedIn }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [loading, setLoading] = useState(false)

  function validate() {
    if (!email.trim() || !password.trim()) {
      setError('Enter both an email and a password.')
      return false
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.')
      return false
    }
    return true
  }

  async function handleLogin() {
    setError('')
    setInfo('')
    if (!validate()) return
    setLoading(true)
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    setLoading(false)
    if (error) setError(error.message)
    else onLoggedIn()
  }

  async function handleSignup() {
    setError('')
    setInfo('')
    if (!validate()) return
    setLoading(true)
    const { data, error } = await supabase.auth.signUp({ email, password })
    setLoading(false)
    if (error) {
      setError(error.message)
    } else if (data.session) {
      // email confirmation is off, so we're logged in immediately
      onLoggedIn()
    } else {
      // email confirmation is on for this project
      setInfo('Account created. Check your email to confirm before logging in.')
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center px-6">
      <div className="max-w-sm w-full flex flex-col gap-6">
        <div className="flex flex-col gap-1 items-center text-center">
          <h1 className="font-display text-4xl text-text">MindForge</h1>
          <p className="font-mono text-xs tracking-widest uppercase text-text-muted">Communication, under pressure</p>
        </div>
        <div className="flex flex-col gap-3">
          <input
            className="bg-bg-card border border-border rounded-xl px-4 py-3 font-body text-[15px] text-text placeholder:text-text-muted focus:outline-none focus:border-accent-dim transition-colors"
            placeholder="Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
          />
          <input
            className="bg-bg-card border border-border rounded-xl px-4 py-3 font-body text-[15px] text-text placeholder:text-text-muted focus:outline-none focus:border-accent-dim transition-colors"
            type="password"
            placeholder="Password (min 6 characters)"
            value={password}
            onChange={e => setPassword(e.target.value)}
          />
          {error && <p className="font-body text-sm text-red-400">{error}</p>}
          {info && <p className="font-body text-sm text-accent">{info}</p>}
          <button
            className="bg-accent text-bg font-body font-semibold rounded-xl py-3 hover:bg-accent-dim transition-colors disabled:opacity-40"
            onClick={handleSignup}
            disabled={loading}
          >
            Sign Up
          </button>
          <button
            className="border border-border text-text font-body rounded-xl py-3 hover:border-accent-dim transition-colors disabled:opacity-40"
            onClick={handleLogin}
            disabled={loading}
          >
            Log In
          </button>
        </div>
      </div>
    </div>
  )
}