import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react'
import { api, ENDPOINTS } from '../services/api'
import toast from 'react-hot-toast'

export default function Approvals() {
  const [approvals, setApprovals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchApprovals = async () => {
      try {
        const res = await api.get(ENDPOINTS.approvals, {
          params: { status_filter: 'PENDING' },
        })
        setApprovals(res.data.items || [])
      } catch (error) {
        console.error('Failed to fetch approvals:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchApprovals()
    const interval = setInterval(fetchApprovals, 10000)
    return () => clearInterval(interval)
  }, [])

  const handleApprove = async (id: string) => {
    try {
      await api.post(ENDPOINTS.approvalApprove(id), {
        decision: 'approve',
        decided_by: 'operator',
      })
      setApprovals(approvals.filter((a) => a.id !== id))
      toast.success('Request approved')
    } catch (error) {
      toast.error('Failed to approve request')
    }
  }

  const handleDeny = async (id: string) => {
    try {
      await api.post(ENDPOINTS.approvalDeny(id), {
        decision: 'deny',
        decided_by: 'operator',
        reason: 'Denied by operator',
      })
      setApprovals(approvals.filter((a) => a.id !== id))
      toast.success('Request denied')
    } catch (error) {
      toast.error('Failed to deny request')
    }
  }

  const riskColors = {
    LOW: 'text-green-500 bg-green-500/10',
    MEDIUM: 'text-yellow-500 bg-yellow-500/10',
    HIGH: 'text-orange-500 bg-orange-500/10',
    CRITICAL: 'text-red-500 bg-red-500/10',
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Approval Queue</h1>
        <p className="text-slate-400 mt-1">
          {approvals.length} pending approval{approvals.length !== 1 ? 's' : ''}
        </p>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-24 bg-slate-700 rounded" />
            </div>
          ))}
        </div>
      ) : approvals.length > 0 ? (
        <div className="space-y-4">
          {approvals.map((approval) => (
            <div key={approval.id} className="card">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-white text-lg">
                    {approval.action_type}
                  </h3>
                  <p className="text-slate-400 mt-1">{approval.action_description}</p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    riskColors[approval.risk_level] || riskColors.MEDIUM
                  }`}
                >
                  {approval.risk_level} ({approval.risk_score})
                </span>
              </div>

              {approval.proposed_command && (
                <div className="mb-4">
                  <p className="text-sm text-slate-500 mb-1">Proposed Command</p>
                  <pre className="bg-slate-900 p-3 rounded-lg text-sm text-slate-300 overflow-x-auto">
                    {approval.proposed_command}
                  </pre>
                </div>
              )}

              <div className="flex items-center justify-between pt-4 border-t border-slate-700">
                <div className="flex items-center gap-4 text-sm text-slate-400">
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    Expires in{' '}
                    {approval.expires_at
                      ? Math.round(
                          (new Date(approval.expires_at).getTime() - Date.now()) /
                            60000
                        )
                      : 30}{' '}
                    min
                  </div>
                  {approval.plugin_name && (
                    <span>Plugin: {approval.plugin_name}</span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleDeny(approval.id)}
                    className="btn btn-danger flex items-center gap-2"
                  >
                    <XCircle className="w-4 h-4" />
                    Deny
                  </button>
                  <button
                    onClick={() => handleApprove(approval.id)}
                    className="btn btn-primary flex items-center gap-2"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Approve
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <CheckCircle className="w-16 h-16 mx-auto text-green-500 mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">All clear!</h2>
          <p className="text-slate-400">
            No pending approval requests at the moment
          </p>
        </div>
      )}
    </div>
  )
}
