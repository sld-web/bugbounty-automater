import { useState, useEffect } from 'react';
import {
  Play,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Shield,
  ChevronDown,
  ChevronRight,
  Zap,
  Eye,
  Lock,
  Loader2,
  Terminal,
  GitBranch,
  User,
} from 'lucide-react';
import { GlassCard, CyberButton } from '@/components/ui';
import WorkflowExecutionModal from '@/components/WorkflowExecutionModal';
import { flowsApi, programsApi } from '@/services/api';
import toast from 'react-hot-toast';

interface WorkflowStep {
  id: string;
  type: string;
  name: string;
  tool: string | null;
  tool_available: boolean;
  auto: boolean;
  status: string;
  command: string | null;
  risk_level: string;
  requires_approval: boolean;
  approval_reason: string | null;
  payloads: any[];
  blockers: string[];
}

interface WorkflowPhase {
  id: string;
  name: string;
  description: string;
  order: number;
  steps: WorkflowStep[];
  status: string;
}

interface Workflow {
  id: string;
  program_name: string;
  phases: {
    target_id: string;
    target_name: string;
    target_type: string;
    domains: string[];
    ips: string[];
    phases: WorkflowPhase[];
    risk_score: { score: number; level: string };
    estimated_duration: { total: string; hours: number };
  }[];
  rules: string[];
  out_of_scope: string[];
  total_steps: number;
  auto_steps: number;
  manual_steps: number;
  approval_points: {
    step: string;
    phase: string;
    target: string;
    reason: string;
  }[];
}

export default function WorkflowVisualization({ programId }: { programId: string }) {
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [loading, setLoading] = useState(true);
  const [executingStep, setExecutingStep] = useState<string | null>(null);
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set());
  const [selectedTarget, setSelectedTarget] = useState<number>(0);
  const [rulesExpanded, setRulesExpanded] = useState(false);
  const [logs, setLogs] = useState<Record<string, string[]>>({});
  const [showApprovalModal, setShowApprovalModal] = useState<WorkflowStep | null>(null);
  const [showExecutionModal, setShowExecutionModal] = useState(false);

  useEffect(() => {
    loadWorkflow();
  }, [programId]);

  const loadWorkflow = async () => {
    try {
      setLoading(true);
      const programRes = await programsApi.get(programId);
      const program = programRes.data;

      if (program.workflow_data && program.workflow_data.phases && program.workflow_data.phases.length > 0) {
        setWorkflow(program.workflow_data);
        const firstTargetPhases = program.workflow_data.phases?.[0]?.phases || [];
        if (firstTargetPhases.length > 0) {
          setExpandedPhases(new Set([firstTargetPhases[0].id]));
        }
        setLoading(false);
        return;
      }

      const generateRes = await flowsApi.generateForProgram(programId);
      setWorkflow(generateRes.data.workflow);
      
      const firstTargetPhases = generateRes.data.workflow?.phases?.[0]?.phases || [];
      if (firstTargetPhases.length > 0) {
        setExpandedPhases(new Set([firstTargetPhases[0].id]));
      }
    } catch (err: any) {
      toast.error('Failed to load workflow: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const executeStep = async (step: WorkflowStep, target: string) => {
    if (!workflow) return;

    if (step.requires_approval) {
      setShowApprovalModal(step);
      return;
    }

    if (!step.tool_available) {
      toast.error(`Tool ${step.tool} is not installed`);
      return;
    }

    setExecutingStep(step.id);
    addLog(step.id, `Starting: ${step.name}`);

    try {
      const result = await flowsApi.executeStep({
        step_id: step.id,
        workflow_data: workflow,
        target: target,
      });

      if (result.data.status === 'completed') {
        addLog(step.id, `Completed successfully`);
        toast.success(`Step "${step.name}" completed`);
      } else if (result.data.status === 'manual_required') {
        addLog(step.id, `Manual execution required`);
        toast(`Step "${step.name}" requires manual execution`, { icon: 'ℹ️' });
      } else if (result.data.status === 'error') {
        addLog(step.id, `Error: ${result.data.error}`);
        toast.error(`Step "${step.name}" failed`);
      }
    } catch (err: any) {
      addLog(step.id, `Error: ${err.message}`);
      toast.error(`Failed to execute step`);
    } finally {
      setExecutingStep(null);
    }
  };

  const requestApproval = async (step: WorkflowStep, target: string) => {
    try {
      await flowsApi.requestApproval({
        step_id: step.id,
        workflow_data: workflow!,
        target,
        reason: step.approval_reason,
      });
      toast.success('Approval request submitted');
      setShowApprovalModal(null);
    } catch (err: any) {
      toast.error('Failed to submit approval request');
    }
  };

  const addLog = (stepId: string, message: string) => {
    setLogs(prev => ({
      ...prev,
      [stepId]: [...(prev[stepId] || []), `[${new Date().toLocaleTimeString()}] ${message}`],
    }));
  };

  const togglePhaseExpanded = (phaseId: string) => {
    const newExpanded = new Set(expandedPhases);
    if (newExpanded.has(phaseId)) {
      newExpanded.delete(phaseId);
    } else {
      newExpanded.add(phaseId);
    }
    setExpandedPhases(newExpanded);
  };

  const getStepIcon = (step: WorkflowStep) => {
    if (step.type === 'recon' || step.type === 'scan') return <Zap className="w-4 h-4" />;
    if (step.type === 'exploit') return <AlertTriangle className="w-4 h-4" />;
    if (step.type === 'manual_review') return <Eye className="w-4 h-4" />;
    return <Terminal className="w-4 h-4" />;
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'critical': return 'text-red-500 bg-red-500/10 border-red-500/30';
      case 'high': return 'text-orange-500 bg-orange-500/10 border-orange-500/30';
      case 'medium': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30';
      default: return 'text-green-500 bg-green-500/10 border-green-500/30';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <span className="ml-3 text-white/60">Generating workflow...</span>
      </div>
    );
  }

  if (!workflow || !workflow.phases || !workflow.phases.length) {
    return (
      <GlassCard className="p-8 text-center">
        <GitBranch className="w-12 h-12 mx-auto text-white/30 mb-4" />
        <h3 className="text-lg font-display text-white mb-2">No Workflow Generated</h3>
        <p className="text-white/50">Create targets or add domains to your program to generate a testing workflow.</p>
        <div className="mt-4 text-xs text-white/30">
          Debug: {workflow ? 'Workflow loaded but no phases' : 'No workflow data'}
        </div>
      </GlassCard>
    );
  }

  const currentTarget = workflow.phases[selectedTarget];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4 mb-6">
        <GlassCard className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Terminal className="w-5 h-5 text-primary" />
            </div>
            <div>
              <div className="text-2xl font-mono text-white">{workflow.total_steps}</div>
              <div className="text-xs text-white/50">Total Steps</div>
            </div>
          </div>
        </GlassCard>
        <GlassCard className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-tertiary/10 rounded-lg">
              <Zap className="w-5 h-5 text-tertiary" />
            </div>
            <div>
              <div className="text-2xl font-mono text-tertiary">{workflow.auto_steps}</div>
              <div className="text-xs text-white/50">Auto Steps</div>
            </div>
          </div>
        </GlassCard>
        <GlassCard className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-warning/10 rounded-lg">
              <User className="w-5 h-5 text-warning" />
            </div>
            <div>
              <div className="text-2xl font-mono text-warning">{workflow.manual_steps}</div>
              <div className="text-xs text-white/50">Manual Steps</div>
            </div>
          </div>
        </GlassCard>
        <GlassCard className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <Shield className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <div className="text-2xl font-mono text-blue-400">{workflow.approval_points.length}</div>
              <div className="text-xs text-white/50">Approvals</div>
            </div>
          </div>
        </GlassCard>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-4 overflow-x-auto pb-2">
          {workflow.phases.map((target, idx) => (
            <button
              key={target.target_id}
              onClick={() => setSelectedTarget(idx)}
              className={`px-4 py-2 rounded-lg whitespace-nowrap transition-all ${
                selectedTarget === idx
                  ? 'bg-primary text-white'
                  : 'bg-surface-50/50 text-white/60 hover:bg-surface-100/50'
              }`}
            >
              {target.target_name}
            </button>
          ))}
        </div>
        <CyberButton
          variant="action"
          size="lg"
          onClick={() => setShowExecutionModal(true)}
        >
          <Play className="w-5 h-5 mr-2" />
          Start Workflow Execution
        </CyberButton>
      </div>

      <div className="flex gap-4 mb-6 overflow-x-auto pb-2 hidden">
        {workflow.phases.map((target, idx) => (
          <button
            key={target.target_id}
            onClick={() => setSelectedTarget(idx)}
            className={`px-4 py-2 rounded-lg whitespace-nowrap transition-all ${
              selectedTarget === idx
                ? 'bg-primary text-white'
                : 'bg-surface-50/50 text-white/60 hover:bg-surface-100/50'
            }`}
          >
            {target.target_name}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-4">
          {currentTarget?.phases.map((phase) => (
            <GlassCard key={phase.id} className="overflow-hidden">
              <div
                className="flex items-center justify-between p-4 cursor-pointer hover:bg-white/5"
                onClick={() => togglePhaseExpanded(phase.id)}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    phase.order <= 1 ? 'bg-primary/10 text-primary' :
                    phase.order <= 3 ? 'bg-tertiary/10 text-tertiary' :
                    phase.order <= 5 ? 'bg-warning/10 text-warning' :
                    'bg-blue-500/10 text-blue-400'
                  }`}>
                    <span className="font-mono text-sm">{phase.order}</span>
                  </div>
                  <div>
                    <h3 className="font-display text-white">{phase.name}</h3>
                    <p className="text-xs text-white/50">{phase.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-white/40">
                    {phase.steps.filter(s => s.status === 'done').length}/{phase.steps.length} steps
                  </span>
                  {expandedPhases.has(phase.id) ? (
                    <ChevronDown className="w-5 h-5 text-white/40" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-white/40" />
                  )}
                </div>
              </div>

              {expandedPhases.has(phase.id) && (
                <div className="border-t border-white/10">
                  {phase.steps.map((step) => (
                    <div key={step.id} className="p-4 border-b border-white/5 last:border-0">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${
                            step.type === 'recon' ? 'bg-primary/10 text-primary' :
                            step.type === 'exploit' ? 'bg-red-500/10 text-red-400' :
                            step.type === 'manual_review' ? 'bg-warning/10 text-warning' :
                            'bg-tertiary/10 text-tertiary'
                          }`}>
                            {getStepIcon(step)}
                          </div>
                          <div>
                            <div className="text-white font-mono">{step.name}</div>
                            <div className="flex items-center gap-2 text-xs">
                              {step.tool && (
                                <span className={`px-2 py-0.5 rounded ${
                                  step.tool_available 
                                    ? 'bg-tertiary/20 text-tertiary' 
                                    : 'bg-warning/20 text-warning'
                                }`}>
                                  {step.tool} {step.tool_available ? '' : '(Not Installed)'}
                                </span>
                              )}
                              {step.auto ? (
                                <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400">Auto</span>
                              ) : (
                                <span className="px-2 py-0.5 rounded bg-warning/20 text-warning">Manual</span>
                              )}
                              <span className={`px-2 py-0.5 rounded border ${getRiskColor(step.risk_level)}`}>
                                {step.risk_level}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {step.requires_approval && (
                            <Lock className="w-4 h-4 text-yellow-400" aria-label="Requires Approval" />
                          )}
                          {step.blockers.length > 0 && (
                            <AlertTriangle className="w-4 h-4 text-orange-400" aria-label={step.blockers.join(', ')} />
                          )}
                          <CyberButton
                            size="sm"
                            variant="action"
                            onClick={(e) => {
                              e?.stopPropagation();
                              const targetUrl = currentTarget.domains[0] || currentTarget.ips[0] || 'TARGET';
                              executeStep(step, targetUrl);
                            }}
                            disabled={executingStep === step.id || !step.tool_available}
                          >
                            {executingStep === step.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Play className="w-4 h-4" />
                            )}
                          </CyberButton>
                        </div>
                      </div>

                      {step.command && (
                        <div className="mb-2 p-2 bg-black/30 rounded font-mono text-xs text-white/60">
                          <span className="text-white/40">$</span> {step.command}
                        </div>
                      )}

                      {logs[step.id] && logs[step.id].length > 0 && (
                        <div className="mt-2 p-2 bg-black/50 rounded font-mono text-xs text-green-400 max-h-24 overflow-y-auto">
                          {logs[step.id].map((log, i) => (
                            <div key={i}>{log}</div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </GlassCard>
          ))}
        </div>

        <div className="space-y-4">
          <GlassCard className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display text-white flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Program Rules
              </h3>
              <button
                onClick={() => setRulesExpanded(!rulesExpanded)}
                className="text-white/40 hover:text-white"
              >
                {rulesExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </button>
            </div>
            {rulesExpanded && (
              <div className="space-y-2">
                {workflow.rules.map((rule, i) => (
                  <div key={i} className="flex items-start gap-2 p-2 bg-surface-50/30 rounded text-sm">
                    <CheckCircle className="w-4 h-4 text-tertiary mt-0.5 flex-shrink-0" />
                    <span className="text-white/70">{rule}</span>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>

          <GlassCard className="p-4">
            <h3 className="font-display text-white flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-yellow-400" />
              Approval Checkpoints
            </h3>
            <div className="space-y-2">
              {workflow.approval_points.map((point, i) => (
                <div key={i} className="p-3 bg-warning/5 border border-warning/20 rounded-lg">
                  <div className="font-mono text-sm text-warning">{point.step}</div>
                  <div className="text-xs text-white/50 mt-1">{point.target}</div>
                  <div className="text-xs text-white/40 mt-1">{point.reason}</div>
                </div>
              ))}
              {workflow.approval_points.length === 0 && (
                <div className="text-sm text-white/40 text-center py-4">
                  No approval checkpoints required
                </div>
              )}
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <h3 className="font-display text-white flex items-center gap-2 mb-4">
              <XCircle className="w-5 h-5 text-red-400" />
              Out of Scope
            </h3>
            <div className="space-y-1">
              {workflow.out_of_scope.map((item, i) => (
                <div key={i} className="text-sm text-white/50 line-through px-2 py-1 bg-error/5 rounded">
                  {item}
                </div>
              ))}
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <h3 className="font-display text-white flex items-center gap-2 mb-2">
              <Clock className="w-5 h-5 text-blue-400" />
              Estimated Duration
            </h3>
            <div className="text-2xl font-mono text-white">
              {currentTarget?.estimated_duration?.total || 'N/A'}
            </div>
            <div className="text-xs text-white/50 mt-1">
              ~{(currentTarget?.estimated_duration?.hours || 0).toFixed(1)} hours
            </div>
          </GlassCard>
        </div>
      </div>

      {showApprovalModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <GlassCard className="p-6 max-w-lg w-full mx-4">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-warning/10 rounded-lg">
                <Lock className="w-6 h-6 text-warning" />
              </div>
              <div>
                <h3 className="font-display text-lg text-warning">Approval Required</h3>
                <p className="text-xs text-white/50">Human review needed before execution</p>
              </div>
            </div>
            
            <div className="mb-4 p-3 bg-surface-50/30 rounded">
              <div className="text-white font-mono">{showApprovalModal.name}</div>
              <div className="text-sm text-white/50 mt-1">{showApprovalModal.approval_reason}</div>
            </div>

            <div className="flex gap-3">
              <CyberButton
                variant="ghost"
                onClick={() => setShowApprovalModal(null)}
                className="flex-1"
              >
                Cancel
              </CyberButton>
              <CyberButton
                variant="action"
                onClick={() => requestApproval(showApprovalModal, currentTarget?.domains[0] || 'TARGET')}
                className="flex-1"
              >
                Request Approval
              </CyberButton>
            </div>
          </GlassCard>
        </div>
      )}

      {showExecutionModal && workflow && (
        <WorkflowExecutionModal
          programId={programId}
          workflow={workflow}
          onClose={() => setShowExecutionModal(false)}
          onUpdate={(updated) => setWorkflow(updated)}
        />
      )}
    </div>
  );
}
