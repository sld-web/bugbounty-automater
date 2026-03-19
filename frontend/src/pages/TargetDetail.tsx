import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Play,
  Pause,
  RotateCcw,
  ArrowLeft,
  Bug,
  Target,
  AlertTriangle,
  Clock,
  CheckCircle,
  XCircle,
} from 'lucide-react'
import { api, ENDPOINTS } from '../services/api'
import { FlowChart, FlowCardData } from '../components/FlowChart'

export default function TargetDetail() {
  const { targetId } = useParams<{ targetId: string }>()
  const [target, setTarget] = useState<any>(null)
  const [flowCards, setFlowCards] = useState<FlowCardData[]>([])
  const [selectedCard, setSelectedCard] = useState<FlowCardData | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    if (!targetId) return

    try {
      const [targetRes, flowRes] = await Promise.all([
        api.get(ENDPOINTS.target(targetId)),
        api.get(ENDPOINTS.targetFlows(targetId)),
      ])
      setTarget(targetRes.data)
      setFlowCards(flowRes.data)
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }, [targetId])

  useEffect(() => {
    if (!targetId) return
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [targetId, fetchData])

  const handleStart = async () => {
    if (!targetId) return
    try {
      await api.post(ENDPOINTS.targetStart(targetId))
      fetchData()
    } catch (error) {
      console.error('Failed to start target:', error)
    }
  }

  const handlePause = async () => {
    if (!targetId) return
    try {
      await api.post(ENDPOINTS.targetPause(targetId))
      fetchData()
    } catch (error) {
      console.error('Failed to pause target:', error)
    }
  }

  const handleCardClick = (card: FlowCardData) => {
    setSelectedCard(card)
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-slate-700 rounded w-1/3" />
          <div className="h-64 bg-slate-700 rounded-lg" />
        </div>
      </div>
    )
  }

  if (!target) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <Target className="w-16 h-16 mx-auto text-slate-600 mb-4" />
          <h2 className="text-xl font-semibold text-white">Target not found</h2>
          <Link to="/targets" className="text-primary-400 hover:text-primary-300 mt-2 inline-block">
            Back to targets
          </Link>
        </div>
      </div>
    )
  }

  const statusColors: Record<string, string> = {
    PENDING: 'bg-slate-500',
    RUNNING: 'bg-green-500',
    PAUSED: 'bg-yellow-500',
    COMPLETED: 'bg-blue-500',
    FAILED: 'bg-red-500',
    CANCELLED: 'bg-slate-600',
  }

  const cardStatusIcons: Record<string, JSX.Element> = {
    NOT_STARTED: <Clock className="w-4 h-4 text-gray-400" />,
    RUNNING: <RotateCcw className="w-4 h-4 text-blue-500 animate-spin" />,
    REVIEW: <AlertTriangle className="w-4 h-4 text-yellow-500" />,
    DONE: <CheckCircle className="w-4 h-4 text-green-500" />,
    FAILED: <XCircle className="w-4 h-4 text-red-500" />,
    BLOCKED: <XCircle className="w-4 h-4 text-purple-500" />,
    FLAGGED: <AlertTriangle className="w-4 h-4 text-orange-500" />,
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <Link
          to="/targets"
          className="text-slate-400 hover:text-white flex items-center gap-2 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to targets
        </Link>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-white">{target.name}</h1>
            <span
              className={`px-3 py-1 rounded-full text-xs font-medium text-white ${statusColors[target.status]}`}
            >
              {target.status}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {target.status === 'PENDING' && (
              <button onClick={handleStart} className="btn btn-primary flex items-center gap-2">
                <Play className="w-4 h-4" />
                Start
              </button>
            )}
            {target.status === 'RUNNING' && (
              <button onClick={handlePause} className="btn btn-secondary flex items-center gap-2">
                <Pause className="w-4 h-4" />
                Pause
              </button>
            )}
            {target.status === 'PAUSED' && (
              <button onClick={handleStart} className="btn btn-primary flex items-center gap-2">
                <RotateCcw className="w-4 h-4" />
                Resume
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2">
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Testing Workflow</h2>
            <FlowChart
              cards={flowCards}
              selectedCardId={selectedCard?.id}
              onCardClick={handleCardClick}
            />
          </div>
        </div>

        <div>
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Coverage</h2>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-slate-400 mb-1">Surface</p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500"
                      style={{ width: `${target.surface_coverage || 0}%` }}
                    />
                  </div>
                  <span className="text-sm text-white">{target.surface_coverage || 0}%</span>
                </div>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">Attack Vectors</p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-red-500"
                      style={{ width: `${target.attack_vector_coverage || 0}%` }}
                    />
                  </div>
                  <span className="text-sm text-white">{target.attack_vector_coverage || 0}%</span>
                </div>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">Logic Flows</p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-yellow-500"
                      style={{ width: `${target.logic_flow_coverage || 0}%` }}
                    />
                  </div>
                  <span className="text-sm text-white">{target.logic_flow_coverage || 0}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {selectedCard && (
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Card Details: {selectedCard.name}</h2>
            <button
              onClick={() => setSelectedCard(null)}
              className="text-slate-400 hover:text-white"
            >
              Close
            </button>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-slate-400 mb-1">Status</p>
              <div className="flex items-center gap-2">
                {cardStatusIcons[selectedCard.status]}
                <span className="text-white">{selectedCard.status}</span>
              </div>
            </div>
            <div>
              <p className="text-sm text-slate-400 mb-1">Type</p>
              <span className="text-white">{selectedCard.card_type}</span>
            </div>
            {selectedCard.description && (
              <div className="col-span-2">
                <p className="text-sm text-slate-400 mb-1">Description</p>
                <p className="text-white">{selectedCard.description}</p>
              </div>
            )}
            {selectedCard.duration_seconds && (
              <div>
                <p className="text-sm text-slate-400 mb-1">Duration</p>
                <span className="text-white">{selectedCard.duration_seconds}s</span>
              </div>
            )}
            {selectedCard.error && (
              <div className="col-span-2">
                <p className="text-sm text-slate-400 mb-1">Error</p>
                <p className="text-red-400">{selectedCard.error}</p>
              </div>
            )}
            {selectedCard.logs && selectedCard.logs.length > 0 && (
              <div className="col-span-2">
                <p className="text-sm text-slate-400 mb-1">Logs</p>
                <div className="bg-slate-800 rounded p-2 max-h-32 overflow-auto">
                  {selectedCard.logs.map((log, i) => (
                    <p key={i} className="text-xs text-slate-400 font-mono">{log}</p>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Discovered Assets</h2>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-slate-400 mb-2">
                  Subdomains ({target.subdomains?.length || 0})
                </p>
                <div className="flex flex-wrap gap-2">
                  {target.subdomains?.length > 0 ? (
                    target.subdomains.map((sub: string) => (
                      <span
                        key={sub}
                        className="px-2 py-1 bg-slate-700 rounded text-sm text-white"
                      >
                        {sub}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-500">No subdomains discovered</span>
                  )}
                </div>
              </div>

              <div>
                <p className="text-sm text-slate-400 mb-2">
                  Endpoints ({target.endpoints?.length || 0})
                </p>
                <div className="flex flex-wrap gap-2">
                  {target.endpoints?.length > 0 ? (
                    target.endpoints.slice(0, 10).map((ep: any) => (
                      <span
                        key={ep.url}
                        className="px-2 py-1 bg-slate-700 rounded text-sm text-white"
                      >
                        {ep.url}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-500">No endpoints discovered</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Technologies</h2>
            <div className="space-y-2">
              {target.technologies?.length > 0 ? (
                target.technologies.map((tech: string) => (
                  <div key={tech} className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-primary-500 rounded-full" />
                    <span className="text-white">{tech}</span>
                  </div>
                ))
              ) : (
                <p className="text-slate-500">No technologies detected</p>
              )}
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Ports</h2>
            <div className="flex flex-wrap gap-2">
              {target.ports?.length > 0 ? (
                target.ports.map((port: any) => (
                  <span
                    key={port.port}
                    className="px-2 py-1 bg-slate-700 rounded text-sm text-white"
                  >
                    {port.port}/{port.service}
                  </span>
                ))
              ) : (
                <p className="text-slate-500">No ports scanned</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
