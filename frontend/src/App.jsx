import { useEffect, useState } from 'react'
import { supabase } from './lib/supabase'
import Login from './Login'
import Debate from './Debate'

export default function App() {
  const [loggedIn, setLoggedIn] = useState(false)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setLoggedIn(!!data.session))
  }, [])

  return loggedIn ? <Debate /> : <Login onLoggedIn={() => setLoggedIn(true)} />
}