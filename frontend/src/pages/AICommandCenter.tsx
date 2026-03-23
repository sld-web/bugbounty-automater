import { useState, useEffect, useRef } from 'react';
import {
  Brain,
  GitBranch,
  Zap,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Play,
  Square,
  MessageSquare,
  Network,
  Target,
  Lock,
  Sparkles,
} from 'lucide-react';
import { GlassCard, CyberButton, StatusIndicator } from '@/components/ui';
import { programsApi } from '@/services/api';
import toast from 'react-hot-toast';

interface AIReasoning {
  id: string;
  timestamp: Date;
  type: 'thought' | 'action' | 'finding' | 'chain' | 'approval';
  content: string;
  details?: any;
  status: 'pending' | 'active' | 'completed' | 'failed';
}

interface AttackChain {
  id: string;
  steps: { node: string; vulnerability: string; action: string }[];
  impact: string;
  status: 'potential' | 'attempting' | 'completed' | 'failed';
}

interface KnowledgeNode {
  id: string;
  type: string;
  properties: any;
  risk_level: string;
  tested: boolean;
  findings: any[];
}

export default function AICommandCenter({ programId }: { programId: string }) {
  const [isRunning, setIsRunning] = useState(false);
  const [reasoningLog, setReasoningLog] = useState<AIReasoning[]>([]);
  const [attackChains, setAttackChains] = useState<AttackChain[]>([]);
  const [knowledgeGraph] = useState<{ nodes: KnowledgeNode[]; stats: any } | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['reasoning', 'chains', 'graph']));
  const [pendingApprovals, setPendingApprovals] = useState<AIReasoning[]>([]);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [reasoningLog]);

  const addReasoning = (type: AIReasoning['type'], content: string, details?: any) => {
    const reasoning: AIReasoning = {
      id: `r_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      type,
      content,
      details,
      status: 'completed',
    };
    setReasoningLog(prev => [...prev, reasoning]);
    
    if (type === 'approval') {
      setPendingApprovals(prev => [...prev, reasoning]);
    }
  };

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const startAIAnalysis = async () => {
    if (isRunning) return;
    
    setIsRunning(true);
    setReasoningLog([]);
    setAttackChains([]);
    
    addReasoning('thought', 'Initializing AI analysis for this program...', { phase: 'init' });
    
    try {
      addReasoning('thought', 'Fetching program configuration and scope...', { phase: 'fetch' });
      const programRes = await programsApi.get(programId);
      const program = programRes.data;
      
      addReasoning('action', `Analyzing scope: ${program.scope?.domains?.length || 0} domains`, {
        domains: program.scope?.domains,
        rules: program.special_requirements?.rules
      });

      addReasoning('thought', 'Building knowledge graph from program data...', { phase: 'graph' });
      
      const targets = program.target_configs?.length > 0 
        ? program.target_configs 
        : program.priority_areas?.map((name: string) => ({ name, type: 'webapp' })) || [];
      
      for (const target of targets) {
        addReasoning('action', `Mapping attack surface for: ${target.name}`, { target });
        
        setTimeout(() => {
          addReasoning('finding', `Discovered authentication flow on ${target.name}`, {
            type: 'auth_flow',
            method: 'OAuth 2.0'
          });
        }, 500);
        
        setTimeout(() => {
          addReasoning('chain', `Potential attack chain: IDOR → Privilege Escalation → RCE`, {
            severity: 'high',
            chain_length: 3
          });
          
          setAttackChains(prev => [...prev, {
            id: `chain_${Date.now()}`,
            steps: [
              { node: `${target.name}/api/users`, vulnerability: 'IDOR', action: 'Modify user ID parameter' },
              { node: `${target.name}/admin`, vulnerability: 'Privilege Escalation', action: 'Access admin panel' },
              { node: `${target.name}/upload`, vulnerability: 'File Upload RCE', action: 'Upload webshell' }
            ],
            impact: 'Full system compromise',
            status: 'potential'
          }]);
        }, 1000);
      }

      setTimeout(() => {
        addReasoning('approval', 'Requesting approval for SQL injection testing', {
          tool: 'sqlmap',
          target: targets[0]?.name || 'unknown',
          risk: 'high'
        });
      }, 2000);

      addReasoning('thought', 'Analysis complete. Review findings and approve next steps.', { phase: 'complete' });

    } catch (err: any) {
      addReasoning('finding', `Error during analysis: ${err.message}`, { status: 'failed' });
      toast.error('AI analysis failed');
    } finally {
      setIsRunning(false);
    }
  };

  const approveAction = async (reasoningId: string) => {
    const reasoning = pendingApprovals.find(r => r.id === reasoningId);
    if (!reasoning) return;

    addReasoning('action', `Approved: ${reasoning.content}`, reasoning.details);
    setPendingApprovals(prev => prev.filter(r => r.id !== reasoningId));
    
    setTimeout(() => {
      addReasoning('finding', `Execution started for approved action`, {
        status: 'running'
      });
    }, 500);
  };

  const denyAction = async (reasoningId: string) => {
    const reasoning = pendingApprovals.find(r => r.id === reasoningId);
    if (!reasoning) return;

    addReasoning('thought', `Action denied by user: ${reasoning.content}`, {
      status: 'denied'
    });
    setPendingApprovals(prev => prev.filter(r => r.id !== reasoningId));
    toast.success('Action denied');
  };

  const getReasoningIcon = (type: string) => {
    switch (type) {
      case 'thought': return <Brain className="w-4 h-4 text-blue-400" />;
      case 'action': return <Play className="w-4 h-4 text-green-400" />;
      case 'finding': return <Target className="w-4 h-4 text-yellow-400" />;
      case 'chain': return <GitBranch className="w-4 h-4 text-purple-400" />;
      case 'approval': return <Lock className="w-4 h-4 text-orange-400" />;
      default: return <MessageSquare className="w-4 h-4" />;
    }
  };

  const getReasoningColor = (type: string) => {
    switch (type) {
      case 'thought': return 'border-l-blue-500';
      case 'action': return 'border-l-green-500';
      case 'finding': return 'border-l-yellow-500';
      case 'chain': return 'border-l-purple-500';
      case 'approval': return 'border-l-orange-500';
      default: return 'border-l-gray-500';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-primary/20 to-tertiary/20 rounded-lg">
            <Sparkles className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h2 className="font-display text-lg text-white">AI Command Center</h2>
            <p className="text-xs text-white/50">Autonomous analysis and attack orchestration</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {isRunning ? (
            <StatusIndicator status="running" size="sm" showLabel />
          ) : (
            <CyberButton
              variant="action"
              onClick={startAIAnalysis}
            >
              <Zap className="w-4 h-4 mr-2" />
              Start AI Analysis
            </CyberButton>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <GlassCard className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <Brain className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <div className="text-2xl font-mono text-white">{reasoningLog.length}</div>
              <div className="text-xs text-white/50">AI Thoughts</div>
            </div>
          </div>
        </GlassCard>
        
        <GlassCard className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/10 rounded-lg">
              <GitBranch className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <div className="text-2xl font-mono text-purple-400">{attackChains.length}</div>
              <div className="text-xs text-white/50">Attack Chains</div>
            </div>
          </div>
        </GlassCard>
        
        <GlassCard className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-500/10 rounded-lg">
              <Lock className="w-5 h-5 text-orange-400" />
            </div>
            <div>
              <div className="text-2xl font-mono text-orange-400">{pendingApprovals.length}</div>
              <div className="text-xs text-white/50">Pending Approvals</div>
            </div>
          </div>
        </GlassCard>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="space-y-4">
          <GlassCard className="overflow-hidden">
            <div
              className="flex items-center justify-between p-4 cursor-pointer hover:bg-white/5"
              onClick={() => toggleSection('reasoning')}
            >
              <div className="flex items-center gap-3">
                <MessageSquare className="w-5 h-5 text-blue-400" />
                <h3 className="font-display text-white">AI Reasoning Log</h3>
              </div>
              {expandedSections.has('reasoning') ? (
                <ChevronDown className="w-5 h-5 text-white/40" />
              ) : (
                <ChevronRight className="w-5 h-5 text-white/40" />
              )}
            </div>
            
            {expandedSections.has('reasoning') && (
              <div
                ref={logRef}
                className="h-[400px] overflow-y-auto border-t border-white/10"
              >
                {reasoningLog.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-white/40">
                    <div className="text-center">
                      <Brain className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>AI reasoning will appear here</p>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 space-y-3">
                    {reasoningLog.map((reasoning) => (
                      <div
                        key={reasoning.id}
                        className={`p-3 bg-surface-50/30 rounded-lg border-l-4 ${getReasoningColor(reasoning.type)}`}
                      >
                        <div className="flex items-start gap-3">
                          {getReasoningIcon(reasoning.type)}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-white">{reasoning.content}</p>
                            <p className="text-xs text-white/40 mt-1">
                              {reasoning.timestamp.toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                        {reasoning.details && (
                          <div className="mt-2 p-2 bg-black/30 rounded text-xs font-mono text-white/60 overflow-x-auto">
                            {JSON.stringify(reasoning.details, null, 2)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </GlassCard>

          {pendingApprovals.length > 0 && (
            <GlassCard className="p-4 border border-orange-500/30">
              <div className="flex items-center gap-3 mb-4">
                <Lock className="w-5 h-5 text-orange-400" />
                <h3 className="font-display text-orange-400">Pending Approvals</h3>
              </div>
              <div className="space-y-3">
                {pendingApprovals.map((approval) => (
                  <div
                    key={approval.id}
                    className="p-3 bg-orange-500/10 border border-orange-500/30 rounded-lg"
                  >
                    <p className="text-sm text-white mb-2">{approval.content}</p>
                    <div className="flex gap-2">
                      <CyberButton
                        size="sm"
                        variant="action"
                        onClick={() => approveAction(approval.id)}
                      >
                        <CheckCircle className="w-4 h-4 mr-1" />
                        Approve
                      </CyberButton>
                      <CyberButton
                        size="sm"
                        variant="ghost"
                        onClick={() => denyAction(approval.id)}
                      >
                        <Square className="w-4 h-4 mr-1" />
                        Deny
                      </CyberButton>
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>
          )}
        </div>

        <div className="space-y-4">
          <GlassCard className="overflow-hidden">
            <div
              className="flex items-center justify-between p-4 cursor-pointer hover:bg-white/5"
              onClick={() => toggleSection('chains')}
            >
              <div className="flex items-center gap-3">
                <GitBranch className="w-5 h-5 text-purple-400" />
                <h3 className="font-display text-white">Attack Chains</h3>
              </div>
              {expandedSections.has('chains') ? (
                <ChevronDown className="w-5 h-5 text-white/40" />
              ) : (
                <ChevronRight className="w-5 h-5 text-white/40" />
              )}
            </div>
            
            {expandedSections.has('chains') && (
              <div className="border-t border-white/10">
                {attackChains.length === 0 ? (
                  <div className="flex items-center justify-center h-32 text-white/40">
                    <div className="text-center">
                      <GitBranch className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>No attack chains discovered yet</p>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 space-y-4">
                    {attackChains.map((chain) => (
                      <div key={chain.id} className="p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-sm font-mono text-purple-400">Chain #{chain.id.split('_')[1]}</span>
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            chain.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                            chain.status === 'attempting' ? 'bg-yellow-500/20 text-yellow-400' :
                            'bg-gray-500/20 text-gray-400'
                          }`}>
                            {chain.status}
                          </span>
                        </div>
                        
                        <div className="space-y-2">
                          {chain.steps.map((step, idx) => (
                            <div key={idx} className="flex items-center gap-2 text-sm">
                              <span className="w-6 h-6 flex items-center justify-center bg-purple-500/20 rounded-full text-xs text-purple-400">
                                {idx + 1}
                              </span>
                              <div className="flex-1">
                                <div className="text-white/70">{step.node}</div>
                                <div className="text-xs text-white/40">
                                  {step.vulnerability}: {step.action}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                        
                        <div className="mt-3 pt-3 border-t border-purple-500/30">
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-white/50">Impact:</span>
                            <span className="text-xs text-red-400">{chain.impact}</span>
                          </div>
                          <div className="mt-2 flex gap-2">
                            <CyberButton size="sm" variant="action">
                              <Play className="w-3 h-3 mr-1" />
                              Execute Chain
                            </CyberButton>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </GlassCard>

          <GlassCard className="overflow-hidden">
            <div
              className="flex items-center justify-between p-4 cursor-pointer hover:bg-white/5"
              onClick={() => toggleSection('graph')}
            >
              <div className="flex items-center gap-3">
                <Network className="w-5 h-5 text-green-400" />
                <h3 className="font-display text-white">Knowledge Graph</h3>
              </div>
              {expandedSections.has('graph') ? (
                <ChevronDown className="w-5 h-5 text-white/40" />
              ) : (
                <ChevronRight className="w-5 h-5 text-white/40" />
              )}
            </div>
            
            {expandedSections.has('graph') && (
              <div className="border-t border-white/10 p-4">
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="p-3 bg-surface-50/30 rounded text-center">
                    <div className="text-xl font-mono text-white">
                      {knowledgeGraph?.stats?.total_nodes || 0}
                    </div>
                    <div className="text-xs text-white/50">Nodes</div>
                  </div>
                  <div className="p-3 bg-surface-50/30 rounded text-center">
                    <div className="text-xl font-mono text-yellow-400">
                      {knowledgeGraph?.stats?.with_findings || 0}
                    </div>
                    <div className="text-xs text-white/50">Findings</div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  {knowledgeGraph?.stats?.by_type && Object.entries(knowledgeGraph.stats.by_type).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between p-2 bg-surface-50/30 rounded">
                      <span className="text-sm text-white/70 capitalize">{type}</span>
                      <span className="text-sm font-mono text-white">{count as number}</span>
                    </div>
                  ))}
                </div>
                
                {!knowledgeGraph && (
                  <div className="text-center py-8 text-white/40">
                    <Network className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>Start AI analysis to build knowledge graph</p>
                  </div>
                )}
              </div>
            )}
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
