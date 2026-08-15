import { useState } from 'react'
import { supabase } from './lib/supabase'

export default function Login({ onLoggedIn }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  async function handleLogin() {
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) setError(error.message)
    else onLoggedIn()
  }

  async function handleSignup() {
    const { error } = await supabase.auth.signUp({ email, password })
    if (error) setError(error.message)
    else onLoggedIn()
  }

  return (
    <div className="flex flex-col gap-3 max-w-sm mx-auto mt-20">
      <input className="border p-2" placeholder="email" value={email} onChange={e => setEmail(e.target.value)} />
      <input className="border p-2" type="password" placeholder="password" value={password} onChange={e => setPassword(e.target.value)} />
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <button className="bg-black text-white p-2" onClick={handleLogin}>Log In</button>
      <button className="border p-2" onClick={handleSignup}>Sign Up</button>
    </div>
  )
}