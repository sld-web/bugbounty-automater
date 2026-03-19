import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Target,
  Bug,
  CheckCircle,
  AlertTriangle,
  Play,
  Pause,
  ArrowRight,
} from 'lucide-react'
import { api, ENDPOINTS } from '../services/api'
import { useAppStore } from '../store'

export default function Dashboard() {
  const { programs, targets, pendingApprovals, setPrograms, setTargets, setPendingApprovals } = useAppStore()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [programsRes, targetsRes, approvalsRes] = await Promise.all([
          api.get(ENDPOINTS.programs),
          api.get(ENDPOINTS.targets),
          api.get(ENDPOINTS.approvalQueue),
        ])
        setPrograms(programsRes.data)
        setTargets(targetsRes.data.items || [])
        setPendingApprovals(approvalsRes.data.pending?.length || 0)
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const stats = [
    {
      name: 'Programs',
      value: programs.length,
      icon: Bug,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
    },
    {
      name: 'Targets',
      value: targets.length,
      icon: Target,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
    },
    {
      name: 'Pending Approvals',
      value: pendingApprovals,
      icon: AlertTriangle,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-500/10',
    },
  ]

  const runningTargets = targets.filter((t) => t.status === 'RUNNING')
  const recentFindings = [] // TODO: Fetch from API

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-slate-400 mt-1">
          Overview of your bug bounty hunting activities
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`w-6 h-6 ${stat.color}`} />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{stat.value}</p>
                <p className="text-sm text-slate-400">{stat.name}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Running Targets</h2>
            <Link
              to="/targets"
              className="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1"
            >
              View all <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {loading ? (
            <div className="animate-pulse space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 bg-slate-700 rounded-lg" />
              ))}
            </div>
          ) : runningTargets.length > 0 ? (
            <div className="space-y-3">
              {runningTargets.map((target) => (
                <div
                  key={target.id}
                  className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    <div>
                      <p className="font-medium text-white">{target.name}</p>
                      <p className="text-sm text-slate-400">
                        {target.program_name}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-right mr-4">
                      <p className="text-sm text-slate-400">Coverage</p>
                      <p className="font-medium text-white">
                        {target.surface_coverage || 0}%
                      </p>
                    </div>
                    <button className="p-2 hover:bg-slate-600 rounded-lg transition-colors">
                      <Pause className="w-5 h-5 text-yellow-500" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-400">
              <Target className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No targets currently running</p>
              <Link
                to="/programs"
                className="text-primary-400 hover:text-primary-300 mt-2 inline-block"
              >
                Start a new target
              </Link>
            </div>
          )}
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Recent Findings</h2>
            <Link
              to="/dashboard"
              className="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1"
            >
              View all <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="text-center py-8 text-slate-400">
            <Bug className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No recent findings</p>
            <p className="text-sm mt-1">
              Start a target scan to discover vulnerabilities
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
