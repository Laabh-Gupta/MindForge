import { useNavigate } from 'react-router-dom'

export default function Dashboard() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-md w-full flex flex-col gap-4">
        <h1 className="font-display text-3xl text-text text-center mb-2">
          Choose your training
        </h1>

        <button
          className="bg-bg-card border border-border rounded-xl py-4 font-body text-text hover:border-accent-dim transition-colors"
          onClick={() => navigate('/debate')}
        >
          Debate Arena
        </button>

        <button
          className="bg-bg-card border border-border rounded-xl py-4 font-body text-text hover:border-accent-dim transition-colors"
          onClick={() => navigate('/interview')}
        >
          Interview Simulator
        </button>
      </div>
    </div>
  )
}