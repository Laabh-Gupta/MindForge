export default function SessionReview({ evaluation, scores, topic, onStartNew }) {
  if (!evaluation) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <span className="font-mono text-sm text-text-muted animate-pulse">Evaluating your session…</span>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-bg px-6 py-10">
      <div className="max-w-2xl mx-auto flex flex-col gap-8">
        <div className="flex flex-col gap-2 text-center">
          <span className="font-mono text-xs tracking-widest uppercase text-accent">Session Complete</span>
          <h1 className="font-display text-3xl text-text">{topic}</h1>
        </div>

        <div className="flex flex-col items-center gap-2">
          <span className="font-display text-6xl text-accent">{Math.round(evaluation.overall_score)}</span>
          <span className="font-mono text-xs uppercase tracking-wider text-text-muted">Overall Score</span>
        </div>

        <div className="bg-bg-card border border-border rounded-xl px-5 py-4">
          <span className="font-mono text-[10px] tracking-wider uppercase text-text-muted">Summary</span>
          <p className="font-body text-[15px] leading-relaxed text-text mt-2">{evaluation.summary}</p>
        </div>

        <div className="flex flex-col gap-3">
          {scores.map((s, i) => (
            <div key={i} className="bg-bg-card border border-border rounded-xl px-5 py-4 flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="font-body font-semibold text-text capitalize">{s.category.replace(/_/g, ' ')}</span>
                <span className="font-mono text-accent text-sm">{Math.round(s.score)}</span>
              </div>
              <p className="font-body text-sm text-text-muted"><span className="text-text">Strength:</span> {s.strength}</p>
              <p className="font-body text-sm text-text-muted"><span className="text-text">Weakness:</span> {s.weakness}</p>
            </div>
          ))}
        </div>

        <button
          className="bg-accent text-bg font-body font-semibold rounded-xl py-3 hover:bg-accent-dim transition-colors"
          onClick={onStartNew}
        >
          Start New Session
        </button>
      </div>
    </div>
  )
}