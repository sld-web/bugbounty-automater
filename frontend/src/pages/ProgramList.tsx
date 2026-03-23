import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bug, Plus, ArrowRight, Trophy, Target, Trash2 } from 'lucide-react';
import { GlassCard, CyberButton, StatusIndicator } from '@/components/ui';
import { programsApi } from '@/services/api';
import toast from 'react-hot-toast';

export default function ProgramList() {
  const [programs, setPrograms] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchPrograms = async () => {
      try {
        const res = await programsApi.list();
        setPrograms(Array.isArray(res.data) ? res.data : res.data?.items || []);
      } catch (error) {
        console.error('Failed to fetch programs:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPrograms();
  }, []);

  const platformColors: Record<string, { bg: string; text: string }> = {
    hackerone: { bg: 'bg-[#00A718]/20', text: 'text-[#00A718]' },
    bugcrowd: { bg: 'bg-[#F47321]/20', text: 'text-[#F47321]' },
    yeswehack: { bg: 'bg-blue-500/20', text: 'text-blue-500' },
    openbugbounty: { bg: 'bg-yellow-500/20', text: 'text-yellow-500' },
    manual: { bg: 'bg-white/10', text: 'text-white/60' },
  };

  const handleProgramClick = (programId: string) => {
    navigate(`/programs/${programId}`);
  };

  const handleDeleteProgram = async (e: React.MouseEvent, programId: string, programName: string) => {
    e.stopPropagation();
    
    if (!confirm(`Delete program "${programName}"? This cannot be undone.`)) {
      return;
    }
    
    try {
      await programsApi.delete(programId);
      setPrograms(prev => prev.filter(p => p.id !== programId));
      toast.success(`Program "${programName}" deleted`);
    } catch (err) {
      toast.error('Failed to delete program');
    }
  };

  return (
    <div className="space-y-6">
      <div className="glass-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-headline text-primary tracking-wider">
              PROGRAMS
            </h1>
            <p className="text-xs font-mono text-white/50 mt-1">
              Bug bounty program management
            </p>
          </div>
          <div className="flex gap-3">
            <Link to="/programs/import">
              <CyberButton variant="secondary">
                <span className="flex items-center gap-2">
                  <Plus className="w-4 h-4" />
                  Import from Policy
                </span>
              </CyberButton>
            </Link>
            <CyberButton>
              <span className="flex items-center gap-2">
                <Plus className="w-4 h-4" />
                Add Program
              </span>
            </CyberButton>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <GlassCard className="p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-secondary/10 rounded-lg">
              <Bug className="w-5 h-5 text-secondary" />
            </div>
            <div>
              <div className="text-2xl font-display font-bold text-white">{programs.length}</div>
              <div className="text-[10px] font-mono text-white/40 uppercase">Total Programs</div>
            </div>
          </div>
        </GlassCard>
        <GlassCard className="p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-tertiary/10 rounded-lg">
              <Target className="w-5 h-5 text-tertiary" />
            </div>
            <div>
              <div className="text-2xl font-display font-bold text-white">
                {programs.reduce((acc, p) => acc + (p.target_count || 0), 0)}
              </div>
              <div className="text-[10px] font-mono text-white/40 uppercase">Active Targets</div>
            </div>
          </div>
        </GlassCard>
        <GlassCard className="p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Trophy className="w-5 h-5 text-primary" />
            </div>
            <div>
              <div className="text-2xl font-display font-bold text-white">
                {programs.reduce((acc, p) => acc + (p.finding_count || 0), 0)}
              </div>
              <div className="text-[10px] font-mono text-white/40 uppercase">Total Findings</div>
            </div>
          </div>
        </GlassCard>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="glass-card p-6 animate-pulse">
              <div className="h-24 bg-surface-50/50 rounded" />
            </div>
          ))}
        </div>
      ) : programs.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {programs.map((program) => (
            <div
              key={program.id}
              onClick={() => handleProgramClick(program.id)}
              className="group cursor-pointer"
            >
              <GlassCard className="p-0 overflow-hidden h-full hover:bg-surface-100/50 transition-colors">
                <div className="p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-surface-50/50 rounded-lg">
                        <Bug className="w-5 h-5 text-secondary" />
                      </div>
                      <div>
                        <h3 className="font-display text-white group-hover:text-primary transition-colors">
                          {program.name}
                        </h3>
                        <span className={`inline-block mt-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                          platformColors[program.platform]
                            ? `${platformColors[program.platform].bg} ${platformColors[program.platform].text}`
                            : 'bg-white/10 text-white/60'
                        }`}>
                          {program.platform}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={(e) => handleDeleteProgram(e, program.id, program.name)}
                        className="p-1.5 hover:bg-error/20 rounded text-white/40 hover:text-error transition-colors"
                        title="Delete program"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                      <StatusIndicator status="running" size="sm" />
                    </div>
                  </div>

                  <div className="space-y-2 mb-4">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-white/40">Domains</span>
                      <span className="text-white">{program.scope?.domains?.length || 0}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-white/40">Targets</span>
                      <span className="text-secondary">{program.target_count || 0}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-white/40">Findings</span>
                      <span className="text-tertiary">{program.finding_count || 0}</span>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-white/5">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-[10px] font-mono text-white/40 uppercase">Confidence</div>
                        <div className="font-display text-lg text-primary">
                          {Math.round((program.confidence_score || 0.8) * 100)}%
                        </div>
                      </div>
                      <ArrowRight className="w-5 h-5 text-white/30 group-hover:text-secondary group-hover:translate-x-1 transition-all" />
                    </div>
                  </div>
                </div>
              </GlassCard>
            </div>
          ))}
        </div>
      ) : (
        <GlassCard className="p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-secondary/10 flex items-center justify-center">
            <Bug className="w-8 h-8 text-secondary" />
          </div>
          <h2 className="font-display text-xl text-white mb-2">No Programs Yet</h2>
          <p className="text-sm font-mono text-white/40 mb-6">
            Add a bug bounty program to start hunting
          </p>
          <CyberButton>
            <span className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Add Program
            </span>
          </CyberButton>
        </GlassCard>
      )}
    </div>
  );
}
