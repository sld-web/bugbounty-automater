import { useState, useEffect } from 'react';
import { 
  Play, RefreshCw, Clock, 
  Activity, Zap, AlertTriangle
} from 'lucide-react';
import { GlassCard, CyberButton, Toggle } from '@/components/ui';
import { jobsApi } from '@/services/api';
import toast from 'react-hot-toast';

interface Job {
  name: string;
  description: string;
  interval: string;
  enabled: boolean;
  last_run: string | null;
  next_run: string | null;
  status: string;
  runs: number;
  failures: number;
}

export default function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState<string | null>(null);

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    try {
      setLoading(true);
      const res = await jobsApi.list();
      setJobs(res.data.jobs || res.data || []);
    } catch (error) {
      toast.error('Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  const triggerJob = async (name: string) => {
    try {
      setTriggering(name);
      await jobsApi.trigger(name);
      toast.success(`Job "${name}" triggered`);
      loadJobs();
    } catch (error) {
      toast.error('Failed to trigger job');
    } finally {
      setTriggering(null);
    }
  };

  const toggleJob = async (name: string, enabled: boolean) => {
    try {
      if (enabled) {
        await jobsApi.enable(name);
        toast.success(`Job "${name}" enabled`);
      } else {
        await jobsApi.disable(name);
        toast.success(`Job "${name}" disabled`);
      }
      loadJobs();
    } catch (error) {
      toast.error('Failed to toggle job');
    }
  };

  const getJobIcon = (name: string) => {
    if (name.includes('cve') || name.includes('vulnerability')) return <AlertTriangle className="w-5 h-5 text-error" />;
    if (name.includes('github') || name.includes('leak')) return <Activity className="w-5 h-5 text-tertiary" />;
    if (name.includes('slack') || name.includes('notification')) return <Zap className="w-5 h-5 text-secondary" />;
    return <Clock className="w-5 h-5 text-white/50" />;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'text-secondary';
      case 'completed': return 'text-tertiary';
      case 'failed': return 'text-error';
      default: return 'text-white/50';
    }
  };

  return (
    <div className="space-y-6">
      <div className="glass-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-headline text-primary tracking-wider">
              BACKGROUND JOBS
            </h1>
            <p className="text-xs font-mono text-white/50 mt-1">
              Scheduled tasks and automation
            </p>
          </div>
          <CyberButton variant="secondary" onClick={loadJobs} loading={loading}>
            <RefreshCw className="w-4 h-4" />
          </CyberButton>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <GlassCard className="p-6 text-center">
          <div className="text-3xl font-display text-white">{jobs.length}</div>
          <div className="text-xs font-mono text-white/50 uppercase mt-1">Total Jobs</div>
        </GlassCard>
        <GlassCard className="p-6 text-center">
          <div className="text-3xl font-display text-tertiary">
            {jobs.filter(j => j.enabled).length}
          </div>
          <div className="text-xs font-mono text-tertiary uppercase mt-1">Enabled</div>
        </GlassCard>
        <GlassCard className="p-6 text-center">
          <div className="text-3xl font-display text-error">
            {jobs.filter(j => j.failures > 0).length}
          </div>
          <div className="text-xs font-mono text-error uppercase mt-1">With Failures</div>
        </GlassCard>
      </div>

      <div className="space-y-4">
        {jobs.map((job) => (
          <GlassCard key={job.name} className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-surface-50/50 flex items-center justify-center">
                  {getJobIcon(job.name)}
                </div>
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="text-white font-mono">{job.name}</h3>
                    <span className={`text-xs font-mono ${getStatusColor(job.status)}`}>
                      {job.status}
                    </span>
                  </div>
                  <p className="text-xs text-white/50 mt-1">{job.description}</p>
                  <div className="flex items-center gap-4 mt-2">
                    <span className="text-xs text-white/40">
                      <Clock className="w-3 h-3 inline mr-1" />
                      {job.interval}
                    </span>
                    {job.last_run && (
                      <span className="text-xs text-white/40">
                        Last: {new Date(job.last_run).toLocaleString()}
                      </span>
                    )}
                    <span className="text-xs text-white/40">
                      Runs: {job.runs}
                    </span>
                    {job.failures > 0 && (
                      <span className="text-xs text-error">
                        Failures: {job.failures}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Toggle
                  checked={job.enabled}
                  onChange={() => toggleJob(job.name, !job.enabled)}
                />
                <CyberButton
                  variant="secondary"
                  size="sm"
                  onClick={() => triggerJob(job.name)}
                  loading={triggering === job.name}
                >
                  <Play className="w-4 h-4" />
                </CyberButton>
              </div>
            </div>
          </GlassCard>
        ))}

        {jobs.length === 0 && !loading && (
          <GlassCard className="p-12 text-center">
            <Clock className="w-12 h-12 mx-auto text-white/20 mb-4" />
            <p className="text-white/40 font-mono">No background jobs configured</p>
          </GlassCard>
        )}
      </div>

      {loading && jobs.length === 0 && (
        <div className="flex justify-center py-12">
          <RefreshCw className="w-8 h-8 text-white/30 animate-spin" />
        </div>
      )}
    </div>
  );
}
