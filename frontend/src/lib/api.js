import { supabase } from './supabase'

const API_BASE = import.meta.env.VITE_API_BASE_URL

async function authHeader() {
  const { data } = await supabase.auth.getSession()
  return { Authorization: `Bearer ${data.session?.access_token}` }
}

export async function createSession(mode, topic) {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(await authHeader()) },
    body: JSON.stringify({ mode, topic }),
  })
  return res.json()
}

export async function sendMessage(sessionId, content) {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(await authHeader()) },
    body: JSON.stringify({ content }),
  })
  return res.json()
}
export async function evaluateSession(sessionId) {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/evaluate`, {
    method: 'POST',
    headers: { ...(await authHeader()) },
  })
  return res.json()
}