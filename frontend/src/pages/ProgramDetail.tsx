import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  Bug, ArrowLeft, Target, Shield, Edit, Loader2,
  Play, CheckCircle, AlertTriangle, Zap, Search, Globe, Key,
  ArrowRight, FileText, Beaker, Upload,
  Crosshair, ShieldAlert, Terminal, Plus, Paperclip,
  GitBranch
} from 'lucide-react';
import { GlassCard, CyberButton, StatusIndicator } from '@/components/ui';
import { programsApi, targetsApi } from '@/services/api';
import AttachmentUpload from '@/components/AttachmentUpload';

interface TestingPhase {
  id: string;
  name: string;
  icon: any;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'skipped';
  tools: string[];
  checkItems: string[];
}

export default function ProgramDetail() {
  const { programId } = useParams<{ programId: string }>();
  const [program, setProgram] = useState<any>(null);
  const [targets, setTargets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAttachments, setShowAttachments] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      if (!programId) {
        setError('No program ID provided');
        setLoading(false);
        return;
      }
      
      try {
        const programRes = await programsApi.get(programId);
        setProgram(programRes.data);
        
        const targetsRes = await targetsApi.list();
        const allTargets = targetsRes.data?.items || targetsRes.data || [];
        const filtered = allTargets.filter(
          (t: any) => t.program_id === programId || t.program_name === programRes.data?.name
        );
        setTargets(filtered);
      } catch (err: any) {
        console.error('Failed to fetch program:', err);
        setError(err.response?.data?.detail || 'Failed to load program');
        setProgram(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [programId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !program) {
    return (
      <div className="space-y-6">
        <GlassCard className="p-12 text-center">
          <Bug className="w-16 h-16 text-white/20 mx-auto mb-4" />
          <h2 className="text-xl text-white mb-2">Program Not Found</h2>
          <p className="text-white/40 mb-2">{error || "The program you're looking for doesn't exist."}</p>
          <Link to="/programs" className="inline-block mt-4">
            <CyberButton>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Programs
            </CyberButton>
          </Link>
        </GlassCard>
      </div>
    );
  }

  const platformColors: Record<string, string> = {
    hackerone: 'text-[#00A718]',
    bugcrowd: 'text-[#F47321]',
    yeswehack: 'text-blue-500',
    openbugbounty: 'text-yellow-500',
    manual: 'text-white/60',
  };

  const domains = program.scope?.domains || [];
  const excluded = program.scope?.excluded || [];
  const rewardTiers = program.reward_tiers || {};
  const severityMapping = program.severity_mapping || {};
  const outOfScope = program.out_of_scope || [];

  const testingPhases: TestingPhase[] = [
    {
      id: 'recon',
      name: 'Reconnaissance',
      icon: Search,
      description: 'Discover assets, subdomains, and attack surface',
      status: 'pending',
      tools: ['Subfinder', 'Amass', 'Nuclei', 'CRT.sh'],
      checkItems: ['Subdomain enumeration', 'Port scanning', 'Technology detection', 'Directory discovery']
    },
    {
      id: 'auth',
      name: 'Authentication Testing',
      icon: Key,
      description: 'Test auth flows, sessions, and credential handling',
      status: 'pending',
      tools: ['Burp Suite', 'JWT Decoder', 'Cookie Editor'],
      checkItems: ['JWT vulnerabilities', 'Session fixation', 'OAuth misconfig', 'MFA bypass']
    },
    {
      id: 'api',
      name: 'API Security',
      icon: Terminal,
      description: 'Test REST/GraphQL endpoints for vulnerabilities',
      status: 'pending',
      tools: ['Burp Intruder', 'ffuf', 'Kite', 'GraphQL Voyager'],
      checkItems: ['IDOR', 'Mass assignment', 'Rate limiting', 'SQL injection']
    },
    {
      id: 'xss',
      name: 'XSS Testing',
      icon: Crosshair,
      description: 'Find and exploit cross-site scripting vulnerabilities',
      status: 'pending',
      tools: ['XSS Strike', 'Dalfox', 'XSStrike'],
      checkItems: ['Reflected XSS', 'Stored XSS', 'DOM XSS', 'Prototype pollution']
    },
    {
      id: 'access',
      name: 'Access Control',
      icon: ShieldAlert,
      description: 'Test authorization and privilege escalation',
      status: 'pending',
      tools: ['Burp Auth Analyzer', 'Autorize'],
      checkItems: ['Vertical privilege escalation', 'Horizontal privilege escalation', 'IDOR', 'BOLA']
    },
    {
      id: 'logic',
      name: 'Business Logic',
      icon: Beaker,
      description: 'Test application-specific logic flaws',
      status: 'pending',
      tools: ['Manual testing', 'Burp Suite'],
      checkItems: ['Race conditions', 'Price manipulation', 'OTP bypass', 'Workflow bypasses']
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <GlassCard className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/programs">
              <CyberButton variant="secondary" size="sm">
                <ArrowLeft className="w-4 h-4" />
              </CyberButton>
            </Link>
            <div className="flex items-center gap-3">
              <div className="p-3 bg-secondary/10 rounded-lg">
                <Bug className="w-6 h-6 text-secondary" />
              </div>
              <div>
                <h1 className="font-display text-headline text-primary tracking-wider">
                  {program.name || 'Unknown Program'}
                </h1>
                <div className="flex items-center gap-3 mt-1">
                  <span className={`text-xs font-mono font-bold uppercase ${platformColors[program.platform] || 'text-white/60'}`}>
                    {program.platform || 'manual'}
                  </span>
                  <StatusIndicator status="running" size="sm" />
                  <span className="text-xs text-white/40">•</span>
                  <span className="text-xs text-white/40">{targets.length} targets</span>
                </div>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <CyberButton variant="secondary" size="sm">
              <Edit className="w-4 h-4 mr-2" />
              Edit
            </CyberButton>
            <Link to={`/targets?program=${programId}`}>
              <CyberButton size="sm">
                <Play className="w-4 h-4 mr-2" />
                Start Testing
              </CyberButton>
            </Link>
          </div>
        </div>
      </GlassCard>

      {/* Testing Workflow */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Testing Phases Flow */}
        <div className="lg:col-span-2">
          <GlassCard className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-sm text-primary tracking-wider flex items-center gap-2">
                <Zap className="w-4 h-4" />
                TESTING WORKFLOW
              </h2>
              <Link to={`/programs/${programId}/workflow`}>
                <CyberButton variant="action" size="sm">
                  <GitBranch className="w-4 h-4 mr-2" />
                  AI Workflow
                </CyberButton>
              </Link>
            </div>
            <div className="relative">
              <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-white/10" />
              <div className="space-y-4">
                {testingPhases.map((phase, index) => {
                  const Icon = phase.icon;
                  return (
                    <div key={phase.id} className="relative flex items-start gap-4 pl-4">
                      <div className={`relative z-10 w-12 h-12 rounded-lg flex items-center justify-center ${
                        phase.status === 'completed' ? 'bg-tertiary/20' :
                        phase.status === 'in_progress' ? 'bg-primary/20' :
                        'bg-surface-50/50'
                      }`}>
                        <Icon className={`w-5 h-5 ${
                          phase.status === 'completed' ? 'text-tertiary' :
                          phase.status === 'in_progress' ? 'text-primary' :
                          'text-white/40'
                        }`} />
                        {index < testingPhases.length - 1 && (
                          <ArrowRight className="absolute -right-6 w-4 h-4 text-white/20" />
                        )}
                      </div>
                      <div className="flex-1 pb-4">
                        <div className="flex items-center justify-between">
                          <h3 className="font-mono text-sm text-white">{phase.name}</h3>
                          <StatusIndicator status={phase.status === 'completed' ? 'running' : 'pending'} size="sm" />
                        </div>
                        <p className="text-xs text-white/40 mt-1">{phase.description}</p>
                        <div className="flex flex-wrap gap-2 mt-2">
                          {phase.checkItems.map((item, i) => (
                            <span key={i} className="text-[10px] px-2 py-1 bg-surface-50/50 rounded text-white/50">
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Quick Stats */}
        <div className="space-y-4">
          <GlassCard className="p-5">
            <h2 className="font-display text-sm text-primary tracking-wider mb-4">REWARD TIERS</h2>
            <div className="space-y-3">
              {['critical', 'high', 'medium', 'low'].map((severity) => {
                const tier = rewardTiers[severity];
                let range = '-';
                if (tier) {
                  if (typeof tier === 'object') {
                    range = `$${tier.min || 0} - $${tier.max || 0}`;
                  } else if (Array.isArray(tier)) {
                    range = `$${tier[0]} - $${tier[1]}`;
                  }
                }
                return (
                  <div key={severity} className="flex items-center justify-between">
                    <span className={`text-xs font-mono uppercase ${
                      severity === 'critical' ? 'text-red-400' :
                      severity === 'high' ? 'text-orange-400' :
                      severity === 'medium' ? 'text-yellow-400' : 'text-green-400'
                    }`}>
                      {severity}
                    </span>
                    <span className="text-sm font-mono text-white">{range}</span>
                  </div>
                );
              })}
            </div>
          </GlassCard>

          <GlassCard className="p-5">
            <h2 className="font-display text-sm text-primary tracking-wider mb-4">WHAT TO FIND</h2>
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {Object.entries(severityMapping).length > 0 ? (
                Object.entries(severityMapping).map(([severity, vulns]) => (
                  <div key={severity} className="p-3 bg-surface-50/30 rounded">
                    <div className={`text-xs font-mono uppercase mb-2 ${
                      severity === 'critical' ? 'text-red-400' :
                      severity === 'high' ? 'text-orange-400' :
                      severity === 'medium' ? 'text-yellow-400' : 'text-green-400'
                    }`}>
                      {severity}
                    </div>
                    <div className="space-y-1">
                      {(vulns as string[]).slice(0, 5).map((vuln, i) => (
                        <div key={i} className="text-xs text-white/60 flex items-center gap-1">
                          <Crosshair className="w-3 h-3" />
                          {vuln}
                        </div>
                      ))}
                      {(vulns as string[]).length > 5 && (
                        <div className="text-[10px] text-white/30">+{(vulns as string[]).length - 5} more</div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-white/40">No specific vulnerabilities defined</p>
              )}
            </div>
          </GlassCard>
        </div>
      </div>

      {/* Scope & Targets */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard className="p-5">
          <h2 className="font-display text-sm text-primary tracking-wider mb-4 flex items-center gap-2">
            <Globe className="w-4 h-4" />
            IN-SCOPE TARGETS
          </h2>
          <div className="space-y-2 max-h-[250px] overflow-y-auto">
            {domains.length > 0 ? domains.map((domain: string, i: number) => (
              <div key={i} className="flex items-center justify-between p-3 bg-surface-50/30 rounded">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-tertiary" />
                  <code className="text-sm text-white font-mono">{domain}</code>
                </div>
                <span className="text-xs text-tertiary">Testing Allowed</span>
              </div>
            )) : (
              <p className="text-white/40 text-sm">No in-scope domains</p>
            )}
          </div>
          
          {excluded.length > 0 && (
            <>
              <h3 className="font-display text-xs text-red-400 tracking-wider mt-6 mb-3">OUT OF SCOPE</h3>
              <div className="space-y-2 max-h-[150px] overflow-y-auto">
                {excluded.map((domain: string, i: number) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-surface-50/30 rounded opacity-50">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-red-400" />
                      <code className="text-sm text-white/60 font-mono">{domain}</code>
                    </div>
                    <span className="text-xs text-red-400">Do Not Test</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </GlassCard>

        <GlassCard className="p-5">
          <h2 className="font-display text-sm text-primary tracking-wider mb-4 flex items-center gap-2">
            <Target className="w-4 h-4" />
            TEST TARGETS ({targets.length})
          </h2>
          {targets.length > 0 ? (
            <div className="space-y-2 max-h-[250px] overflow-y-auto">
              {targets.map((target: any) => (
                <Link key={target.id} to={`/targets/${target.id}`}>
                  <div className="flex items-center justify-between p-3 bg-surface-50/30 rounded hover:bg-surface-100/50 transition-colors cursor-pointer">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-primary/10 rounded flex items-center justify-center">
                        <Target className="w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <div className="text-sm text-white font-medium">{target.name}</div>
                        <div className="text-xs text-white/40">{target.target_type || 'domain'}</div>
                      </div>
                    </div>
                    <StatusIndicator status={target.status?.toLowerCase() || 'pending'} size="sm" />
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Target className="w-12 h-12 text-white/20 mx-auto mb-3" />
              <p className="text-white/40 text-sm mb-4">No targets added yet</p>
              <Link to="/targets">
                <CyberButton size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Target
                </CyberButton>
              </Link>
            </div>
          )}
        </GlassCard>
      </div>

      {/* Testing Guidelines */}
      <GlassCard className="p-5">
        <h2 className="font-display text-sm text-primary tracking-wider mb-4 flex items-center gap-2">
          <FileText className="w-4 h-4" />
          TESTING GUIDELINES
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-tertiary/10 rounded-lg border border-tertiary/20">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-4 h-4 text-tertiary" />
              <span className="font-mono text-sm text-tertiary">ALLOWED</span>
            </div>
            <ul className="space-y-1 text-xs text-white/60">
              <li>• Manual testing of identified endpoints</li>
              <li>• Testing with your own test accounts</li>
              <li>• Rate limiting respected (max 10 req/sec)</li>
              <li>• Using provided test credentials</li>
            </ul>
          </div>
          <div className="p-4 bg-warning/10 rounded-lg border border-warning/20">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-warning" />
              <span className="font-mono text-sm text-warning">REQUIRES APPROVAL</span>
            </div>
            <ul className="space-y-1 text-xs text-white/60">
              <li>• Testing on production systems</li>
              <li>• Automated vulnerability scanning</li>
              <li>• Social engineering attacks</li>
              <li>• Denial of service testing</li>
            </ul>
          </div>
          <div className="p-4 bg-error/10 rounded-lg border border-error/20">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-error" />
              <span className="font-mono text-sm text-error">PROHIBITED</span>
            </div>
            <ul className="space-y-1 text-xs text-white/60">
              {outOfScope.slice(0, 4).map((item: string, i: number) => (
                <li key={i}>• {item}</li>
              ))}
              {outOfScope.length > 4 && (
                <li className="text-white/30">+{outOfScope.length - 4} more</li>
              )}
            </ul>
          </div>
        </div>
      </GlassCard>

      {/* Attachments Section */}
      {program && (
        <GlassCard className="p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Paperclip className="w-5 h-5 text-warning" />
              <h2 className="font-display text-sm text-primary tracking-wider">
                PROGRAM ATTACHMENTS
              </h2>
            </div>
            <CyberButton 
              variant="secondary" 
              size="sm"
              onClick={() => setShowAttachments(!showAttachments)}
            >
              <Upload className="w-4 h-4 mr-2" />
              {showAttachments ? 'Hide Upload' : 'Upload Files'}
            </CyberButton>
          </div>
          
          {showAttachments && (
            <AttachmentUpload 
              programId={program.id}
              onComplete={() => setShowAttachments(false)}
            />
          )}
          
          {!showAttachments && (
            <div className="flex items-center gap-4 text-xs text-white/40">
              <button 
                onClick={() => setShowAttachments(true)}
                className="flex items-center gap-2 hover:text-white transition-colors"
              >
                <Upload className="w-4 h-4" />
                Upload credentials, certificates, or documents
              </button>
            </div>
          )}
        </GlassCard>
      )}

      {/* Next Actions */}
      <GlassCard className="p-5 bg-gradient-to-r from-primary/5 to-tertiary/5">
        <h2 className="font-display text-sm text-primary tracking-wider mb-4">NEXT ACTIONS</h2>
        <div className="flex flex-wrap gap-3">
          <Link to="/targets">
            <CyberButton>
              <Target className="w-4 h-4 mr-2" />
              Add Test Target
            </CyberButton>
          </Link>
          <Link to="/intel">
            <CyberButton variant="secondary">
              <Search className="w-4 h-4 mr-2" />
              Run Reconnaissance
            </CyberButton>
          </Link>
          <Link to="/testing">
            <CyberButton variant="secondary">
              <Zap className="w-4 h-4 mr-2" />
              Mixed Mode Testing
            </CyberButton>
          </Link>
          <Link to="/headers">
            <CyberButton variant="secondary">
              <Key className="w-4 h-4 mr-2" />
              Configure Headers
            </CyberButton>
          </Link>
        </div>
      </GlassCard>
    </div>
  );
}
