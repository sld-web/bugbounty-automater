import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Target,
  Bug,
  AlertTriangle,
  Pause,
  Activity,
  Zap,
} from 'lucide-react';
import { MetricCard, SeverityBadge, StatusIndicator, Terminal, ProgressBar, CyberButton } from '@/components/ui';
import { api, ENDPOINTS } from '../services/api';

interface ApiTarget {
  id: string;
  name: string;
  status: string;
  surface_coverage: number;
  program_name?: string;
}

interface ApiProgram {
  id: string;
  name: string;
}

export default function Dashboard() {
  const [targets, setTargets] = useState<ApiTarget[]>([]);
  const [programs, setPrograms] = useState<ApiProgram[]>([]);
  const [approvals, setApprovals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const demoLogs = [
    '[14:23:01] Initializing recon module...',
    '[14:23:02] Subfinder enumeration started',
    '[14:23:15] Discovered 47 subdomains',
    '[14:23:16] Amass passive scan complete',
    '[14:23:20] HTTPX probing active targets',
    '[14:23:28] Found 12 live hosts',
    '[14:23:29] Starting nuclei scan...',
    '[14:23:45] 3 potential findings detected',
  ];

  const findings = [
    { id: 1, severity: 'critical' as const, title: 'SQL Injection in /api/users', target: 'api.example.com', status: 'PENDING' },
    { id: 2, severity: 'high' as const, title: 'XSS in search parameter', target: 'app.example.com', status: 'APPROVED' },
    { id: 3, severity: 'medium' as const, title: 'CSRF on profile update', target: 'portal.example.com', status: 'REVIEW' },
  ];

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [targetsRes, programsRes, approvalsRes] = await Promise.allSettled([
          api.get(ENDPOINTS.targets),
          api.get(ENDPOINTS.programs),
          api.get(ENDPOINTS.approvals),
        ]);

        if (targetsRes.status === 'fulfilled' && targetsRes.value.data?.items) {
          setTargets(targetsRes.value.data.items);
        }
        if (programsRes.status === 'fulfilled' && Array.isArray(programsRes.value.data)) {
          setPrograms(programsRes.value.data);
        }
        if (approvalsRes.status === 'fulfilled' && approvalsRes.value.data?.items) {
          setApprovals(approvalsRes.value.data.items);
        }
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const runningTargets = targets.filter((t) => t.status === 'RUNNING');

  return (
    <div className="space-y-6">
      <div className="glass-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-display text-primary glow-text-cyan tracking-tight">
              COMMAND CENTER
            </h1>
            <p className="text-sm font-mono text-white/50 mt-1">
              Bug Bounty Automation Platform
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1.5 bg-secondary/10 border border-secondary/30 rounded text-xs font-mono text-secondary uppercase">
              HackerOne Active
            </span>
            <CyberButton variant="action" size="sm">
              <span className="flex items-center gap-2">
                <Zap className="w-4 h-4" />
                Quick Scan
              </span>
            </CyberButton>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Active Programs"
          value={loading ? '-' : programs.length}
          icon={<Bug className="w-5 h-5" />}
          trend={{ value: 12, direction: 'up' }}
          color="primary"
        />
        <MetricCard
          label="Total Targets"
          value={loading ? '-' : targets.length}
          icon={<Target className="w-5 h-5" />}
          trend={{ value: 5, direction: 'up' }}
          color="secondary"
        />
        <MetricCard
          label="Running Scans"
          value={loading ? '-' : runningTargets.length}
          icon={<Activity className="w-5 h-5" />}
          color="tertiary"
        />
        <MetricCard
          label="Pending Approvals"
          value={loading ? '-' : approvals.filter((a) => a.status === 'PENDING').length}
          icon={<AlertTriangle className="w-5 h-5" />}
          color="error"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-6">
            <div className="panel-header">
              <h2 className="section-title">Pipeline Status</h2>
              <Link to="/targets" className="text-xs font-mono text-secondary uppercase hover:underline">
                View All
              </Link>
            </div>
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center p-4 bg-surface-50/50 rounded">
                <div className="text-2xl font-display font-bold text-primary">
                  {targets.filter((t) => t.status === 'PENDING').length}
                </div>
                <div className="text-[10px] font-mono text-white/40 uppercase tracking-wider mt-1">Pending</div>
              </div>
              <div className="text-center p-4 bg-surface-50/50 rounded">
                <div className="text-2xl font-display font-bold text-secondary">
                  {targets.filter((t) => t.status === 'RUNNING').length}
                </div>
                <div className="text-[10px] font-mono text-white/40 uppercase tracking-wider mt-1">Running</div>
              </div>
              <div className="text-center p-4 bg-surface-50/50 rounded">
                <div className="text-2xl font-display font-bold text-tertiary">
                  {targets.filter((t) => t.status === 'COMPLETED').length}
                </div>
                <div className="text-[10px] font-mono text-white/40 uppercase tracking-wider mt-1">Completed</div>
              </div>
              <div className="text-center p-4 bg-surface-50/50 rounded">
                <div className="text-2xl font-display font-bold text-warning">
                  {targets.filter((t) => t.status === 'FAILED').length}
                </div>
                <div className="text-[10px] font-mono text-white/40 uppercase tracking-wider mt-1">Failed</div>
              </div>
            </div>
          </div>

          <div className="glass-card p-6">
            <div className="panel-header">
              <h2 className="section-title">Active Targets</h2>
              <Link to="/targets" className="text-xs font-mono text-secondary uppercase hover:underline">
                View All
              </Link>
            </div>

            <div className="space-y-3">
              {runningTargets.map((target) => (
                <Link
                  key={target.id}
                  to={`/targets/${target.id}`}
                  className="block p-4 bg-surface-50/50 hover:bg-surface-100/50 rounded transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <StatusIndicator status="running" />
                      <div>
                        <div className="font-mono text-sm text-white">{target.name}</div>
                        <div className="text-[10px] font-mono text-white/40 mt-0.5">
                          {target.program_name}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <div className="text-[10px] font-mono text-white/40 uppercase">Coverage</div>
                        <div className="font-mono text-sm text-secondary">
                          {target.surface_coverage}%
                        </div>
                      </div>
                      <ProgressBar value={target.surface_coverage} size="sm" className="w-20" />
                      <button className="p-2 hover:bg-surface-200/50 rounded transition-colors">
                        <Pause className="w-4 h-4 text-warning" />
                      </button>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass-card p-6">
            <div className="panel-header">
              <h2 className="section-title">Severity Distribution</h2>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <SeverityBadge severity="critical" />
                <div className="flex items-center gap-3">
                  <ProgressBar value={15} size="sm" color="error" className="w-24" />
                  <span className="font-mono text-sm text-error">2</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <SeverityBadge severity="high" />
                <div className="flex items-center gap-3">
                  <ProgressBar value={35} size="sm" color="tertiary" className="w-24" />
                  <span className="font-mono text-sm text-tertiary">5</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <SeverityBadge severity="medium" />
                <div className="flex items-center gap-3">
                  <ProgressBar value={50} size="sm" color="secondary" className="w-24" />
                  <span className="font-mono text-sm text-secondary">8</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <SeverityBadge severity="low" />
                <div className="flex items-center gap-3">
                  <ProgressBar value={80} size="sm" color="primary" className="w-24" />
                  <span className="font-mono text-sm text-primary">12</span>
                </div>
              </div>
            </div>
          </div>

          <div className="glass-card p-6">
            <div className="panel-header">
              <h2 className="section-title">Recent Findings</h2>
            </div>
            <div className="space-y-3">
              {findings.map((finding) => (
                <div key={finding.id} className="p-3 bg-surface-50/50 rounded">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <SeverityBadge severity={finding.severity} />
                    <span className="text-[10px] font-mono text-white/30">2h ago</span>
                  </div>
                  <div className="font-mono text-xs text-white mb-1">{finding.title}</div>
                  <div className="text-[10px] font-mono text-white/40">{finding.target}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card p-6">
            <div className="panel-header">
              <h2 className="section-title">Live Console</h2>
              <span className="flex items-center gap-1.5 text-[10px] font-mono text-tertiary">
                <span className="w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse" />
                LIVE
              </span>
            </div>
            <Terminal logs={demoLogs} maxLines={8} />
          </div>
        </div>
      </div>

      <div className="glass-card p-6">
        <div className="panel-header">
          <h2 className="section-title">Audit Trail</h2>
        </div>
        <div className="space-y-2">
          {[
            { time: '14:25:33', action: 'TARGET_START', user: 'system', detail: 'Started nuclei scan on api.example.com', severity: 'info' },
            { time: '14:24:18', action: 'FINDING_DETECTED', user: 'nuclei', detail: 'Potential SQL Injection in /api/users', severity: 'warning' },
            { time: '14:23:45', action: 'PLUGIN_RUN', user: 'system', detail: 'subfinder completed - 47 subdomains found', severity: 'info' },
            { time: '14:22:00', action: 'TARGET_CREATE', user: 'admin', detail: 'Created target: api.example.com', severity: 'info' },
          ].map((log, i) => (
            <div key={i} className="flex items-center gap-4 py-2 border-b border-white/5 last:border-0">
              <span className="font-mono text-xs text-white/30 w-20">{log.time}</span>
              <span className={`font-mono text-[10px] px-2 py-0.5 rounded ${
                log.severity === 'warning' ? 'bg-warning/10 text-warning' : 'bg-secondary/10 text-secondary'
              }`}>
                {log.action}
              </span>
              <span className="font-mono text-xs text-white/70 flex-1">{log.detail}</span>
              <span className="font-mono text-[10px] text-white/30">{log.user}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
