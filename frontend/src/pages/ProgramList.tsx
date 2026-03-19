import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bug, Plus, ArrowRight, AlertCircle } from 'lucide-react'
import { api, ENDPOINTS } from '../services/api'

export default function ProgramList() {
  const [programs, setPrograms] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPrograms = async () => {
      try {
        const res = await api.get(ENDPOINTS.programs)
        setPrograms(res.data)
      } catch (error) {
        console.error('Failed to fetch programs:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchPrograms()
  }, [])

  const platformColors: Record<string, string> = {
    hackerone: 'bg-green-600',
    bugcrowd: 'bg-red-600',
    yeswehack: 'bg-blue-600',
    openbugbounty: 'bg-yellow-600',
    manual: 'bg-slate-600',
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Programs</h1>
          <p className="text-slate-400 mt-1">
            {programs.length} programs configured
          </p>
        </div>
        <button className="btn btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Program
        </button>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-6 bg-slate-700 rounded w-2/3 mb-4" />
              <div className="h-4 bg-slate-700 rounded w-1/2 mb-4" />
              <div className="h-20 bg-slate-700 rounded" />
            </div>
          ))}
        </div>
      ) : programs.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {programs.map((program) => (
            <Link
              key={program.id}
              to={`/programs/${program.id}`}
              className="card hover:border-primary-500 transition-colors"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-slate-700 rounded-lg">
                    <Bug className="w-5 h-5 text-primary-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{program.name}</h3>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium text-white ${platformColors[program.platform] || 'bg-slate-600'}`}
                    >
                      {program.platform}
                    </span>
                  </div>
                </div>
                {program.needs_review && (
                  <div className="flex items-center gap-1 text-yellow-500">
                    <AlertCircle className="w-4 h-4" />
                    <span className="text-xs">Review needed</span>
                  </div>
                )}
              </div>

              <div className="space-y-2 text-sm text-slate-400 mb-4">
                <p>
                  <span className="text-slate-500">Domains:</span>{' '}
                  {program.scope?.domains?.length || 0}
                </p>
                <p>
                  <span className="text-slate-500">Targets:</span> {program.target_count || 0}
                </p>
                <p>
                  <span className="text-slate-500">Findings:</span> {program.finding_count || 0}
                </p>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-slate-700">
                <div className="text-sm">
                  <span className="text-slate-500">Confidence:</span>{' '}
                  <span className="text-white">
                    {Math.round((program.confidence_score || 0) * 100)}%
                  </span>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-500" />
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <Bug className="w-16 h-16 mx-auto text-slate-600 mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">No programs yet</h2>
          <p className="text-slate-400 mb-4">
            Add a bug bounty program to start hunting
          </p>
          <button className="btn btn-primary flex items-center gap-2 mx-auto">
            <Plus className="w-4 h-4" />
            Add Program
          </button>
        </div>
      )}
    </div>
  )
}
