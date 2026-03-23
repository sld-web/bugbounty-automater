import { useState } from 'react';
import { Activity, RefreshCw, Settings, CheckCircle, Link2, Unlink } from 'lucide-react';
import { GlassCard, CyberButton, Toggle, Terminal } from '@/components/ui';

const integrations = [
  {
    id: 'hackerone',
    name: 'HackerOne',
    description: 'Access programs, submit findings, sync reports',
    icon: 'H1',
    color: '#00A718',
    connected: true,
    lastSync: '2 minutes ago',
    status: 'syncing',
  },
  {
    id: 'bugcrowd',
    name: 'Bugcrowd',
    description: 'Connect to Bugcrowd programs and submissions',
    icon: 'BC',
    color: '#F47321',
    connected: false,
    lastSync: null,
    status: 'idle',
  },
  {
    id: 'shodan',
    name: 'Shodan',
    description: 'Vulnerability intelligence and network data',
    icon: 'SD',
    color: '#FB4834',
    connected: false,
    lastSync: null,
    status: 'idle',
  },
  {
    id: 'slack',
    name: 'Slack',
    description: 'Notifications and approval workflows',
    icon: 'SL',
    color: '#4A154B',
    connected: true,
    lastSync: '15 minutes ago',
    status: 'connected',
  },
  {
    id: 'github',
    name: 'GitHub',
    description: 'Repository scanning and issue tracking',
    icon: 'GH',
    color: '#24292E',
    connected: false,
    lastSync: null,
    status: 'idle',
  },
  {
    id: 'discord',
    name: 'Discord',
    description: 'Team notifications and alerts',
    icon: 'DC',
    color: '#5865F2',
    connected: false,
    lastSync: null,
    status: 'idle',
  },
];

export default function Integrations() {
  const [integrationsState, setIntegrationsState] = useState(integrations);
  const [selectedIntegration, setSelectedIntegration] = useState<string | null>(null);
  const [syncLogs, setSyncLogs] = useState<string[]>([
    '[14:20:00] Syncing with HackerOne API...',
    '[14:20:01] Fetching new programs: 12 found',
    '[14:20:02] Importing programs: complete',
    '[14:20:03] Sync completed successfully',
  ]);

  const toggleConnection = (id: string) => {
    setIntegrationsState(prev =>
      prev.map(int =>
        int.id === id
          ? {
              ...int,
              connected: !int.connected,
              lastSync: !int.connected ? 'Just now' : int.lastSync,
              status: !int.connected ? 'syncing' : 'idle',
            }
          : int
      )
    );
  };

  const syncIntegration = (id: string) => {
    setIntegrationsState(prev =>
      prev.map(int =>
        int.id === id
          ? { ...int, status: 'syncing' }
          : int
      )
    );

    setSyncLogs(prev => [
      ...prev,
      `[${new Date().toLocaleTimeString()}] Starting sync with ${integrationsState.find(i => i.id === id)?.name}...`,
      `[${new Date().toLocaleTimeString()}] Connection verified`,
      `[${new Date().toLocaleTimeString()}] Fetching data...`,
      `[${new Date().toLocaleTimeString()}] Sync completed`,
    ]);

    setTimeout(() => {
      setIntegrationsState(prev =>
        prev.map(int =>
          int.id === id
            ? { ...int, status: 'connected', lastSync: 'Just now' }
            : int
        )
      );
    }, 2000);
  };

  return (
    <div className="space-y-6">
      <div className="glass-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-headline text-primary tracking-wider">
              INTEGRATIONS
            </h1>
            <p className="text-xs font-mono text-white/50 mt-1">
              Connect external platforms and services
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="px-4 py-2 glass-card-subtle rounded-lg flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse" />
              <span className="text-xs font-mono text-white/50 uppercase">Active</span>
              <span className="font-display text-tertiary">
                {integrationsState.filter(i => i.connected).length}
              </span>
            </div>
            <div className="px-4 py-2 glass-card-subtle rounded-lg flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-secondary" />
              <span className="text-xs font-mono text-white/50 uppercase">Nodes</span>
              <span className="font-display text-secondary">
                {integrationsState.filter(i => i.status === 'syncing').length + integrationsState.filter(i => i.connected).length}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {integrationsState.map((integration) => (
              <GlassCard
                key={integration.id}
                className={`p-0 overflow-hidden transition-all ${
                  selectedIntegration === integration.id ? 'ring-2 ring-secondary' : ''
                }`}
                onClick={() => setSelectedIntegration(integration.id)}
              >
                <div className="p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div
                      className="w-12 h-12 rounded-lg flex items-center justify-center font-display font-bold text-lg"
                      style={{ backgroundColor: `${integration.color}20`, color: integration.color }}
                    >
                      {integration.icon}
                    </div>
                    <div className="flex items-center gap-2">
                      {integration.connected ? (
                        <span className="flex items-center gap-1 text-[10px] font-mono text-tertiary">
                          <CheckCircle className="w-3 h-3" />
                          Connected
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-[10px] font-mono text-white/30">
                          <Unlink className="w-3 h-3" />
                          Disconnected
                        </span>
                      )}
                    </div>
                  </div>

                  <h3 className="font-display text-white mb-1">{integration.name}</h3>
                  <p className="text-xs font-mono text-white/40 mb-4">{integration.description}</p>

                  {integration.connected && integration.lastSync && (
                    <div className="text-[10px] font-mono text-white/30 mb-4">
                      Last sync: {integration.lastSync}
                    </div>
                  )}

                  <div className="flex items-center gap-2">
                    <Toggle
                      checked={integration.connected}
                      onChange={() => toggleConnection(integration.id)}
                      size="sm"
                    />
                    {integration.connected && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          syncIntegration(integration.id);
                        }}
                        className="p-1.5 hover:bg-surface-100 rounded transition-colors"
                        disabled={integration.status === 'syncing'}
                      >
                        <RefreshCw
                          className={`w-4 h-4 text-secondary ${
                            integration.status === 'syncing' ? 'animate-spin' : ''
                          }`}
                        />
                      </button>
                    )}
                  </div>
                </div>

                {integration.status === 'syncing' && (
                  <div className="px-5 pb-4">
                    <div className="h-0.5 bg-surface-50/50 rounded-full overflow-hidden">
                      <div className="h-full bg-secondary animate-pulse" style={{ width: '60%' }} />
                    </div>
                  </div>
                )}
              </GlassCard>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <GlassCard className="p-6">
            <div className="panel-header">
              <h2 className="section-title">Configuration</h2>
              <Settings className="w-4 h-4 text-white/30" />
            </div>

            {selectedIntegration ? (
              <div className="space-y-4">
                <div className="p-4 bg-surface-50/50 rounded-lg">
                  <div className="text-[10px] font-mono text-white/40 uppercase mb-2">
                    {integrationsState.find(i => i.id === selectedIntegration)?.name}
                  </div>
                  <div className="text-xs font-mono text-white/70">
                    Configure API credentials and sync settings
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="data-label">API Token</label>
                    <input
                      type="password"
                      placeholder="Enter API token"
                      className="input"
                    />
                  </div>

                  <div>
                    <label className="data-label">Webhook URL</label>
                    <input
                      type="text"
                      placeholder="https://..."
                      className="input"
                    />
                  </div>

                  <div className="flex items-center justify-between py-2">
                    <span className="text-xs font-mono text-white/70">Auto-sync</span>
                    <Toggle checked={true} onChange={() => {}} size="sm" />
                  </div>

                  <div className="flex items-center justify-between py-2">
                    <span className="text-xs font-mono text-white/70">Sync interval</span>
                    <select className="bg-surface-50 border-none rounded text-xs font-mono py-1 px-2">
                      <option>5 minutes</option>
                      <option>15 minutes</option>
                      <option>30 minutes</option>
                      <option>1 hour</option>
                    </select>
                  </div>
                </div>

                <CyberButton variant="secondary" className="w-full">
                  <span className="flex items-center gap-2 justify-center">
                    <RefreshCw className="w-4 h-4" />
                    Test Connection
                  </span>
                </CyberButton>
              </div>
            ) : (
              <div className="text-center py-8">
                <Link2 className="w-8 h-8 mx-auto text-white/20 mb-2" />
                <p className="text-xs font-mono text-white/40">
                  Select an integration to configure
                </p>
              </div>
            )}
          </GlassCard>

          <GlassCard className="p-6">
            <div className="panel-header">
              <h2 className="section-title">Live Sync Stream</h2>
              <Activity className="w-4 h-4 text-secondary" />
            </div>
            <Terminal logs={syncLogs} maxLines={15} />
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
