import { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
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
  Shield,
  Activity,
  Globe,
  Database,
  Network,
} from 'lucide-react';
import { SeverityBadge, StatusIndicator, ProgressBar, CyberButton, Terminal, Modal } from '@/components/ui';
import { FlowChart, FlowCardData } from '../components/FlowChart';
import { api, ENDPOINTS } from '../services/api';

export default function TargetDetail() {
  const { targetId } = useParams<{ targetId: string }>();
  const [target, setTarget] = useState<any>(null);
  const [flowCards, setFlowCards] = useState<FlowCardData[]>([]);
  const [selectedCard, setSelectedCard] = useState<FlowCardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCardModal, setShowCardModal] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  const fetchData = useCallback(async () => {
    if (!targetId) return;

    try {
      const [targetRes, flowRes] = await Promise.all([
        api.get(ENDPOINTS.target(targetId)).catch(() => ({ data: null })),
        api.get(ENDPOINTS.targetFlows(targetId)).catch(() => ({ data: [] })),
      ]);
      setTarget(targetRes.data);
      setFlowCards(flowRes.data);

      if (targetRes.data) {
        setLogs([
          `[${new Date().toLocaleTimeString()}] Initializing target: ${targetRes.data.name}`,
          `[${new Date().toLocaleTimeString()}] Loading plugins...`,
          `[${new Date().toLocaleTimeString()}] Checking scope boundaries...`,
          `[${new Date().toLocaleTimeString()}] Target ready for scanning`,
        ]);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  }, [targetId]);

  useEffect(() => {
    if (!targetId) return;
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [targetId, fetchData]);

  const handleStart = async () => {
    if (!targetId) return;
    try {
      await api.post(ENDPOINTS.targetStart(targetId));
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Starting scan...`]);
      fetchData();
    } catch (error) {
      console.error('Failed to start target:', error);
    }
  };

  const handlePause = async () => {
    if (!targetId) return;
    try {
      await api.post(ENDPOINTS.targetPause(targetId));
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Scan paused`]);
      fetchData();
    } catch (error) {
      console.error('Failed to pause target:', error);
    }
  };

  const handleCardClick = (card: FlowCardData) => {
    setSelectedCard(card);
    setShowCardModal(true);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-surface-50/50 rounded w-1/3 animate-pulse" />
        <div className="h-64 glass-card rounded animate-pulse" />
      </div>
    );
  }

  if (!target) {
    return (
      <div className="text-center py-12">
        <Target className="w-16 h-16 mx-auto text-white/20 mb-4" />
        <h2 className="font-display text-xl text-primary mb-2">Target Not Found</h2>
        <Link to="/targets" className="text-secondary hover:underline font-mono text-sm">
          Back to targets
        </Link>
      </div>
    );
  }

  const statusMap: Record<string, 'running' | 'pending' | 'completed' | 'failed' | 'idle' | 'paused'> = {
    RUNNING: 'running',
    PENDING: 'pending',
    COMPLETED: 'completed',
    FAILED: 'failed',
    PAUSED: 'paused',
  };

  const cardStatusIcons: Record<string, { icon: React.ReactNode; color: string }> = {
    NOT_STARTED: { icon: <Clock className="w-4 h-4" />, color: 'text-white/40' },
    RUNNING: { icon: <RotateCcw className="w-4 h-4 animate-spin" />, color: 'text-secondary' },
    REVIEW: { icon: <AlertTriangle className="w-4 h-4" />, color: 'text-warning' },
    DONE: { icon: <CheckCircle className="w-4 h-4" />, color: 'text-tertiary' },
    FAILED: { icon: <XCircle className="w-4 h-4" />, color: 'text-error' },
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/targets"
            className="p-2 hover:bg-surface-50 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-white/60" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="font-display text-headline text-primary tracking-wider">
                {target.name}
              </h1>
              <StatusIndicator status={statusMap[target.status] || 'idle'} size="md" />
            </div>
            <div className="flex items-center gap-4 mt-1">
              <span className="text-xs font-mono text-white/40">
                Program: <span className="text-secondary">{target.program_name || 'Unknown'}</span>
              </span>
              <span className="text-xs font-mono text-white/30">
                ID: {target.id}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {target.status === 'PENDING' && (
            <CyberButton onClick={handleStart}>
              <span className="flex items-center gap-2">
                <Play className="w-4 h-4" />
                Start Scan
              </span>
            </CyberButton>
          )}
          {target.status === 'RUNNING' && (
            <CyberButton variant="secondary" onClick={handlePause}>
              <span className="flex items-center gap-2">
                <Pause className="w-4 h-4" />
                Pause
              </span>
            </CyberButton>
          )}
          {target.status === 'PAUSED' && (
            <CyberButton variant="action" onClick={handleStart}>
              <span className="flex items-center gap-2">
                <RotateCcw className="w-4 h-4" />
                Resume
              </span>
            </CyberButton>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-6">
            <div className="panel-header">
              <h2 className="section-title">Testing Workflow</h2>
              <span className="text-xs font-mono text-white/30">
                {flowCards.filter(c => c.status === 'DONE').length} / {flowCards.length} Complete
              </span>
            </div>
            <FlowChart
              cards={flowCards}
              selectedCardId={selectedCard?.id}
              onCardClick={handleCardClick}
            />
          </div>

          <div className="glass-card p-6">
            <div className="panel-header">
              <h2 className="section-title">Live Console</h2>
              <span className="flex items-center gap-1.5 text-[10px] font-mono text-tertiary">
                <span className="w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse" />
                {target.status === 'RUNNING' ? 'STREAMING' : 'IDLE'}
              </span>
            </div>
            <Terminal logs={logs} maxLines={20} />
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass-card p-6">
            <div className="panel-header">
              <h2 className="section-title">Coverage Metrics</h2>
            </div>
            <div className="space-y-5">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Globe className="w-4 h-4 text-secondary" />
                    <span className="text-xs font-mono text-white/70">Surface</span>
                  </div>
                  <span className="font-mono text-sm text-secondary">
                    {target.surface_coverage || 0}%
                  </span>
                </div>
                <ProgressBar value={target.surface_coverage || 0} color="secondary" />
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-error" />
                    <span className="text-xs font-mono text-white/70">Attack Vectors</span>
                  </div>
                  <span className="font-mono text-sm text-error">
                    {target.attack_vector_coverage || 0}%
                  </span>
                </div>
                <ProgressBar value={target.attack_vector_coverage || 0} color="error" />
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-warning" />
                    <span className="text-xs font-mono text-white/70">Logic Flows</span>
                  </div>
                  <span className="font-mono text-sm text-warning">
                    {target.logic_flow_coverage || 0}%
                  </span>
                </div>
                <ProgressBar value={target.logic_flow_coverage || 0} color="tertiary" />
              </div>
            </div>
          </div>

          <div className="glass-card p-6">
            <div className="panel-header">
              <h2 className="section-title">Target Info</h2>
            </div>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <Shield className="w-4 h-4 text-white/40 mt-0.5" />
                <div className="flex-1">
                  <div className="text-[10px] font-mono text-white/40 uppercase">Scope</div>
                  <div className="font-mono text-xs text-white mt-1">
                    {target.scope || 'In Scope'}
                  </div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Database className="w-4 h-4 text-white/40 mt-0.5" />
                <div className="flex-1">
                  <div className="text-[10px] font-mono text-white/40 uppercase">Subdomains</div>
                  <div className="font-mono text-xs text-white mt-1">
                    {target.subdomains?.length || 0} discovered
                  </div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Network className="w-4 h-4 text-white/40 mt-0.5" />
                <div className="flex-1">
                  <div className="text-[10px] font-mono text-white/40 uppercase">Endpoints</div>
                  <div className="font-mono text-xs text-white mt-1">
                    {target.endpoints?.length || 0} found
                  </div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Bug className="w-4 h-4 text-white/40 mt-0.5" />
                <div className="flex-1">
                  <div className="text-[10px] font-mono text-white/40 uppercase">Findings</div>
                  <div className="font-mono text-xs text-white mt-1">
                    {target.findings?.length || 0} detected
                  </div>
                </div>
              </div>
            </div>
          </div>

          {target.technologies?.length > 0 && (
            <div className="glass-card p-6">
              <div className="panel-header">
                <h2 className="section-title">Technologies</h2>
              </div>
              <div className="flex flex-wrap gap-2">
                {target.technologies.map((tech: string) => (
                  <span
                    key={tech}
                    className="px-2 py-1 bg-surface-50/50 text-xs font-mono text-secondary rounded"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {selectedCard && (
        <Modal
          isOpen={showCardModal}
          onClose={() => setShowCardModal(false)}
          title={selectedCard.name}
          size="lg"
        >
          <div className="space-y-6">
            <div className="flex items-center gap-4">
              <div className={`flex items-center gap-2 ${cardStatusIcons[selectedCard.status]?.color}`}>
                {cardStatusIcons[selectedCard.status]?.icon}
                <span className="font-mono text-sm uppercase">{selectedCard.status}</span>
              </div>
              <SeverityBadge severity="info" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="glass-card-subtle p-4">
                <div className="text-[10px] font-mono text-white/40 uppercase mb-1">Type</div>
                <div className="font-mono text-sm text-white">{selectedCard.card_type}</div>
              </div>
              <div className="glass-card-subtle p-4">
                <div className="text-[10px] font-mono text-white/40 uppercase mb-1">Duration</div>
                <div className="font-mono text-sm text-white">
                  {selectedCard.duration_seconds ? `${selectedCard.duration_seconds}s` : 'N/A'}
                </div>
              </div>
            </div>

            {selectedCard.description && (
              <div className="glass-card-subtle p-4">
                <div className="text-[10px] font-mono text-white/40 uppercase mb-2">Description</div>
                <p className="font-mono text-sm text-white/80">{selectedCard.description}</p>
              </div>
            )}

            {selectedCard.error && (
              <div className="glass-card-subtle p-4 border border-error/30">
                <div className="text-[10px] font-mono text-error uppercase mb-2">Error</div>
                <p className="font-mono text-sm text-error">{selectedCard.error}</p>
              </div>
            )}

            {selectedCard.logs && selectedCard.logs.length > 0 && (
              <div>
                <div className="text-[10px] font-mono text-white/40 uppercase mb-2">Logs</div>
                <Terminal logs={selectedCard.logs} className="h-48" />
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
