import { useState, useEffect, useRef, useCallback } from 'react';
import ManualTestingChecklist from './ManualTestingChecklist';
import {
  X,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Terminal,
  ChevronRight,
  ChevronDown,
  Loader2,
  Brain,
  Zap,
  Eye,
  Copy,
  Download,
  RefreshCw,
  BarChart3,
  Lightbulb,
  Target,
  ClipboardList,
} from 'lucide-react';
import { CyberButton } from '@/components/ui';
import { flowsApi } from '@/services/api';
import toast from 'react-hot-toast';
import ManualTestingChecklist from './ManualTestingChecklist';
import ApprovalModal from './ApprovalModal';
import ApprovalModal from './ApprovalModal';

interface TestResult {
  id: string;
  hypothesis_id: string;
  timestamp: string;
  payload_used: string;
  response_status: number;
  response_body: string;
  success: boolean;
  notes: string;
  screenshot?: string; // base64 or URL
}

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

interface TargetWorkflow {
  target_id: string;
  target_name: string;
  target_type: string;
  domains: string[];
  phases: WorkflowPhase[];
  risk_score: { score: number; level: string };
}

interface StepResult {
  step_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  output: string;
  error?: string;
  start_time?: string;
  end_time?: string;
  duration?: number;
  findings?: any[];
}

interface AIInsight {
  type: 'finding' | 'suggestion' | 'warning' | 'next_step';
  title: string;
  content: string;
  confidence: number;
}

interface WorkflowExecutionModalProps {
  programId: string;
  workflow: any;
  onClose: () => void;
  onUpdate?: (updatedWorkflow: any) => void;
}

export default function WorkflowExecutionModal({
  programId,
  workflow,
  onClose,
}: WorkflowExecutionModalProps) {
  const [activeTarget, setActiveTarget] = useState(0);
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set());
  const [stepResults, setStepResults] = useState<Record<string, StepResult>>({});
  const [executingStep, setExecutingStep] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState<string | null>(null);
  const [terminalOutput, setTerminalOutput] = useState<string[]>([]);
  const [aiInsights, setAiInsights] = useState<AIInsight[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed' | 'failed'>('all');
  const [currentTarget, setCurrentTarget] = useState<TargetWorkflow | null>(null);
  const [showManualTesting, setShowManualTesting] = useState(false);
  const [manualTestingHypotheses, setManualTestingHypotheses] = useState<Hypothesis[]>([]);
  const [manualTestingTargetId, setManualTestingTargetId] = useState<string>('');
  
  const terminalRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (workflow?.phases?.[activeTarget]) {
      setCurrentTarget(workflow.phases[activeTarget]);
      const initialExpanded = new Set<string>();
      workflow.phases[activeTarget].phases.forEach((p: WorkflowPhase) => {
        initialExpanded.add(p.id);
      });
      setExpandedPhases(initialExpanded);
    }
  }, [workflow, activeTarget]);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [terminalOutput]);

  const addTerminalOutput = useCallback((text: string, _type: 'info' | 'success' | 'error' | 'command' | 'output' = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setTerminalOutput(prev => [...prev, `[${timestamp}] ${text}`]);
  }, []);

  const executeStep = async (step: WorkflowStep) => {
    if (executingStep) {
      toast.error('Another step is already running');
      return;
    }

    if (step.requires_approval && step.status !== 'approved') {
      toast.error('This step requires approval first');
      return;
    }

    setExecutingStep(step.id);
    setActiveStep(step.id);
    const startTime = new Date();
    
    addTerminalOutput('');
    addTerminalOutput(`╔══════════════════════════════════════════════════════╗`, 'command');
    addTerminalOutput(`║ EXECUTING: ${step.name.padEnd(47)}║`, 'command');
    addTerminalOutput(`╚══════════════════════════════════════════════════════╝`, 'command');
    
    if (step.command) {
      addTerminalOutput(`Command: ${step.command}`, 'command');
    }
    addTerminalOutput(`Target: ${currentTarget?.target_name || 'Unknown'}`, 'info');
    addTerminalOutput(`Tool: ${step.tool || 'N/A'}`, 'info');
    addTerminalOutput(`Started: ${startTime.toLocaleTimeString()}`, 'info');
    addTerminalOutput('', 'info');

    const result: StepResult = {
      step_id: step.id,
      status: 'running',
      output: '',
      start_time: startTime.toISOString(),
    };

    setStepResults(prev => ({ ...prev, [step.id]: { ...result } }));

    try {
      const targetDomain = currentTarget?.domains[0] || currentTarget?.target_name || 'TARGET';
      
      const response = await flowsApi.executeStep({
        step_id: step.id,
        workflow_data: workflow,
        target: targetDomain,
        params: {},
      });

      const endTime = new Date();
      const duration = (endTime.getTime() - startTime.getTime()) / 1000;

      if (response.data.status === 'completed') {
        const outputData = response.data.result?.output || {};
        const stdout = response.data.result?.stdout || '';
        
        let outputText = '';
        
        if (stdout) {
          try {
            const parsed = JSON.parse(stdout);
            outputText = JSON.stringify(parsed, null, 2);
          } catch {
            outputText = stdout;
          }
        } else if (typeof outputData === 'object' && Object.keys(outputData).length > 0) {
          outputText = JSON.stringify(outputData, null, 2);
        } else {
          outputText = 'Execution completed successfully (no output data)';
        }
        
        result.status = 'completed';
        result.output = outputText;
        result.end_time = endTime.toISOString();
        result.duration = duration;
        
        addTerminalOutput('┌─ RESULTS ──────────────────────────────────────────────', 'success');
        addTerminalOutput('│ ✓ Status: SUCCESS', 'success');
        addTerminalOutput(`│ ⏱ Duration: ${duration.toFixed(2)} seconds`, 'success');
        
        if (stdout || (typeof outputData === 'object' && Object.keys(outputData).length > 0)) {
          addTerminalOutput('│', 'info');
          addTerminalOutput('├─ Output Data:', 'info');
          outputText.split('\n').forEach(line => {
            addTerminalOutput(`│   ${line}`, 'output');
          });
        }
        
        addTerminalOutput('└─────────────────────────────────────────────────────────', 'success');
        
        toast.success(`${step.name} completed`);
      } else if (response.data.status === 'manual_required') {
        result.status = 'pending';
        result.output = response.data.message || 'Manual execution required';
        addTerminalOutput('┌─ MANUAL ACTION REQUIRED ────────────────────────────────', 'info');
        addTerminalOutput('│', 'info');
        addTerminalOutput(`│ ${response.data.message || 'This step requires manual execution'}`, 'info');
        addTerminalOutput('│', 'info');
        addTerminalOutput('│ Please run this step manually and mark it as complete.', 'info');
        addTerminalOutput('└─────────────────────────────────────────────────────────', 'info');
        toast('Manual execution required for this step', { icon: 'ℹ️' });
      } else if (response.data.status === 'tool_not_available') {
        result.status = 'failed';
        result.error = `Tool '${step.tool}' is not installed`;
        result.end_time = endTime.toISOString();
        result.duration = duration;
        addTerminalOutput('┌─ ERROR ────────────────────────────────────────────────', 'error');
        addTerminalOutput('│ ✗ Status: TOOL NOT AVAILABLE', 'error');
        addTerminalOutput(`│ ✗ Tool: ${step.tool}`, 'error');
        addTerminalOutput('│', 'error');
        addTerminalOutput('│ Install the tool or mark this step as manually completed.', 'error');
        addTerminalOutput('└─────────────────────────────────────────────────────────', 'error');
        toast.error('Tool not installed');
      } else {
        result.status = 'failed';
        result.error = response.data.error || 'Unknown error';
        result.end_time = endTime.toISOString();
        result.duration = duration;
        addTerminalOutput('┌─ ERROR ────────────────────────────────────────────────', 'error');
        addTerminalOutput('│ ✗ Status: FAILED', 'error');
        addTerminalOutput(`│ ✗ Error: ${result.error}`, 'error');
        addTerminalOutput('└─────────────────────────────────────────────────────────', 'error');
        toast.error('Step execution failed');
      }
    } catch (err: any) {
      const endTime = new Date();
      const duration = (endTime.getTime() - startTime.getTime()) / 1000;
      result.status = 'failed';
      result.error = err.message || 'Execution failed';
      result.end_time = endTime.toISOString();
      result.duration = duration;
      addTerminalOutput('┌─ ERROR ────────────────────────────────────────────────', 'error');
      addTerminalOutput('│ ✗ Status: EXCEPTION', 'error');
      addTerminalOutput(`│ ✗ Error: ${err.message}`, 'error');
      addTerminalOutput('└─────────────────────────────────────────────────────────', 'error');
      toast.error('Failed to execute step: ' + err.message);
    }

    setStepResults(prev => ({ ...prev, [step.id]: { ...result } }));
    setExecutingStep(null);
    
    analyzeResults();
  };

  const runAutoSteps = async () => {
    if (!currentTarget) return;
    
    addTerminalOutput('');
    addTerminalOutput('╔══════════════════════════════════════════════════════════════╗', 'command');
    addTerminalOutput('║              AUTO-EXECUTION MODE STARTED                 ║', 'command');
    addTerminalOutput('╚══════════════════════════════════════════════════════════════╝', 'command');
    addTerminalOutput('');
    
    let executed = 0;
    for (const phase of currentTarget.phases) {
      for (const step of phase.steps) {
        const existingResult = stepResults[step.id];
        if (step.auto && step.tool_available && (!existingResult || existingResult.status !== 'completed')) {
          executed++;
          addTerminalOutput(`[AUTO ${executed}] Running: ${step.name}`, 'command');
          await executeStep(step);
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      }
    }
    
    addTerminalOutput('');
    addTerminalOutput('╔══════════════════════════════════════════════════════════════╗', 'command');
    addTerminalOutput('║              AUTO-EXECUTION MODE COMPLETED               ║', 'command');
    addTerminalOutput('╚══════════════════════════════════════════════════════════════╝', 'command');
    addTerminalOutput(`Executed ${executed} step(s)`, 'success');
    addTerminalOutput('');
  };

  const markAsManual = (step: WorkflowStep) => {
    const result: StepResult = {
      step_id: step.id,
      status: 'completed',
      output: `Manually completed by user on ${new Date().toLocaleString()}\nStep: ${step.name}\nTool: ${step.tool || 'N/A'}\nCommand: ${step.command || 'N/A'}`,
      end_time: new Date().toISOString(),
    };
    setStepResults(prev => ({ ...prev, [step.id]: result }));
    addTerminalOutput('');
    addTerminalOutput('┌─ MANUAL COMPLETION ──────────────────────────────────────', 'info');
    addTerminalOutput('│ ✓ Step marked as manually completed', 'success');
    addTerminalOutput(`│ Step: ${step.name}`, 'info');
    addTerminalOutput(`│ Completed: ${new Date().toLocaleString()}`, 'info');
    addTerminalOutput('└─────────────────────────────────────────────────────────', 'info');
    toast.success('Step marked as completed');
    analyzeResults();
  };

  const analyzeResults = useCallback(() => {
    setIsAnalyzing(true);
    
    const results = stepResults;
    const insights: AIInsight[] = [];
    
    const completedSteps = Object.values(results).filter(r => r.status === 'completed');
    const failedSteps = Object.values(results).filter(r => r.status === 'failed');
    const runningSteps = Object.values(results).filter(r => r.status === 'running');

    const totalSteps = currentTarget?.phases.reduce((acc, p) => acc + p.steps.length, 0) || 1;
    const completedCount = completedSteps.length;
    const percentage = totalSteps > 0 ? Math.round((completedCount / totalSteps) * 100) : 0;

    if (completedCount > 0 || failedSteps.length > 0) {
      insights.push({
        type: 'finding',
        title: 'Progress Report',
        content: `${completedCount}/${totalSteps} steps completed (${percentage}%). ${failedSteps.length > 0 ? `${failedSteps.length} failed.` : ''} ${runningSteps.length > 0 ? `${runningSteps.length} running.` : ''}`,
        confidence: 0.95,
      });
    }

    if (failedSteps.length > 0) {
      insights.push({
        type: 'warning',
        title: 'Failed Steps',
        content: `${failedSteps.length} step(s) failed. Tools may not be installed or commands may have errors.`,
        confidence: 0.8,
      });
    }

    if (percentage >= 100) {
      insights.push({
        type: 'suggestion',
        title: 'Workflow Complete!',
        content: 'All steps completed. Review findings and generate report.',
        confidence: 0.95,
      });
    } else if (percentage >= 50) {
      insights.push({
        type: 'suggestion',
        title: 'Halfway There!',
        content: `${percentage}% complete. ${totalSteps - completedCount} steps remaining.`,
        confidence: 0.9,
      });
    } else if (percentage > 0) {
      insights.push({
        type: 'next_step',
        title: 'Continue Testing',
        content: `${percentage}% complete. Run auto-steps or execute remaining steps manually.`,
        confidence: 0.85,
      });
    }

    setAiInsights(insights);
    setIsAnalyzing(false);
  }, [stepResults, currentTarget]);

  const togglePhase = (phaseId: string) => {
    setExpandedPhases(prev => {
      const next = new Set(prev);
      if (next.has(phaseId)) {
        next.delete(phaseId);
      } else {
        next.add(phaseId);
      }
      return next;
    });
  };

  const getStepStatus = (step: WorkflowStep) => {
    if (stepResults[step.id]) {
      return stepResults[step.id].status;
    }
    return 'pending';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'failed': return <XCircle className="w-4 h-4 text-red-400" />;
      case 'running': return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
      case 'skipped': return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getTerminalColor = (type: string) => {
    switch (type) {
      case 'success': return 'text-green-400';
      case 'error': return 'text-red-400';
      case 'command': return 'text-yellow-400';
      case 'output': return 'text-cyan-300';
      default: return 'text-gray-300';
    }
  };

  const getFilteredSteps = (steps: WorkflowStep[]) => {
    if (filter === 'all') return steps;
    return steps.filter(step => {
      const status = getStepStatus(step);
      if (filter === 'pending') return status === 'pending' || !status;
      return status === filter;
    });
  };

  const getProgress = useCallback(() => {
    if (!currentTarget) return { total: 0, completed: 0, failed: 0, pending: 0, percentage: 0 };
    const total = currentTarget.phases.reduce((acc, p) => acc + p.steps.length, 0);
    const results = Object.values(stepResults);
    const completed = results.filter(r => r.status === 'completed').length;
    const failed = results.filter(r => r.status === 'failed').length;
    const pending = results.filter(r => r.status === 'pending' || r.status === 'running').length;
    return { 
      total, 
      completed, 
      failed, 
      pending,
      percentage: total > 0 ? Math.round((completed / total) * 100) : 0 
    };
  }, [stepResults, currentTarget]);

  const copyTerminalOutput = () => {
    navigator.clipboard.writeText(terminalOutput.join('\n'));
    toast.success('Output copied to clipboard');
  };

  const downloadResults = () => {
    const results = {
      program_id: programId,
      target: currentTarget?.target_name,
      executed_at: new Date().toISOString(),
      results: stepResults,
      summary: getProgress(),
    };
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `workflow-results-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Results downloaded');
  };

    const progress = getProgress();

    // Manual Testing Checklist functions
    const openManualTestingChecklist = () => {
      if (!currentTarget) return;
      
      // In a real implementation, we would fetch hypotheses from the hypothesis generation service
      // For now, we'll create some mock hypotheses based on the current step results
      const mockHypotheses: Hypothesis[] = [
        {
          id: 'hyp_1',
          description: 'Test for IDOR by modifying user ID parameter',
          type: 'IDOR',
          endpoint: '/api/user/{id}',
          method: 'GET',
          payload: '123',
          expected_behavior: 'Access to another user\\'s data'
        },
        {
          id: 'hyp_2',
          description: 'Test for XSS in search parameter',
          type: 'XSS',
          endpoint: '/api/search',
          method: 'GET',
          payload: '<script>alert(document.domain)</script>',
          expected_behavior: 'Script executes in victim\\'s browser'
        },
        {
          id: 'hyp_3',
          description: 'Test for missing CSRF protection on profile update',
          type: 'CSRF',
          endpoint: '/api/profile/update',
          method: 'POST',
          payload: '',
          expected_behavior: 'Profile update succeeds without CSRF token'
        }
      ];
      
      setManualTestingHypotheses(mockHypotheses);
      setManualTestingTargetId(currentTarget?.target_id || '');
      setShowManualTesting(true);
    };

    const handleHypothesisTested = (hypothesisId: string, result: TestResult) => {
      // In a real implementation, we would save this result and potentially generate new hypotheses
      // For now, we'll just log it
      console.log('Hypothesis tested:', { hypothesisId, result });
      
      // Close the manual testing modal and show a toast
      setShowManualTesting(false);
      toast.success('Hypothesis test completed', {
        description: result.success ? 'Potential vulnerability detected!' : 'No vulnerability found with this test.'
      });
    };

    const closeManualTesting = () => {
      setShowManualTesting(false);
      setManualTestingHypotheses([]);
      setManualTestingTargetId('');
    };

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-cyber-primary/20 to-cyber-secondary/10 border-b border-cyber-primary/30">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-display text-white">WORKFLOW EXECUTION</h2>
          <div className="flex gap-2">
            {workflow?.phases?.map((t: any, idx: number) => (
              <button
                key={t.target_id}
                onClick={() => setActiveTarget(idx)}
                className={`px-3 py-1 text-xs rounded ${
                  idx === activeTarget 
                    ? 'bg-cyber-primary text-white' 
                    : 'bg-cyber-dark/50 text-white/50 hover:text-white'
                }`}
              >
                {t.target_name}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button onClick={onClose} className="text-white/50 hover:text-white">
            <X className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Workflow Steps */}
        <div className="w-1/3 border-r border-cyber-primary/30 flex flex-col">
          {/* Progress Bar */}
          <div className="p-4 border-b border-cyber-primary/30 bg-cyber-dark/30">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-white/70">Progress</span>
              <span className="text-sm text-white font-mono">
                {progress.completed}/{progress.total}
              </span>
            </div>
            <div className="h-2 bg-black/50 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-cyber-primary to-cyber-secondary transition-all duration-300"
                style={{ width: `${progress.percentage}%` }}
              />
            </div>
            <div className="flex gap-4 mt-2 text-xs">
              <span className="text-green-400">{progress.completed} completed</span>
              <span className="text-red-400">{progress.failed} failed</span>
              <span className="text-gray-400">{progress.total - progress.completed - progress.failed} pending</span>
            </div>
          </div>

          {/* Filter */}
          <div className="p-3 border-b border-cyber-primary/30 flex gap-2">
            {(['all', 'pending', 'completed', 'failed'] as const).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-2 py-1 text-xs rounded ${
                  filter === f ? 'bg-cyber-primary/50 text-white' : 'bg-black/30 text-white/50'
                }`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
            <div className="flex-1" />
            <button onClick={runAutoSteps} className="px-2 py-1 text-xs bg-green-600/30 text-green-400 rounded hover:bg-green-600/50">
              <Zap className="w-3 h-3 inline mr-1" />
              Run Auto
            </button>
          </div>

          {/* Steps List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2" ref={scrollRef}>
            {currentTarget?.phases.map(phase => (
              <div key={phase.id} className="border border-cyber-primary/20 rounded-lg overflow-hidden">
                <button
                  onClick={() => togglePhase(phase.id)}
                  className="w-full flex items-center justify-between p-3 bg-cyber-dark/40 hover:bg-cyber-dark/60 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {expandedPhases.has(phase.id) ? (
                      <ChevronDown className="w-4 h-4 text-white/50" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-white/50" />
                    )}
                    <span className="text-sm font-medium text-white">{phase.name}</span>
                  </div>
                  <span className="text-xs text-white/50">
                    {phase.steps.filter(s => getStepStatus(s) === 'completed').length}/{phase.steps.length}
                  </span>
                </button>

                {expandedPhases.has(phase.id) && (
                  <div className="p-2 space-y-1">
                    {getFilteredSteps(phase.steps).map(step => {
                      const status = getStepStatus(step);
                      const result = stepResults[step.id];
                      
                      return (
                        <div
                          key={step.id}
                          onClick={() => setActiveStep(step.id)}
                          className={`p-3 rounded cursor-pointer transition-all ${
                            activeStep === step.id
                              ? 'bg-cyber-primary/20 border border-cyber-primary/50'
                              : 'bg-black/30 hover:bg-black/50 border border-transparent'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2">
                              {getStatusIcon(status)}
                              <span className="text-sm text-white">{step.name}</span>
                            </div>
                            {executingStep === step.id && (
                              <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                            )}
                          </div>
                          
                          <div className="flex items-center gap-2 text-xs text-white/50 mb-2">
                            {step.tool && (
                              <span className={step.tool_available ? 'text-green-400' : 'text-red-400'}>
                                {step.tool}
                              </span>
                            )}
                            {step.auto ? (
                              <span className="px-1.5 py-0.5 bg-blue-500/20 text-blue-400 rounded">Auto</span>
                            ) : (
                              <span className="px-1.5 py-0.5 bg-yellow-500/20 text-yellow-400 rounded">Manual</span>
                            )}
                            <span className={`px-1.5 py-0.5 rounded ${
                              step.risk_level === 'low' ? 'bg-green-500/20 text-green-400' :
                              step.risk_level === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                              'bg-red-500/20 text-red-400'
                            }`}>
                              {step.risk_level}
                            </span>
                          </div>

                          {step.command && (
                            <div className="font-mono text-xs text-white/40 bg-black/50 p-2 rounded truncate">
                              $ {step.command}
                            </div>
                          )}

                          {result?.duration && (
                            <div className="text-xs text-white/40 mt-1">
                              Duration: {result.duration.toFixed(2)}s
                            </div>
                          )}

                          {status === 'completed' || status === 'failed' ? (
                            <div className="mt-2 flex gap-2">
                              <CyberButton
                                size="sm"
                                variant="action"
                                onClick={(e) => {
                                  e?.stopPropagation();
                                  executeStep(step);
                                }}
                                disabled={executingStep === step.id}
                              >
                                <RefreshCw className="w-3 h-3" />
                              </CyberButton>
                              {!step.auto && status !== 'completed' && (
                                <CyberButton
                                  size="sm"
                                  variant="ghost"
                                  onClick={(e) => {
                                    e?.stopPropagation();
                                    markAsManual(step);
                                  }}
                                >
                                  Mark Manual
                                </CyberButton>
                              )}
                            </div>
                          ) : (
                            <div className="mt-2">
                              <CyberButton
                                size="sm"
                                variant="action"
                                onClick={(e) => {
                                  e?.stopPropagation();
                                  executeStep(step);
                                }}
                                disabled={executingStep === step.id || !step.tool_available}
                              >
                                <Play className="w-3 h-3" />
                                Run
                              </CyberButton>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Right Side - Terminal & AI */}
        <div className="flex-1 flex flex-col">
          {/* Terminal */}
          <div className="flex-1 flex flex-col">
              <div className="flex items-center justify-between px-4 py-2 bg-cyber-dark/40 border-b border-cyber-primary/30">
                <div className="flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-cyber-primary" />
                  <span className="text-sm text-white/70">Terminal Output</span>
                </div>
                <div className="flex gap-2">
                  <button onClick={copyTerminalOutput} className="p-1 text-white/50 hover:text-white">
                    <Copy className="w-4 h-4" />
                  </button>
                  <button onClick={downloadResults} className="p-1 text-white/50 hover:text-white">
                    <Download className="w-4 h-4" />
                  </button>
                  <button onClick={openManualTestingChecklist} className="p-1 text-white/50 hover:text-white">
                    <ClipboardList className="w-4 h-4" />
                  </button>
                </div>
              </div>
            <div 
              ref={terminalRef}
              className="flex-1 bg-black/90 p-4 font-mono text-sm overflow-y-auto"
            >
              {terminalOutput.length === 0 ? (
                <div className="text-white/30">
                  <p>No output yet. Click on a step and run it to see results.</p>
                  <p className="mt-2">Use "Run Auto" to execute all auto-steps automatically.</p>
                </div>
              ) : (
                terminalOutput.map((line, i) => (
                  <div key={i} className={`${getTerminalColor(
                    line.includes('[SUCCESS]') ? 'success' :
                    line.includes('[ERROR]') ? 'error' :
                    line.includes('$') ? 'command' :
                    'info'
                  )} whitespace-pre-wrap break-all`}>
                    {line}
                  </div>
                ))
              )}
            </div>
          </div>

            {/* AI Analysis Panel */}
            <div className="h-64 border-t border-cyber-primary/30 flex flex-col">
              <div className="flex items-center gap-2 px-4 py-2 bg-cyber-dark/40 border-b border-cyber-primary/30">
                <Brain className="w-4 h-4 text-purple-400" />
                <span className="text-sm text-white/70">AI Analysis</span>
                {isAnalyzing && <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />}
                <div className="flex-1" />
                <button 
                  onClick={analyzeResults}
                  className="px-2 py-1 text-xs bg-purple-600/30 text-purple-400 rounded hover:bg-purple-600/50"
                >
                  <RefreshCw className="w-3 h-3 inline mr-1" />
                  Refresh
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {aiInsights.length === 0 ? (
                  <div className="text-white/30 text-sm flex items-center gap-2">
                    <Lightbulb className="w-4 h-4" />
                    <span>Execute some steps to get AI-powered insights and suggestions.</span>
                  </div>
                ) : (
                  aiInsights.map((insight, i) => (
                    <div 
                      key={i}
                      className={`p-3 rounded-lg border ${
                        insight.type === 'finding' ? 'bg-blue-500/10 border-blue-500/30' :
                        insight.type === 'warning' ? 'bg-yellow-500/10 border-yellow-500/30' :
                        insight.type === 'suggestion' ? 'bg-green-500/10 border-green-500/30' :
                        'bg-purple-500/10 border-purple-500/30'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        {insight.type === 'finding' && <Eye className="w-4 h-4 text-blue-400" />}
                        {insight.type === 'warning' && <AlertTriangle className="w-4 h-4 text-yellow-400" />}
                        {insight.type === 'suggestion' && <Lightbulb className="w-4 h-4 text-green-400" />}
                        {insight.type === 'next_step' && <Target className="w-4 h-4 text-purple-400" />}
                        <span className="text-sm font-medium text-white">{insight.title}</span>
                      </div>
                      <p className="text-xs text-white/70">{insight.content}</p>
                      <div className="mt-1 text-xs text-white/40">
                        Confidence: {(insight.confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
            
            {/* Manual Testing Panel */}
            <div className="h-64 border-t border-cyber-primary/30 flex flex-col">
              <div className="flex items-center gap-2 px-4 py-2 bg-cyber-dark/40 border-b border-cyber-primary/30">
                <ClipboardList className="w-4 h-4 text-blue-400" />
                <span className="text-sm text-white/70">Manual Testing</span>
                <div className="flex-1" />
                <button 
                  onClick={closeManualTesting}
                  variant="outline"
                  colorScheme="gray"
                  size="sm"
                >
                  Close
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-4">
                <ManualTestingChecklist
                  targetId={manualTestingTargetId}
                  hypotheses={manualTestingHypotheses}
                  onHypothesisTested={handleHypothesisTested}
                />
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {aiInsights.length === 0 ? (
                <div className="text-white/30 text-sm flex items-center gap-2">
                  <Lightbulb className="w-4 h-4" />
                  <span>Execute some steps to get AI-powered insights and suggestions.</span>
                </div>
              ) : (
                aiInsights.map((insight, i) => (
                  <div 
                    key={i}
                    className={`p-3 rounded-lg border ${
                      insight.type === 'finding' ? 'bg-blue-500/10 border-blue-500/30' :
                      insight.type === 'warning' ? 'bg-yellow-500/10 border-yellow-500/30' :
                      insight.type === 'suggestion' ? 'bg-green-500/10 border-green-500/30' :
                      'bg-purple-500/10 border-purple-500/30'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      {insight.type === 'finding' && <Eye className="w-4 h-4 text-blue-400" />}
                      {insight.type === 'warning' && <AlertTriangle className="w-4 h-4 text-yellow-400" />}
                      {insight.type === 'suggestion' && <Lightbulb className="w-4 h-4 text-green-400" />}
                      {insight.type === 'next_step' && <Target className="w-4 h-4 text-purple-400" />}
                      <span className="text-sm font-medium text-white">{insight.title}</span>
                    </div>
                    <p className="text-xs text-white/70">{insight.content}</p>
                    <div className="mt-1 text-xs text-white/40">
                      Confidence: {(insight.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                ))
              )}

              {/* Results Summary */}
              {Object.keys(stepResults).length > 0 && (
                <div className="mt-4 p-3 bg-cyber-dark/50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <BarChart3 className="w-4 h-4 text-white/50" />
                    <span className="text-sm text-white/70">Results Summary</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-black/30 p-2 rounded">
                      <div className="text-white/50">Total Steps Run</div>
                      <div className="text-white font-mono">{Object.keys(stepResults).length}</div>
                    </div>
                    <div className="bg-black/30 p-2 rounded">
                      <div className="text-green-400">Successful</div>
                      <div className="text-green-400 font-mono">
                        {Object.values(stepResults).filter(r => r.status === 'completed').length}
                      </div>
                    </div>
                    <div className="bg-black/30 p-2 rounded">
                      <div className="text-red-400">Failed</div>
                      <div className="text-red-400 font-mono">
                        {Object.values(stepResults).filter(r => r.status === 'failed').length}
                      </div>
                    </div>
                    <div className="bg-black/30 p-2 rounded">
                      <div className="text-white/50">Total Output</div>
                      <div className="text-white font-mono">
                        {Object.values(stepResults).reduce((acc, r) => acc + (r.output?.length || 0), 0)} chars
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
