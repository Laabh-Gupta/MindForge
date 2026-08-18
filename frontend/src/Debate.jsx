import { useState, useRef, useEffect } from 'react'
import { createSession, sendMessage, evaluateSession } from './lib/api'
import DebateMessage from './components/DebateMessage'
import SessionReview from './components/SessionReview'

export default function Debate() {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [topic, setTopic] = useState('')
  const [loading, setLoading] = useState(false)
  const [starting, setStarting] = useState(false)

  // Step 15 — evaluation/review state
  const [concluded, setConcluded] = useState(false)
  const [evaluation, setEvaluation] = useState(null)
  const [scores, setScores] = useState([])

  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth'
    })
  }, [messages, loading])

  async function startSession() {
    if (!topic.trim()) return

    setStarting(true)

    try {
      const session = await createSession('debate', topic)

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
      {
        role: 'user',
        content: userMsg
      }
    ])

    setInput('')
    setLoading(true)

    try {
      const res = await sendMessage(sessionId, userMsg)

      // Add AI response to the conversation
      if (res && res.reply) {
        setMessages(prev => [
          ...prev,
          {
            role: 'ai',
            content: res.reply
          }
        ])
      } else {
        console.error('Unexpected response shape:', res)

        setMessages(prev => [
          ...prev,
          {
            role: 'ai',
            content: 'Something went wrong — check the backend logs.'
          }
        ])
      }

      /*
       * Step 15:
       * Backend returns concluded: true when max_turns is reached.
       */
      if (res && res.concluded) {
        setConcluded(true)
        setLoading(false)

        try {
          const evalRes = await evaluateSession(sessionId)

          if (evalRes && evalRes.evaluation) {
            setEvaluation(evalRes.evaluation)
            setScores(evalRes.scores || [])
          } else {
            console.error(
              'Unexpected evaluation response:',
              evalRes
            )
          }
        } catch (err) {
          console.error('evaluateSession failed:', err)
        }

        return
      }

    } catch (err) {
      console.error('sendMessage failed:', err)

      setMessages(prev => [
        ...prev,
        {
          role: 'ai',
          content: 'Request failed — check the backend logs.'
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  function startNewSession() {
    setSessionId(null)
    setMessages([])
    setTopic('')
    setConcluded(false)
    setEvaluation(null)
    setScores([])
  }

  // No active session yet — show topic selection screen
  if (!sessionId) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center px-6">
        <div className="max-w-md w-full flex flex-col gap-6">

          <div className="flex flex-col gap-2">
            <span className="font-mono text-xs tracking-widest uppercase text-accent">
              Debate Arena
            </span>

            <h1 className="font-display text-3xl text-text">
              What's your position today?
            </h1>

            <p className="font-body text-sm text-text-muted">
              Name a topic. Your opponent won't agree with you — and won't let you off easy either.
            </p>
          </div>

          <textarea
            className="bg-bg-card border border-border rounded-xl px-4 py-3 font-body text-[15px] text-text placeholder:text-text-muted resize-none focus:outline-none focus:border-accent-dim transition-colors"
            rows={3}
            placeholder="e.g. Should social media be regulated like tobacco?"
            value={topic}
            onChange={e => setTopic(e.target.value)}
          />

          <button
            className="bg-accent text-bg font-body font-semibold rounded-xl py-3 hover:bg-accent-dim transition-colors disabled:opacity-40"
            onClick={startSession}
            disabled={!topic.trim() || starting}
          >
            {starting ? 'Setting up…' : 'Enter the Arena'}
          </button>

        </div>
      </div>
    )
  }

  /*
   * Session has concluded.
   * Show evaluation/review instead of the chat.
   */
  if (concluded) {
    return (
      <SessionReview
        evaluation={evaluation}
        scores={scores}
        topic={topic}
        onStartNew={startNewSession}
      />
    )
  }

  // Active Debate session
  return (
    <div className="min-h-screen bg-bg flex flex-col">

      <header className="border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="flex flex-col">
          <span className="font-mono text-[10px] tracking-widest uppercase text-accent">
            Debate Arena
          </span>

          <h2 className="font-display text-lg text-text">
            {topic}
          </h2>
        </div>

        <span className="font-mono text-xs text-text-muted">
          {messages.filter(m => m.role === 'user').length} turns
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
            placeholder="Make your case…"
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