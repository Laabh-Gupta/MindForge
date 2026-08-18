import { useState, useRef, useEffect } from 'react'
import { createSession, sendMessage, evaluateSession } from './lib/api'
import DebateMessage from './components/DebateMessage'
import SessionReview from './components/SessionReview'

export default function Interview({ onExit }) {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [role, setRole] = useState('')
  const [loading, setLoading] = useState(false)
  const [starting, setStarting] = useState(false)
  const [concluded, setConcluded] = useState(false)
  const [evaluation, setEvaluation] = useState(null)
  const [scores, setScores] = useState([])
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth',
    })
  }, [messages, loading])

  async function startSession() {
    if (!role.trim()) return

    setStarting(true)

    try {
      const session = await createSession('interview', role)

      if (session && session.id) {
        setSessionId(session.id)
      } else {
        console.error('Unexpected session response:', session)
      }
    } catch (err) {
      console.error('createSession failed:', err)
    } finally {
      setStarting(false)
    }
  }

  async function handleSend() {
    if (!sessionId || !input.trim() || loading) return

    const userMsg = input

    setMessages(prev => [
      ...prev,
      { role: 'user', content: userMsg },
    ])

    setInput('')
    setLoading(true)

    try {
      const res = await sendMessage(sessionId, userMsg)

      if (res && res.reply) {
        setMessages(prev => [
          ...prev,
          { role: 'ai', content: res.reply },
        ])
      } else {
        console.error('Unexpected response shape:', res)

        setMessages(prev => [
          ...prev,
          {
            role: 'ai',
            content: 'Something went wrong — check the backend logs.',
          },
        ])
      }

      if (res && res.concluded) {
        setConcluded(true)
        setLoading(false)

        const evalRes = await evaluateSession(sessionId)

        if (evalRes && evalRes.evaluation) {
          setEvaluation(evalRes.evaluation)
          setScores(evalRes.scores || [])
        } else {
          console.error('Unexpected evaluation response:', evalRes)
        }

        return
      }
    } catch (err) {
      console.error('sendMessage failed:', err)

      setMessages(prev => [
        ...prev,
        {
          role: 'ai',
          content: 'Request failed — check the backend logs.',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  function startNewSession() {
    setSessionId(null)
    setMessages([])
    setRole('')
    setConcluded(false)
    setEvaluation(null)
    setScores([])
  }

  if (concluded) {
    return (
      <SessionReview
        evaluation={evaluation}
        scores={scores}
        topic={role}
        onStartNew={startNewSession}
      />
    )
  }

  if (!sessionId) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center px-6">
        <div className="max-w-md w-full flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <span className="font-mono text-xs tracking-widest uppercase text-accent">
              Interview Simulator
            </span>

            <h1 className="font-display text-3xl text-text">
              What are you interviewing for?
            </h1>

            <p className="font-body text-sm text-text-muted">
              Name the role or interview type. Every follow-up will build on
              what you actually say.
            </p>
          </div>

          <input
            className="bg-bg-card border border-border rounded-xl px-4 py-3 font-body text-[15px] text-text placeholder:text-text-muted focus:outline-none focus:border-accent-dim transition-colors"
            placeholder="e.g. MBA Interview, HR Interview, Product Manager"
            value={role}
            onChange={e => setRole(e.target.value)}
          />

          <button
            className="bg-accent text-bg font-body font-semibold rounded-xl py-3 hover:bg-accent-dim transition-colors disabled:opacity-40"
            onClick={startSession}
            disabled={!role.trim() || starting}
          >
            {starting ? 'Setting up…' : 'Begin Interview'}
          </button>

          {onExit && (
            <button
              className="font-mono text-xs text-text-muted hover:text-text transition-colors"
              onClick={onExit}
            >
              ← Back
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-bg flex flex-col">
      <header className="border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="flex flex-col">
          <span className="font-mono text-[10px] tracking-widest uppercase text-accent">
            Interview Simulator
          </span>

          <h2 className="font-display text-lg text-text">
            {role}
          </h2>
        </div>

        <span className="font-mono text-xs text-text-muted">
          {messages.filter(m => m.role === 'user').length} answers
        </span>
      </header>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-6 py-6 flex flex-col gap-4 max-w-3xl mx-auto w-full"
      >
        {messages.map((m, i) => (
          <DebateMessage
            key={i}
            role={m.role}
            content={m.content}
          />
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-bg-card border border-border rounded-2xl rounded-bl-sm px-5 py-4">
              <span className="font-mono text-xs text-text-muted animate-pulse">
                thinking…
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-border px-6 py-4">
        <div className="max-w-3xl mx-auto flex gap-3">
          <input
            className="flex-1 bg-bg-card border border-border rounded-xl px-4 py-3 font-body text-[15px] text-text placeholder:text-text-muted focus:outline-none focus:border-accent-dim transition-colors"
            placeholder="Your answer…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
          />

          <button
            className="bg-accent text-bg font-body font-semibold rounded-xl px-6 hover:bg-accent-dim transition-colors disabled:opacity-40"
            onClick={handleSend}
            disabled={loading || !input.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}