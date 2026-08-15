import { useState } from 'react'
import { createSession, sendMessage } from './lib/api'

export default function Debate() {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [topic, setTopic] = useState('')

  async function startSession() {
    const session = await createSession('debate', topic)
    setSessionId(session.id)
  }

  async function handleSend() {
    if (!sessionId || !input.trim()) return
    setMessages(prev => [...prev, { role: 'user', content: input }])
    const userMsg = input
    setInput('')
    const res = await sendMessage(sessionId, userMsg)
    setMessages(prev => [...prev, { role: 'ai', content: res.reply }])
  }

  if (!sessionId) {
    return (
      <div className="max-w-md mx-auto mt-20 flex flex-col gap-3">
        <input className="border p-2" placeholder="Debate topic" value={topic} onChange={e => setTopic(e.target.value)} />
        <button className="bg-black text-white p-2" onClick={startSession}>Start Debate</button>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto mt-10 flex flex-col gap-4">
      <div className="flex flex-col gap-3">
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
            <div className={`inline-block p-3 rounded ${m.role === 'user' ? 'bg-black text-white' : 'bg-gray-100'}`}>
              {m.content}
            </div>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input className="border p-2 flex-1" value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()} />
        <button className="bg-black text-white px-4" onClick={handleSend}>Send</button>
      </div>
    </div>
  )
}