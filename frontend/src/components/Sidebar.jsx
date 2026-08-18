import { NavLink } from 'react-router-dom'
import { supabase } from '../lib/supabase'

export default function Sidebar({ onLogout }) {
  async function handleLogout() {
    await supabase.auth.signOut()
    onLogout()
  }

  const linkClass = ({ isActive }) =>
    `font-body text-sm px-4 py-2 rounded-lg transition-colors ${
      isActive
        ? 'bg-accent text-bg font-semibold'
        : 'text-text-muted hover:text-text hover:bg-bg-card'
    }`

  return (
    <aside className="w-56 border-r border-border flex flex-col gap-1 px-3 py-6 shrink-0 h-screen">
      <div className="px-4 mb-6">
        <span className="font-display text-xl text-text">MindForge</span>
      </div>

      <NavLink to="/" end className={linkClass}>
        Dashboard
      </NavLink>

      <NavLink to="/debate" className={linkClass}>
        Debate Arena
      </NavLink>

      <NavLink to="/interview" className={linkClass}>
        Interview Simulator
      </NavLink>

      <div className="flex-1" />

      <NavLink to="/account" className={linkClass}>
        Account
      </NavLink>

      <button
        className="font-body text-sm px-4 py-2 rounded-lg text-text-muted hover:text-text hover:bg-bg-card transition-colors text-left"
        onClick={handleLogout}
      >
        Log Out
      </button>
    </aside>
  )
}