function parseStructuredReply(text) {
  if (!text || typeof text !== 'string') return null

  const regex = /\*\*(?:\d+\.\s*)?([^*]+?):\*\*\s*/g
  const parts = text.split(regex)

  const sections = []
  for (let i = 1; i < parts.length; i += 2) {
    const label = parts[i]
    const content = parts[i + 1]
    if (label && content && content.trim()) {
      sections.push({ label: label.trim(), content: content.trim() })
    }
  }
  return sections.length > 0 ? sections : null
}

export default function DebateMessage({ role, content }) {
  const safeContent = content || ''

  if (role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] bg-user-bubble border border-border rounded-2xl rounded-br-sm px-4 py-3">
          <p className="font-body text-[15px] leading-relaxed">{safeContent}</p>
        </div>
      </div>
    )
  }

  const sections = parseStructuredReply(safeContent)

  if (!sections) {
    return (
      <div className="flex justify-start">
        <div className="max-w-[80%] bg-bg-card border border-border rounded-2xl rounded-bl-sm px-4 py-3">
          <p className="font-body text-[15px] leading-relaxed text-text">
            {safeContent || 'No response received.'}
          </p>
        </div>
      </div>
    )
  }

  const lastSection = sections[sections.length - 1]
  const bodySections = sections.slice(0, -1)

  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] flex flex-col gap-3">
        <div className="bg-bg-card border border-border rounded-2xl rounded-bl-sm px-5 py-4 flex flex-col gap-3">
          {bodySections.map((s, i) => (
            <div key={i}>
              <span className="font-mono text-[10px] tracking-wider uppercase text-text-muted">{s.label}</span>
              <p className="font-body text-[15px] leading-relaxed mt-1">{s.content}</p>
            </div>
          ))}
        </div>
        {lastSection && (
          <div className="border border-accent-dim bg-accent/10 rounded-xl px-4 py-3 flex gap-3 items-start">
            <span className="font-mono text-[10px] tracking-wider uppercase text-accent mt-0.5 shrink-0">Your Move</span>
            <p className="font-display text-[16px] leading-snug text-text italic">{lastSection.content}</p>
          </div>
        )}
      </div>
    </div>
  )
}