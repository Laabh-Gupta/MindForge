import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function Layout({ onLogout }) {
  return (
    <div className="h-screen bg-bg flex overflow-hidden">
      <Sidebar onLogout={onLogout} />

      <div className="flex-1 min-h-0 overflow-y-auto">
        <Outlet />
      </div>
    </div>
  )
}