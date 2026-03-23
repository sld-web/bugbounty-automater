import { useState, useEffect } from 'react';
import { 
  Search, Filter, Plus, Eye, Sparkles, 
  RefreshCw, Trash, AlertTriangle, CheckCircle, 
  XCircle, ChevronDown, ChevronUp 
} from 'lucide-react';
import { GlassCard, CyberButton } from '@/components/ui';
import { findingsApi } from '@/services/api';
import toast from 'react-hot-toast';

interface Finding {
  id: string;
  title: string;
  description: string;
  severity: string;
  vuln_type: string;
  target_id: string;
  status: string;
  cvss_score?: number;
  cve_id?: string;
  created_at: string;
  updated_at: string;
}

interface Stats {
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  informational: number;
}

export default function Findings() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [_showCreateModal, setShowCreateModal] = useState(false);
  const [filters, setFilters] = useState({
    severity: '',
    vuln_type: '',
    target_id: '',
    status: '',
  });
  const [sortField, setSortField] = useState('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [enhancing, setEnhancing] = useState<string | null>(null);

  useEffect(() => {
    loadFindings();
    loadStats();
  }, []);

  const loadFindings = async () => {
    try {
      setLoading(true);
      const res = await findingsApi.list(filters);
      setFindings(res.data.findings || res.data || []);
    } catch (error) {
      toast.error('Failed to load findings');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const res = await findingsApi.stats();
      setStats(res.data);
    } catch (error) {
      console.error('Failed to load stats');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this finding?')) return;
    try {
      await findingsApi.delete(id);
      toast.success('Finding deleted');
      loadFindings();
      loadStats();
    } catch (error) {
      toast.error('Failed to delete finding');
    }
  };

  const handleEnhance = async (id: string) => {
    try {
      setEnhancing(id);
      await findingsApi.enhance(id);
      toast.success('Finding enhanced with AI');
      loadFindings();
    } catch (error) {
      toast.error('Failed to enhance finding');
    } finally {
      setEnhancing(null);
    }
  };

  const handleBatchEnhance = async () => {
    const selectedIds = findings.filter(f => (f as any).selected).map(f => f.id);
    if (selectedIds.length === 0) {
      toast.error('Select findings to enhance');
      return;
    }
    try {
      setLoading(true);
      await findingsApi.batchEnhance(selectedIds);
      toast.success(`Enhanced ${selectedIds.length} findings`);
      loadFindings();
    } catch (error) {
      toast.error('Failed to batch enhance');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return 'text-error bg-error/10';
      case 'high': return 'text-orange-500 bg-orange-500/10';
      case 'medium': return 'text-yellow-500 bg-yellow-500/10';
      case 'low': return 'text-blue-500 bg-blue-500/10';
      default: return 'text-white/50 bg-white/5';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return <XCircle className="w-4 h-4" />;
      case 'high': return <AlertTriangle className="w-4 h-4" />;
      case 'medium': return <AlertTriangle className="w-4 h-4" />;
      case 'low': return <CheckCircle className="w-4 h-4" />;
      default: return <CheckCircle className="w-4 h-4" />;
    }
  };

  const sortedFindings = [...findings].sort((a, b) => {
    const aVal = (a as any)[sortField] || '';
    const bVal = (b as any)[sortField] || '';
    const comparison = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
    return sortOrder === 'asc' ? comparison : -comparison;
  });

  return (
    <div className="space-y-6">
      <div className="glass-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-headline text-primary tracking-wider">
              FINDINGS
            </h1>
            <p className="text-xs font-mono text-white/50 mt-1">
              Vulnerability findings and AI analysis
            </p>
          </div>
          <div className="flex items-center gap-3">
            <CyberButton variant="secondary" onClick={loadFindings}>
              <RefreshCw className="w-4 h-4" />
            </CyberButton>
            <CyberButton onClick={() => setShowCreateModal(true)}>
              <Plus className="w-4 h-4" />
              Add Finding
            </CyberButton>
          </div>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-6 gap-4">
          <GlassCard className="p-4 text-center">
            <div className="text-2xl font-display text-white">{stats.total}</div>
            <div className="text-xs font-mono text-white/50 uppercase">Total</div>
          </GlassCard>
          <GlassCard className="p-4 text-center border-error/30">
            <div className="text-2xl font-display text-error">{stats.critical}</div>
            <div className="text-xs font-mono text-error uppercase">Critical</div>
          </GlassCard>
          <GlassCard className="p-4 text-center border-orange-500/30">
            <div className="text-2xl font-display text-orange-500">{stats.high}</div>
            <div className="text-xs font-mono text-orange-500 uppercase">High</div>
          </GlassCard>
          <GlassCard className="p-4 text-center border-yellow-500/30">
            <div className="text-2xl font-display text-yellow-500">{stats.medium}</div>
            <div className="text-xs font-mono text-yellow-500 uppercase">Medium</div>
          </GlassCard>
          <GlassCard className="p-4 text-center border-blue-500/30">
            <div className="text-2xl font-display text-blue-500">{stats.low}</div>
            <div className="text-xs font-mono text-blue-500 uppercase">Low</div>
          </GlassCard>
          <GlassCard className="p-4 text-center">
            <div className="text-2xl font-display text-white/50">{stats.informational}</div>
            <div className="text-xs font-mono text-white/50 uppercase">Info</div>
          </GlassCard>
        </div>
      )}

      <div className="glass-card p-4">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
              <input
                type="text"
                placeholder="Search findings..."
                className="input pl-10 w-full"
                onChange={(e) => setFilters({ ...filters, vuln_type: e.target.value })}
              />
            </div>
          </div>
          <select
            className="bg-surface-50 border-none rounded px-3 py-2 text-sm font-mono"
            value={filters.severity}
            onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
            <option value="informational">Informational</option>
          </select>
          <CyberButton variant="secondary" onClick={loadFindings}>
            <Filter className="w-4 h-4" />
          </CyberButton>
          <CyberButton variant="ghost" onClick={handleBatchEnhance}>
            <Sparkles className="w-4 h-4" />
            Batch AI Enhance
          </CyberButton>
        </div>
      </div>

      <GlassCard className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-surface-50/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-mono text-white/50 uppercase">
                  <input type="checkbox" className="rounded" />
                </th>
                <th 
                  className="px-4 py-3 text-left text-xs font-mono text-white/50 uppercase cursor-pointer"
                  onClick={() => { setSortField('severity'); setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc'); }}
                >
                  Severity {sortField === 'severity' && (sortOrder === 'asc' ? <ChevronUp className="inline w-3 h-3" /> : <ChevronDown className="inline w-3 h-3" />)}
                </th>
                <th className="px-4 py-3 text-left text-xs font-mono text-white/50 uppercase">Title</th>
                <th className="px-4 py-3 text-left text-xs font-mono text-white/50 uppercase">Type</th>
                <th className="px-4 py-3 text-left text-xs font-mono text-white/50 uppercase">CVSS</th>
                <th className="px-4 py-3 text-left text-xs font-mono text-white/50 uppercase">CVE</th>
                <th className="px-4 py-3 text-left text-xs font-mono text-white/50 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-mono text-white/50 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {sortedFindings.map((finding) => (
                <tr key={finding.id} className="hover:bg-surface-50/30">
                  <td className="px-4 py-4">
                    <input type="checkbox" className="rounded" />
                  </td>
                  <td className="px-4 py-4">
                    <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-mono ${getSeverityColor(finding.severity)}`}>
                      {getSeverityIcon(finding.severity)}
                      {finding.severity}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <div className="text-sm font-mono text-white max-w-xs truncate">
                      {finding.title}
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <span className="text-xs font-mono text-white/60">
                      {finding.vuln_type || 'N/A'}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <span className="text-sm font-mono text-white/80">
                      {finding.cvss_score?.toFixed(1) || '-'}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <span className="text-xs font-mono text-tertiary">
                      {finding.cve_id || '-'}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <span className="text-xs font-mono text-white/60">
                      {finding.status || 'open'}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setSelectedFinding(finding)}
                        className="p-1.5 hover:bg-surface-100 rounded text-white/40 hover:text-white"
                        title="View"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleEnhance(finding.id)}
                        disabled={enhancing === finding.id}
                        className="p-1.5 hover:bg-surface-100 rounded text-white/40 hover:text-tertiary disabled:opacity-50"
                        title="AI Enhance"
                      >
                        <Sparkles className={`w-4 h-4 ${enhancing === finding.id ? 'animate-pulse' : ''}`} />
                      </button>
                      <button
                        onClick={() => handleDelete(finding.id)}
                        className="p-1.5 hover:bg-surface-100 rounded text-white/40 hover:text-error"
                        title="Delete"
                      >
                        <Trash className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {sortedFindings.length === 0 && !loading && (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center">
                    <div className="text-white/30 font-mono">No findings found</div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {loading && (
          <div className="p-8 text-center">
            <RefreshCw className="w-6 h-6 mx-auto text-white/30 animate-spin" />
          </div>
        )}
      </GlassCard>

      {selectedFinding && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <GlassCard className="w-full max-w-2xl max-h-[80vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-display text-white">Finding Details</h2>
              <button onClick={() => setSelectedFinding(null)} className="text-white/40 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-xs font-mono text-white/50 uppercase">Title</label>
                <div className="text-white">{selectedFinding.title}</div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-mono text-white/50 uppercase">Severity</label>
                  <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-mono ${getSeverityColor(selectedFinding.severity)}`}>
                    {selectedFinding.severity}
                  </span>
                </div>
                <div>
                  <label className="text-xs font-mono text-white/50 uppercase">Type</label>
                  <div className="text-white">{selectedFinding.vuln_type || 'N/A'}</div>
                </div>
              </div>
              <div>
                <label className="text-xs font-mono text-white/50 uppercase">Description</label>
                <div className="text-white/80 text-sm mt-1">{selectedFinding.description}</div>
              </div>
              {selectedFinding.cve_id && (
                <div>
                  <label className="text-xs font-mono text-white/50 uppercase">CVE</label>
                  <div className="text-tertiary">{selectedFinding.cve_id}</div>
                </div>
              )}
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  );
}
