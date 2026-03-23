import { useEffect, useState } from 'react';
import { CheckCircle, XCircle, Clock, Shield, Zap, History } from 'lucide-react';
import { GlassCard, CyberButton, SeverityBadge, Modal } from '@/components/ui';
import { api, ENDPOINTS } from '../services/api';
import toast from 'react-hot-toast';

interface Approval {
  id: string;
  action_type: string;
  action_description: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_score: number;
  proposed_command?: string;
  plugin_name?: string;
  expires_at?: string;
  target?: string;
}

const riskColors = {
  LOW: 'text-tertiary bg-tertiary/10 border-tertiary/30',
  MEDIUM: 'text-warning bg-warning/10 border-warning/30',
  HIGH: 'text-error bg-error/10 border-error/30',
  CRITICAL: 'text-error bg-error/20 border-error/50',
};

export default function Approvals() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApproval, setSelectedApproval] = useState<Approval | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [processing, setProcessing] = useState<string | null>(null);

  useEffect(() => {
    const fetchApprovals = async () => {
      try {
        const res = await api.get(ENDPOINTS.approvals, {
          params: { status_filter: 'PENDING' },
        }).catch(() => ({ data: { items: [] } }));
        setApprovals(res.data.items || []);
      } catch (error) {
        console.error('Failed to fetch approvals:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchApprovals();
    const interval = setInterval(fetchApprovals, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleApprove = async (id: string) => {
    setProcessing(id);
    try {
      await api.post(ENDPOINTS.approvalApprove(id), {
        decision: 'approve',
        decided_by: 'operator',
      });
      setApprovals(approvals.filter((a) => a.id !== id));
      toast.success('Request approved successfully');
    } catch (error) {
      toast.error('Failed to approve request');
    } finally {
      setProcessing(null);
    }
  };

  const handleDeny = async (id: string) => {
    setProcessing(id);
    try {
      await api.post(ENDPOINTS.approvalDeny(id), {
        decision: 'deny',
        decided_by: 'operator',
        reason: 'Denied by operator',
      });
      setApprovals(approvals.filter((a) => a.id !== id));
      toast.success('Request denied');
    } catch (error) {
      toast.error('Failed to deny request');
    } finally {
      setProcessing(null);
    }
  };

  const handleDefer = async (id: string) => {
    setProcessing(id);
    try {
      await api.post(ENDPOINTS.approvalTimeout(id), {
        reason: 'Deferred for later review',
      });
      setApprovals(approvals.filter((a) => a.id !== id));
      toast.success('Request deferred');
    } catch (error) {
      toast.error('Failed to defer request');
    } finally {
      setProcessing(null);
    }
  };

  const openDetailModal = (approval: Approval) => {
    setSelectedApproval(approval);
    setShowDetailModal(true);
  };

  const auditTrail = [
    { id: '1', action: 'APPROVED', target: 'nuclei_scan.sh', user: 'admin', time: '14:23:18' },
    { id: '2', action: 'DENIED', target: 'sqlmap_scan.sh', user: 'admin', time: '14:20:45' },
    { id: '3', action: 'APPROVED', target: 'recon.sh', user: 'operator', time: '14:15:22' },
    { id: '4', action: 'AUTO_APPROVED', target: 'subfinder.sh', user: 'system', time: '14:10:00' },
  ];

  return (
    <div className="space-y-6">
      <div className="glass-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-headline text-primary tracking-wider">
              APPROVAL QUEUE
            </h1>
            <p className="text-xs font-mono text-white/50 mt-1">
              Human-in-the-loop decision requests
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="px-4 py-2 glass-card-subtle rounded-lg">
              <span className="text-[10px] font-mono text-white/40 uppercase">Pending</span>
              <span className="ml-2 font-display text-xl text-warning">{approvals.length}</span>
            </div>
            <div className="px-4 py-2 glass-card-subtle rounded-lg">
              <span className="text-[10px] font-mono text-white/40 uppercase">High Risk</span>
              <span className="ml-2 font-display text-xl text-error">
                {approvals.filter(a => a.risk_level === 'HIGH' || a.risk_level === 'CRITICAL').length}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="glass-card p-6 animate-pulse">
                  <div className="h-24 bg-surface-50/50 rounded" />
                </div>
              ))}
            </div>
          ) : approvals.length > 0 ? (
            approvals.map((approval) => (
              <GlassCard key={approval.id} className="p-0 overflow-hidden" onClick={() => openDetailModal(approval)}>
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-surface-50/50 rounded-lg">
                        <Zap className="w-5 h-5 text-secondary" />
                      </div>
                      <div>
                        <h3 className="font-display text-lg text-white">
                          {approval.action_type}
                        </h3>
                        <p className="text-xs font-mono text-white/50 mt-0.5">
                          {approval.action_description}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 border text-xs font-mono font-bold rounded ${riskColors[approval.risk_level]}`}>
                        {approval.risk_level} ({approval.risk_score})
                      </span>
                    </div>
                  </div>

                  {approval.proposed_command && (
                    <div className="mb-4 p-3 bg-surface-lowest rounded font-mono text-xs text-tertiary/80 overflow-x-auto">
                      <span className="text-[10px] text-white/30 uppercase mb-1 block">Command</span>
                      {approval.proposed_command}
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-4 border-t border-white/5">
                    <div className="flex items-center gap-4 text-xs font-mono text-white/40">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5" />
                        <span>
                          Expires in{' '}
                          {approval.expires_at
                            ? Math.round((new Date(approval.expires_at).getTime() - Date.now()) / 60000)
                            : 30}{' '}
                          min
                        </span>
                      </div>
                      {approval.plugin_name && (
                        <div className="flex items-center gap-1.5">
                          <Shield className="w-3.5 h-3.5" />
                          <span>{approval.plugin_name}</span>
                        </div>
                      )}
                      {approval.target && (
                        <div className="text-secondary">{approval.target}</div>
                      )}
                    </div>

                    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                      <CyberButton
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDefer(approval.id)}
                        disabled={processing === approval.id}
                      >
                        Defer
                      </CyberButton>
                      <CyberButton
                        variant="danger"
                        size="sm"
                        onClick={() => handleDeny(approval.id)}
                        loading={processing === approval.id}
                      >
                        <span className="flex items-center gap-1.5">
                          <XCircle className="w-3.5 h-3.5" />
                          Deny
                        </span>
                      </CyberButton>
                      <CyberButton
                        variant="action"
                        size="sm"
                        onClick={() => handleApprove(approval.id)}
                        disabled={processing === approval.id}
                      >
                        <span className="flex items-center gap-1.5">
                          <CheckCircle className="w-3.5 h-3.5" />
                          Approve
                        </span>
                      </CyberButton>
                    </div>
                  </div>
                </div>
              </GlassCard>
            ))
          ) : (
            <GlassCard className="p-12 text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-tertiary/10 flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-tertiary" />
              </div>
              <h2 className="font-display text-xl text-tertiary mb-2">All Clear</h2>
              <p className="text-sm font-mono text-white/40">
                No pending approval requests at the moment
              </p>
            </GlassCard>
          )}
        </div>

        <div className="space-y-6">
          <div className="glass-card p-6">
            <div className="panel-header">
              <h2 className="section-title">Auto-Rules</h2>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-surface-50/50 rounded">
                <div>
                  <div className="text-xs font-mono text-white">Auto-approve recon</div>
                  <div className="text-[10px] text-white/40">SAFE plugins only</div>
                </div>
                <div className="relative w-10 h-4 bg-tertiary rounded-full">
                  <div className="absolute right-0.5 top-0.5 w-3 h-3 bg-white rounded-full" />
                </div>
              </div>
              <div className="flex items-center justify-between p-3 bg-surface-50/50 rounded">
                <div>
                  <div className="text-xs font-mono text-white">Skip approval for L0</div>
                  <div className="text-[10px] text-white/40">Risk score 0-10</div>
                </div>
                <div className="relative w-10 h-4 bg-tertiary rounded-full">
                  <div className="absolute right-0.5 top-0.5 w-3 h-3 bg-white rounded-full" />
                </div>
              </div>
              <div className="flex items-center justify-between p-3 bg-surface-50/50 rounded">
                <div>
                  <div className="text-xs font-mono text-white">Request approval for L3+</div>
                  <div className="text-[10px] text-white/40">Risk score 70+</div>
                </div>
                <div className="relative w-10 h-4 bg-surface-200 rounded-full">
                  <div className="absolute left-0.5 top-0.5 w-3 h-3 bg-white/50 rounded-full" />
                </div>
              </div>
            </div>
          </div>

          <div className="glass-card p-6">
            <div className="panel-header">
              <h2 className="section-title">Audit Trail</h2>
              <History className="w-4 h-4 text-white/30" />
            </div>
            <div className="space-y-3">
              {auditTrail.map((log) => (
                <div key={log.id} className="flex items-center gap-3 py-2 border-b border-white/5 last:border-0">
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                    log.action === 'APPROVED' ? 'bg-tertiary/10 text-tertiary' :
                    log.action === 'DENIED' ? 'bg-error/10 text-error' :
                    'bg-secondary/10 text-secondary'
                  }`}>
                    {log.action}
                  </span>
                  <span className="text-xs font-mono text-white/70 flex-1 truncate">{log.target}</span>
                  <span className="text-[10px] font-mono text-white/30">{log.user}</span>
                  <span className="text-[10px] font-mono text-white/30">{log.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {selectedApproval && (
        <Modal
          isOpen={showDetailModal}
          onClose={() => setShowDetailModal(false)}
          title="Approval Details"
          size="lg"
        >
          <div className="space-y-6">
            <div className="flex items-center gap-4">
              <SeverityBadge severity={selectedApproval.risk_level === 'CRITICAL' ? 'critical' : selectedApproval.risk_level === 'HIGH' ? 'high' : selectedApproval.risk_level === 'MEDIUM' ? 'medium' : 'low'} />
              <span className={`px-3 py-1 border text-xs font-mono font-bold rounded ${riskColors[selectedApproval.risk_level]}`}>
                Risk Score: {selectedApproval.risk_score}
              </span>
            </div>

            <div className="glass-card-subtle p-4">
              <div className="text-[10px] font-mono text-white/40 uppercase mb-2">Action</div>
              <div className="font-display text-lg text-white">{selectedApproval.action_type}</div>
            </div>

            <div className="glass-card-subtle p-4">
              <div className="text-[10px] font-mono text-white/40 uppercase mb-2">Description</div>
              <div className="text-sm text-white/80">{selectedApproval.action_description}</div>
            </div>

            {selectedApproval.proposed_command && (
              <div className="glass-card-subtle p-4">
                <div className="text-[10px] font-mono text-white/40 uppercase mb-2">Proposed Command</div>
                <pre className="font-mono text-xs text-tertiary overflow-x-auto">
                  {selectedApproval.proposed_command}
                </pre>
              </div>
            )}

            <div className="flex gap-3">
              <CyberButton
                variant="danger"
                className="flex-1"
                onClick={() => {
                  handleDeny(selectedApproval.id);
                  setShowDetailModal(false);
                }}
              >
                Deny
              </CyberButton>
              <CyberButton
                variant="action"
                className="flex-1"
                onClick={() => {
                  handleApprove(selectedApproval.id);
                  setShowDetailModal(false);
                }}
              >
                Approve
              </CyberButton>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
