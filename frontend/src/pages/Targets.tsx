import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Target, Plus, Search, Filter, ArrowRight, Play, Pause, Globe, Bug, Trash2 } from 'lucide-react';
import { GlassCard, CyberButton, StatusIndicator, ProgressBar } from '@/components/ui';
import { targetsApi } from '@/services/api';
import toast from 'react-hot-toast';

export default function Targets() {
  const [targets, setTargets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchTargets = async () => {
      try {
        const res = await targetsApi.list();
        setTargets(Array.isArray(res.data) ? res.data : res.data?.items || []);
      } catch (error) {
        console.error('Failed to fetch targets:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTargets();
  }, []);

  const handleDeleteTarget = async (e: React.MouseEvent, targetId: string, targetName: string) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!confirm(`Delete target "${targetName}"? This cannot be undone.`)) {
      return;
    }
    
    try {
      await targetsApi.delete(targetId);
      setTargets(prev => prev.filter(t => t.id !== targetId));
      toast.success(`Target "${targetName}" deleted`);
    } catch (err) {
      toast.error('Failed to delete target');
    }
  };

  const filteredTargets = targets.filter(t =>
    (t.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (t.program_name || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  const statusMap: Record<string, 'running' | 'pending' | 'completed' | 'failed' | 'idle' | 'paused'> = {
    RUNNING: 'running',
    PENDING: 'pending',
    COMPLETED: 'completed',
    FAILED: 'failed',
    PAUSED: 'paused',
  };

  return (
    <div className="space-y-6">
      <div className="glass-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-headline text-primary tracking-wider">
              TARGETS
            </h1>
            <p className="text-xs font-mono text-white/50 mt-1">
              Active reconnaissance and scanning targets
            </p>
          </div>
          <CyberButton>
            <span className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Add Target
            </span>
          </CyberButton>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
          <input
            type="text"
            placeholder="Search targets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-surface-50 border-0 rounded-lg text-sm font-mono py-3 pl-11 pr-4 text-white placeholder:text-white/30 focus:outline-none focus:ring-1 focus:ring-secondary/50"
          />
        </div>
        <button className="p-3 glass-card-subtle rounded-lg hover:bg-surface-100/50 transition-colors">
          <Filter className="w-4 h-4 text-white/60" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <GlassCard className="p-4 text-center">
          <div className="text-3xl font-display font-bold text-white mb-1">{targets.length}</div>
          <div className="text-[10px] font-mono text-white/40 uppercase">Total</div>
        </GlassCard>
        <GlassCard className="p-4 text-center">
          <div className="text-3xl font-display font-bold text-tertiary mb-1">
            {targets.filter(t => t.status === 'RUNNING').length}
          </div>
          <div className="text-[10px] font-mono text-white/40 uppercase">Running</div>
        </GlassCard>
        <GlassCard className="p-4 text-center">
          <div className="text-3xl font-display font-bold text-secondary mb-1">
            {targets.filter(t => t.status === 'COMPLETED').length}
          </div>
          <div className="text-[10px] font-mono text-white/40 uppercase">Completed</div>
        </GlassCard>
        <GlassCard className="p-4 text-center">
          <div className="text-3xl font-display font-bold text-primary mb-1">
            {targets.reduce((acc, t) => acc + (t.finding_count || 0), 0)}
          </div>
          <div className="text-[10px] font-mono text-white/40 uppercase">Findings</div>
        </GlassCard>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="glass-card p-6 animate-pulse">
              <div className="h-16 bg-surface-50/50 rounded" />
            </div>
          ))}
        </div>
      ) : filteredTargets.length > 0 ? (
        <div className="space-y-3">
          {filteredTargets.map((target) => (
            <Link key={target.id} to={`/targets/${target.id}`}>
              <GlassCard className="p-0 overflow-hidden hover:bg-surface-100/50 transition-colors group">
                <div className="p-5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-surface-50/50 rounded-lg">
                        <Globe className="w-5 h-5 text-secondary" />
                      </div>
                      <div>
                        <div className="flex items-center gap-3 mb-1">
                          <h3 className="font-mono text-white group-hover:text-primary transition-colors">
                            {target.name}
                          </h3>
                          <StatusIndicator status={statusMap[target.status] || 'idle'} size="sm" />
                        </div>
                        <div className="flex items-center gap-3 text-xs font-mono text-white/40">
                          <span className="flex items-center gap-1">
                            <Target className="w-3 h-3" />
                            {target.program_name || 'Unknown Program'}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="text-right hidden md:block">
                        <div className="text-[10px] font-mono text-white/40 uppercase mb-1">Surface</div>
                        <div className="flex items-center gap-2">
                          <ProgressBar value={target.surface_coverage || 0} size="sm" className="w-20" />
                          <span className="font-mono text-xs text-secondary w-10">
                            {target.surface_coverage || 0}%
                          </span>
                        </div>
                      </div>

                      <div className="text-right hidden md:block">
                        <div className="text-[10px] font-mono text-white/40 uppercase mb-1">Vectors</div>
                        <div className="flex items-center gap-2">
                          <ProgressBar value={target.attack_vector_coverage || 0} size="sm" color="error" className="w-20" />
                          <span className="font-mono text-xs text-error w-10">
                            {target.attack_vector_coverage || 0}%
                          </span>
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="text-[10px] font-mono text-white/40 uppercase mb-1">Findings</div>
                        <div className="flex items-center gap-1 justify-end">
                          {target.finding_count > 0 ? (
                            <>
                              <Bug className="w-3 h-3 text-tertiary" />
                              <span className="font-mono text-sm text-tertiary">{target.finding_count}</span>
                            </>
                          ) : (
                            <span className="font-mono text-sm text-white/30">0</span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 pl-4 border-l border-white/5">
                        <button
                          onClick={(e) => handleDeleteTarget(e, target.id, target.name)}
                          className="p-2 hover:bg-error/20 rounded transition-colors"
                          title="Delete target"
                        >
                          <Trash2 className="w-4 h-4 text-white/40 hover:text-error" />
                        </button>
                        {target.status === 'RUNNING' ? (
                          <button className="p-2 hover:bg-surface-100 rounded transition-colors">
                            <Pause className="w-4 h-4 text-warning" />
                          </button>
                        ) : target.status === 'PENDING' ? (
                          <button className="p-2 hover:bg-surface-100 rounded transition-colors">
                            <Play className="w-4 h-4 text-tertiary" />
                          </button>
                        ) : null}
                        <ArrowRight className="w-5 h-5 text-white/30 group-hover:text-secondary group-hover:translate-x-1 transition-all" />
                      </div>
                    </div>
                  </div>
                </div>
              </GlassCard>
            </Link>
          ))}
        </div>
      ) : (
        <GlassCard className="p-12 text-center">
          <Target className="w-12 h-12 mx-auto text-white/20 mb-4" />
          <h2 className="font-display text-xl text-white mb-2">No Targets Found</h2>
          <p className="text-sm font-mono text-white/40 mb-6">
            {searchQuery ? 'Try a different search term' : 'Add a target to start scanning'}
          </p>
          <CyberButton>
            <span className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Add Target
            </span>
          </CyberButton>
        </GlassCard>
      )}
    </div>
  );
}
