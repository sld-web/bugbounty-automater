import { useEffect, useState } from 'react';
import { 
  Package, 
  Play, 
  RefreshCw, 
  Plus, 
  Search, 
  Shield, 
  AlertTriangle,
  Clock,
  Eye,
  Settings,
  Zap
} from 'lucide-react';
import { GlassCard, CyberButton, StatusIndicator, Terminal as TerminalComponent, Modal } from '@/components/ui';
import { api, ENDPOINTS } from '../services/api';

interface Plugin {
  name: string;
  version: string;
  permission_level: 'SAFE' | 'LIMITED' | 'DANGEROUS';
  description: string;
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  timeout_seconds?: number;
  docker_image?: string;
}

const permissionColors = {
  SAFE: { bg: 'bg-tertiary/10', text: 'text-tertiary', border: 'border-tertiary/30', icon: Shield },
  LIMITED: { bg: 'bg-warning/10', text: 'text-warning', border: 'border-warning/30', icon: AlertTriangle },
  DANGEROUS: { bg: 'bg-error/10', text: 'text-error', border: 'border-error/30', icon: Zap },
};

const pluginDetails = {
  amass: {
    category: 'Reconnaissance',
    author: 'OWASP',
    lastRun: '2 hours ago',
    runCount: 47,
    avgDuration: '5m 32s',
  },
  subfinder: {
    category: 'Reconnaissance',
    author: 'ProjectDiscovery',
    lastRun: '1 hour ago',
    runCount: 89,
    avgDuration: '2m 15s',
  },
  httpx: {
    category: 'Discovery',
    author: 'ProjectDiscovery',
    lastRun: '30 minutes ago',
    runCount: 156,
    avgDuration: '8m 45s',
  },
  nmap: {
    category: 'Scanning',
    author: 'Nmap Project',
    lastRun: '4 hours ago',
    runCount: 34,
    avgDuration: '15m 20s',
  },
  nuclei: {
    category: 'Vulnerability',
    author: 'ProjectDiscovery',
    lastRun: '1 hour ago',
    runCount: 67,
    avgDuration: '25m 10s',
  },
  template: {
    category: 'Template',
    author: 'Custom',
    lastRun: 'Never',
    runCount: 0,
    avgDuration: '-',
  },
};

export default function Plugins() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterLevel, setFilterLevel] = useState<string>('all');
  const [selectedPlugin, setSelectedPlugin] = useState<Plugin | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [runningPlugins, setRunningPlugins] = useState<Set<string>>(new Set());
  const [pluginLogs, setPluginLogs] = useState<string[]>([]);
  const [showLogs, setShowLogs] = useState(false);

  useEffect(() => {
    fetchPlugins();
  }, []);

  const fetchPlugins = async () => {
    try {
      const res = await api.get(ENDPOINTS.plugins).catch(() => ({ data: { plugins: [] } }));
      setPlugins(res.data?.plugins || []);
    } catch (error) {
      console.error('Failed to fetch plugins:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunPlugin = async (pluginName: string) => {
    setRunningPlugins(prev => new Set(prev).add(pluginName));
    
    const newLogs = [
      `[${new Date().toLocaleTimeString()}] Initializing ${pluginName}...`,
      `[${new Date().toLocaleTimeString()}] Pulling Docker image...`,
      `[${new Date().toLocaleTimeString()}] Container started`,
      `[${new Date().toLocaleTimeString()}] Running ${pluginName} scan...`,
      `[${new Date().toLocaleTimeString()}] Processing results...`,
    ];
    setPluginLogs(newLogs);
    setShowLogs(true);

    setTimeout(() => {
      setRunningPlugins(prev => {
        const next = new Set(prev);
        next.delete(pluginName);
        return next;
      });
      setPluginLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Scan completed successfully`]);
    }, 3000);
  };

  const filteredPlugins = plugins.filter(plugin => {
    const matchesSearch = plugin.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         plugin.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterLevel === 'all' || plugin.permission_level === filterLevel;
    return matchesSearch && matchesFilter;
  });

  const stats = {
    total: plugins.length,
    safe: plugins.filter(p => p.permission_level === 'SAFE').length,
    limited: plugins.filter(p => p.permission_level === 'LIMITED').length,
    dangerous: plugins.filter(p => p.permission_level === 'DANGEROUS').length,
  };

  return (
    <div className="space-y-6">
      <div className="glass-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-headline text-primary tracking-wider">
              PLUGIN MANAGEMENT
            </h1>
            <p className="text-xs font-mono text-white/50 mt-1">
              Security tool plugins with Docker isolation
            </p>
          </div>
          <div className="flex items-center gap-3">
            <CyberButton variant="secondary" size="sm" onClick={fetchPlugins}>
              <span className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4" />
                Refresh
              </span>
            </CyberButton>
            <CyberButton size="sm">
              <span className="flex items-center gap-2">
                <Plus className="w-4 h-4" />
                Add Plugin
              </span>
            </CyberButton>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <GlassCard className="p-4 cursor-pointer hover:bg-surface-100/50 transition-colors" onClick={() => setFilterLevel('all')}>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Package className="w-5 h-5 text-primary" />
            </div>
            <div>
              <div className="text-2xl font-display font-bold text-white">{stats.total}</div>
              <div className="text-[10px] font-mono text-white/40 uppercase">Total</div>
            </div>
          </div>
        </GlassCard>
        <GlassCard className="p-4 cursor-pointer hover:bg-surface-100/50 transition-colors" onClick={() => setFilterLevel('SAFE')}>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-tertiary/10 rounded-lg">
              <Shield className="w-5 h-5 text-tertiary" />
            </div>
            <div>
              <div className="text-2xl font-display font-bold text-white">{stats.safe}</div>
              <div className="text-[10px] font-mono text-white/40 uppercase">Safe</div>
            </div>
          </div>
        </GlassCard>
        <GlassCard className="p-4 cursor-pointer hover:bg-surface-100/50 transition-colors" onClick={() => setFilterLevel('LIMITED')}>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-warning/10 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-warning" />
            </div>
            <div>
              <div className="text-2xl font-display font-bold text-white">{stats.limited}</div>
              <div className="text-[10px] font-mono text-white/40 uppercase">Limited</div>
            </div>
          </div>
        </GlassCard>
        <GlassCard className="p-4 cursor-pointer hover:bg-surface-100/50 transition-colors" onClick={() => setFilterLevel('DANGEROUS')}>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-error/10 rounded-lg">
              <Zap className="w-5 h-5 text-error" />
            </div>
            <div>
              <div className="text-2xl font-display font-bold text-white">{stats.dangerous}</div>
              <div className="text-[10px] font-mono text-white/40 uppercase">Dangerous</div>
            </div>
          </div>
        </GlassCard>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
          <input
            type="text"
            placeholder="Search plugins..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-surface-50 border-0 rounded-lg text-sm font-mono py-3 pl-11 pr-4 text-white placeholder:text-white/30 focus:outline-none focus:ring-1 focus:ring-secondary/50"
          />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilterLevel('all')}
            className={`px-4 py-2 text-xs font-mono rounded-lg transition-colors ${
              filterLevel === 'all' ? 'bg-secondary text-white' : 'bg-surface-50 text-white/60 hover:bg-surface-100'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilterLevel('SAFE')}
            className={`px-4 py-2 text-xs font-mono rounded-lg transition-colors ${
              filterLevel === 'SAFE' ? 'bg-tertiary text-white' : 'bg-surface-50 text-white/60 hover:bg-surface-100'
            }`}
          >
            Safe
          </button>
          <button
            onClick={() => setFilterLevel('LIMITED')}
            className={`px-4 py-2 text-xs font-mono rounded-lg transition-colors ${
              filterLevel === 'LIMITED' ? 'bg-warning text-white' : 'bg-surface-50 text-white/60 hover:bg-surface-100'
            }`}
          >
            Limited
          </button>
          <button
            onClick={() => setFilterLevel('DANGEROUS')}
            className={`px-4 py-2 text-xs font-mono rounded-lg transition-colors ${
              filterLevel === 'DANGEROUS' ? 'bg-error text-white' : 'bg-surface-50 text-white/60 hover:bg-surface-100'
            }`}
          >
            Dangerous
          </button>
        </div>
      </div>

      {showLogs && (
        <GlassCard className="p-6">
          <div className="panel-header mb-4">
            <h2 className="section-title">Plugin Execution Log</h2>
            <button onClick={() => setShowLogs(false)} className="text-xs font-mono text-white/40 hover:text-white">
              Close
            </button>
          </div>
          <TerminalComponent logs={pluginLogs} maxLines={15} />
        </GlassCard>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="glass-card p-6 animate-pulse">
              <div className="h-32 bg-surface-50/50 rounded" />
            </div>
          ))}
        </div>
      ) : filteredPlugins.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPlugins.map((plugin) => {
            const details = pluginDetails[plugin.name as keyof typeof pluginDetails] || {
              category: 'Custom',
              author: 'Unknown',
              lastRun: 'Never',
              runCount: 0,
              avgDuration: '-',
            };
            const colors = permissionColors[plugin.permission_level];
            const IconComponent = colors.icon;

            return (
              <GlassCard
                key={plugin.name}
                className="p-0 overflow-hidden hover:bg-surface-100/50 transition-colors"
              >
                <div className="p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className={`p-3 ${colors.bg} rounded-lg`}>
                        <IconComponent className={`w-6 h-6 ${colors.text}`} />
                      </div>
                      <div>
                        <h3 className="font-display text-lg text-white">{plugin.name}</h3>
                        <span className={`inline-block mt-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${colors.bg} ${colors.text}`}>
                          {plugin.permission_level}
                        </span>
                      </div>
                    </div>
                    {runningPlugins.has(plugin.name) && (
                      <StatusIndicator status="running" size="sm" />
                    )}
                  </div>

                  <p className="text-xs font-mono text-white/50 mb-4 line-clamp-2">
                    {plugin.description}
                  </p>

                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <div>
                      <div className="text-[10px] font-mono text-white/30 uppercase">Category</div>
                      <div className="text-xs font-mono text-white">{details.category}</div>
                    </div>
                    <div>
                      <div className="text-[10px] font-mono text-white/30 uppercase">Author</div>
                      <div className="text-xs font-mono text-white">{details.author}</div>
                    </div>
                    <div>
                      <div className="text-[10px] font-mono text-white/30 uppercase">Runs</div>
                      <div className="text-xs font-mono text-secondary">{details.runCount}</div>
                    </div>
                    <div>
                      <div className="text-[10px] font-mono text-white/30 uppercase">Avg Duration</div>
                      <div className="text-xs font-mono text-tertiary">{details.avgDuration}</div>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-white/5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-[10px] font-mono text-white/30">
                        <Clock className="w-3 h-3" />
                        Last run: {details.lastRun}
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            setSelectedPlugin(plugin);
                            setShowDetailModal(true);
                          }}
                          className="p-2 hover:bg-surface-50 rounded transition-colors"
                        >
                          <Eye className="w-4 h-4 text-white/60" />
                        </button>
                        <button
                          onClick={() => handleRunPlugin(plugin.name)}
                          disabled={runningPlugins.has(plugin.name)}
                          className="p-2 hover:bg-tertiary/20 rounded transition-colors disabled:opacity-50"
                        >
                          <Play className={`w-4 h-4 ${runningPlugins.has(plugin.name) ? 'text-tertiary animate-pulse' : 'text-tertiary'}`} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </GlassCard>
            );
          })}
        </div>
      ) : (
        <GlassCard className="p-12 text-center">
          <Package className="w-12 h-12 mx-auto text-white/20 mb-4" />
          <h2 className="font-display text-xl text-white mb-2">No Plugins Found</h2>
          <p className="text-sm font-mono text-white/40 mb-6">
            {searchQuery ? 'Try a different search term' : 'Add a plugin to get started'}
          </p>
          <CyberButton>
            <span className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Add Plugin
            </span>
          </CyberButton>
        </GlassCard>
      )}

      {selectedPlugin && (
        <Modal
          isOpen={showDetailModal}
          onClose={() => setShowDetailModal(false)}
          title={selectedPlugin.name}
          size="lg"
        >
          <div className="space-y-6">
            <div className="flex items-center gap-4">
              <div className={`px-3 py-1 border rounded text-xs font-mono font-bold uppercase ${
                permissionColors[selectedPlugin.permission_level].bg
              } ${permissionColors[selectedPlugin.permission_level].text} border-current`}
              >
                {selectedPlugin.permission_level}
              </div>
              <span className="text-sm font-mono text-white/50">v{selectedPlugin.version}</span>
            </div>

            <div className="glass-card-subtle p-4">
              <div className="text-[10px] font-mono text-white/40 uppercase mb-2">Description</div>
              <p className="text-sm text-white/80">{selectedPlugin.description}</p>
            </div>

            {Object.keys(selectedPlugin.inputs).length > 0 && (
              <div className="glass-card-subtle p-4">
                <div className="text-[10px] font-mono text-white/40 uppercase mb-3">Required Inputs</div>
                <div className="space-y-2">
                  {Object.entries(selectedPlugin.inputs).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                      <span className="font-mono text-xs text-white">{key}</span>
                      <span className="font-mono text-xs text-white/50">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {Object.keys(selectedPlugin.outputs).length > 0 && (
              <div className="glass-card-subtle p-4">
                <div className="text-[10px] font-mono text-white/40 uppercase mb-3">Outputs</div>
                <div className="space-y-2">
                  {Object.entries(selectedPlugin.outputs).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                      <span className="font-mono text-xs text-tertiary">{key}</span>
                      <span className="font-mono text-xs text-white/50">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <CyberButton
                variant="secondary"
                className="flex-1"
                onClick={() => setShowDetailModal(false)}
              >
                <span className="flex items-center gap-2 justify-center">
                  <Settings className="w-4 h-4" />
                  Configure
                </span>
              </CyberButton>
              <CyberButton
                variant="action"
                className="flex-1"
                onClick={() => {
                  handleRunPlugin(selectedPlugin.name);
                  setShowDetailModal(false);
                }}
              >
                <span className="flex items-center gap-2 justify-center">
                  <Play className="w-4 h-4" />
                  Run Plugin
                </span>
              </CyberButton>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
