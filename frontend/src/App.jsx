import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { supabase } from './lib/supabase'
import Login from './Login'
import Layout from './components/Layout'
import Dashboard from './Dashboard'
import Debate from './Debate'
import Interview from './Interview'
import Account from './Account'

export default function App() {
  const [loggedIn, setLoggedIn] = useState(false)
  const [checked, setChecked] = useState(false)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setLoggedIn(!!data.session)
      setChecked(true)
    })
  }, [])

  if (!checked) return null

  if (!loggedIn) {
    return <Login onLoggedIn={() => setLoggedIn(true)} />
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout onLogout={() => setLoggedIn(false)} />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/debate" element={<Debate />} />
          <Route path="/interview" element={<Interview />} />
          <Route path="/account" element={<Account />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}