import { useState, useEffect } from 'react';
import { 
  Play, RefreshCw, CheckCircle, XCircle,
  Zap, Key, Send
} from 'lucide-react';
import { GlassCard, CyberButton } from '@/components/ui';
import { testingApi, targetsApi, programsApi } from '@/services/api';
import toast from 'react-hot-toast';

interface Strategy {
  name: string;
  description: string;
  auth_level: string;
}

interface AccountRequest {
  id: string;
  program_id: string;
  program_name: string;
  auth_level: string;
  status: string;
  created_at: string;
  requested_by: string;
  notes: string;
}

export default function Testing() {
  const [activeTab, setActiveTab] = useState<'mixed' | 'accounts'>('mixed');
  const [loading, setLoading] = useState(true);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [targets, setTargets] = useState<any[]>([]);
  const [programs, setPrograms] = useState<any[]>([]);
  const [accountRequests, setAccountRequests] = useState<AccountRequest[]>([]);
  const [running, setRunning] = useState(false);
  
  // Mixed mode form
  const [selectedTarget, setSelectedTarget] = useState('');
  const [selectedStrategy, setSelectedStrategy] = useState('');
  
  // Account request form
  const [newRequest, setNewRequest] = useState({
    program_id: '',
    auth_level: 'L1',
    notes: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [stratRes, targetsRes, programsRes, pendingRes] = await Promise.all([
        testingApi.strategies(),
        targetsApi.list(),
        programsApi.list(),
        testingApi.getPending()
      ]);
      setStrategies(stratRes.data.strategies || []);
      setTargets(targetsRes.data.targets || targetsRes.data || []);
      setPrograms(programsRes.data.programs || programsRes.data || []);
      setAccountRequests(pendingRes.data.requests || []);
    } catch (error) {
      toast.error('Failed to load testing data');
    } finally {
      setLoading(false);
    }
  };

  const runMixedMode = async () => {
    if (!selectedTarget) {
      toast.error('Select a target');
      return;
    }
    try {
      setRunning(true);
      await testingApi.mixedMode({
        target_id: selectedTarget,
        strategy: selectedStrategy || undefined
      });
      toast.success('Mixed mode testing started');
    } catch (error) {
      toast.error('Failed to start mixed mode testing');
    } finally {
      setRunning(false);
    }
  };

  const createAccountRequest = async () => {
    if (!newRequest.program_id) {
      toast.error('Select a program');
      return;
    }
    try {
      await testingApi.createAccountRequest({
        program_id: newRequest.program_id,
        auth_level: newRequest.auth_level,
        notes: newRequest.notes
      });
      toast.success('Account request created');
      setNewRequest({ program_id: '', auth_level: 'L1', notes: '' });
      loadData();
    } catch (error) {
      toast.error('Failed to create account request');
    }
  };

  const updateRequestStatus = async (id: string, status: string) => {
    try {
      await testingApi.updateAccountRequest(id, { status });
      toast.success(`Request ${status}`);
      loadData();
    } catch (error) {
      toast.error('Failed to update request');
    }
  };

  const tabs = [
    { id: 'mixed', label: 'Mixed Mode Testing', icon: Zap },
    { id: 'accounts', label: 'Account Requests', icon: Key },
  ];

  return (
    <div className="space-y-6">
      <div className="glass-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-headline text-primary tracking-wider">
              TESTING
            </h1>
            <p className="text-xs font-mono text-white/50 mt-1">
              Mixed mode testing and credential management
            </p>
          </div>
          <CyberButton variant="secondary" onClick={loadData} loading={loading}>
            <RefreshCw className="w-4 h-4" />
          </CyberButton>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <GlassCard className="p-0 overflow-hidden">
            <nav className="py-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-mono transition-colors ${
                    activeTab === tab.id
                      ? 'text-primary bg-primary/10 border-r-2 border-secondary'
                      : 'text-white/60 hover:text-white hover:bg-surface-50/50'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </GlassCard>
        </div>

        <div className="lg:col-span-3">
          {activeTab === 'mixed' && (
            <div className="space-y-6">
              <GlassCard className="p-6">
                <h2 className="section-title mb-4">Run Mixed Mode Testing</h2>
                <p className="text-sm text-white/60 mb-4">
                  Automated testing that combines multiple techniques based on program requirements.
                </p>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="data-label">Target</label>
                    <select
                      value={selectedTarget}
                      onChange={(e) => setSelectedTarget(e.target.value)}
                      className="input"
                    >
                      <option value="">Select target...</option>
                      {targets.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.name || t.url}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="data-label">Strategy (Optional)</label>
                    <select
                      value={selectedStrategy}
                      onChange={(e) => setSelectedStrategy(e.target.value)}
                      className="input"
                    >
                      <option value="">Auto-select</option>
                      {strategies.map((s) => (
                        <option key={s.name} value={s.name}>
                          {s.name} ({s.auth_level})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <CyberButton onClick={runMixedMode} loading={running}>
                  <Play className="w-4 h-4" />
                  Start Testing
                </CyberButton>
              </GlassCard>

              <GlassCard className="p-6">
                <h2 className="section-title mb-4">Available Strategies</h2>
                <div className="space-y-3">
                  {strategies.map((strategy) => (
                    <div key={strategy.name} className="p-4 bg-surface-50/50 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-white font-mono">{strategy.name}</h3>
                          <p className="text-xs text-white/50 mt-1">{strategy.description}</p>
                        </div>
                        <span className="px-2 py-1 bg-secondary/20 text-secondary text-xs rounded">
                          {strategy.auth_level}
                        </span>
                      </div>
                    </div>
                  ))}
                  {strategies.length === 0 && (
                    <div className="text-center py-8 text-white/30">
                      No strategies configured
                    </div>
                  )}
                </div>
              </GlassCard>
            </div>
          )}

          {activeTab === 'accounts' && (
            <div className="space-y-6">
              <GlassCard className="p-6">
                <h2 className="section-title mb-4">Request Test Account</h2>
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div>
                    <label className="data-label">Program</label>
                    <select
                      value={newRequest.program_id}
                      onChange={(e) => setNewRequest({ ...newRequest, program_id: e.target.value })}
                      className="input"
                    >
                      <option value="">Select program...</option>
                      {programs.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="data-label">Auth Level</label>
                    <select
                      value={newRequest.auth_level}
                      onChange={(e) => setNewRequest({ ...newRequest, auth_level: e.target.value })}
                      className="input"
                    >
                      <option value="L1">L1 - No Auth</option>
                      <option value="L2">L2 - Basic Auth</option>
                      <option value="L3">L3 - Email Verified</option>
                      <option value="L4">L4 - Phone/ID Verified</option>
                    </select>
                  </div>
                  <div>
                    <label className="data-label">Notes</label>
                    <input
                      type="text"
                      value={newRequest.notes}
                      onChange={(e) => setNewRequest({ ...newRequest, notes: e.target.value })}
                      placeholder="Additional notes..."
                      className="input"
                    />
                  </div>
                </div>
                <CyberButton onClick={createAccountRequest}>
                  <Send className="w-4 h-4" />
                  Submit Request
                </CyberButton>
              </GlassCard>

              <GlassCard className="p-6">
                <h2 className="section-title mb-4">
                  Pending Requests ({accountRequests.length})
                </h2>
                <div className="space-y-3">
                  {accountRequests.map((request) => (
                    <div key={request.id} className="p-4 bg-surface-50/50 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-3">
                            <h3 className="text-white">{request.program_name}</h3>
                            <span className="px-2 py-0.5 bg-secondary/20 text-secondary text-xs rounded">
                              {request.auth_level}
                            </span>
                          </div>
                          <div className="flex items-center gap-4 mt-2 text-xs text-white/50">
                            <span>By: {request.requested_by}</span>
                            <span>{new Date(request.created_at).toLocaleDateString()}</span>
                          </div>
                          {request.notes && (
                            <p className="text-xs text-white/40 mt-2">{request.notes}</p>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <CyberButton
                            variant="secondary"
                            size="sm"
                            onClick={() => updateRequestStatus(request.id, 'approved')}
                          >
                            <CheckCircle className="w-4 h-4" />
                          </CyberButton>
                          <CyberButton
                            variant="danger"
                            size="sm"
                            onClick={() => updateRequestStatus(request.id, 'denied')}
                          >
                            <XCircle className="w-4 h-4" />
                          </CyberButton>
                        </div>
                      </div>
                    </div>
                  ))}
                  {accountRequests.length === 0 && (
                    <div className="text-center py-8 text-white/30">
                      No pending account requests
                    </div>
                  )}
                </div>
              </GlassCard>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
