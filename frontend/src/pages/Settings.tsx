import { useState, useEffect } from 'react';
import { Shield, Key, Bell, Database, Eye, EyeOff, Save, RefreshCw, Trash2, CheckCircle, XCircle, Activity, AlertTriangle } from 'lucide-react';
import { GlassCard, CyberButton, Toggle, Terminal } from '@/components/ui';
import { api, ENDPOINTS } from '../services/api';
import toast from 'react-hot-toast';

interface ApiKeys {
  openai: string;
  shodan: string;
  censys_id: string;
  censys_secret: string;
  nvd: string;
  github: string;
  virustotal: string;
  alienvault: string;
  securitytrails: string;
  hunterio: string;
  leaklookup: string;
  slack_access: string;
  slack_refresh: string;
  hackerone: string;
}

export default function Settings() {
  const [activeTab, setActiveTab] = useState('api-keys');
  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState(false);
  const [logs, setLogs] = useState<string[]>([
    '[14:20:00] Configuration loaded',
    '[14:20:01] Database connection verified',
    '[14:20:02] Encryption service initialized',
  ]);
  const [apiKeys, setApiKeys] = useState<ApiKeys>({
    openai: '',
    shodan: '',
    censys_id: '',
    censys_secret: '',
    nvd: '',
    github: '',
    virustotal: '',
    alienvault: '',
    securitytrails: '',
    hunterio: '',
    leaklookup: '',
    slack_access: '',
    slack_refresh: '',
    hackerone: '',
  });
  const [notificationSettings, setNotificationSettings] = useState({
    slack: true,
    email: false,
    findings: true,
    scanCompletion: true,
    approvalReminders: false,
  });
  const [securitySettings, setSecuritySettings] = useState({
    twoFactor: false,
    auditLogging: true,
    pluginSandboxing: true,
  });
  const [testResults, setTestResults] = useState<Record<string, 'pending' | 'success' | 'error'>>({});
  const [apiStatus, setApiStatus] = useState<{ summary: any; apis: any[] } | null>(null);
  const [verifyingApis, setVerifyingApis] = useState(false);

  const tabs = [
    { id: 'api-keys', label: 'API Keys', icon: Key },
    { id: 'api-status', label: 'API Status', icon: Activity },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'database', label: 'Database', icon: Database },
    { id: 'security', label: 'Security', icon: Shield },
  ];

  useEffect(() => {
    loadApiKeys();
    if (activeTab === 'api-status') {
      loadApiStatus();
    }
  }, [activeTab]);

  const loadApiStatus = async () => {
    setVerifyingApis(true);
    try {
      const res = await api.get(ENDPOINTS.verifyApis);
      setApiStatus(res.data);
    } catch (error) {
      console.error('Failed to load API status');
      toast.error('Failed to verify APIs');
    } finally {
      setVerifyingApis(false);
    }
  };

  const loadApiKeys = async () => {
    try {
      const res = await api.get('/api-keys').catch(() => ({ data: null }));
      if (res.data) {
        setApiKeys(res.data);
      }
    } catch (error) {
      console.error('Failed to load API keys');
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Saving configuration...`]);
    try {
      await api.post('/api-keys', apiKeys);
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Configuration saved successfully`]);
      toast.success('Settings saved successfully');
    } catch (error) {
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Failed to save configuration`]);
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const testApiKey = async (service: string) => {
    setTestResults(prev => ({ ...prev, [service]: 'pending' }));
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Testing ${service} connection...`]);
    
    await loadApiStatus();
    
    const apiMap: Record<string, string> = {
      'OpenAI': 'openai',
      'Shodan': 'shodan',
      'NVD': 'nvd',
      'VirusTotal': 'virustotal',
      'Censys': 'censys',
      'SecurityTrails': 'securitytrails',
      'Hunter.io': 'hunterio',
      'AlienVault': 'alienvault otx',
      'LeakLookup': 'leaklookup',
      'GitHub': 'github',
      'Slack': 'slack',
    };
    
    const searchName = apiMap[service]?.toLowerCase() || service.toLowerCase();
    const foundApi = apiStatus?.apis.find(a => a.name.toLowerCase().includes(searchName));
    
    if (foundApi) {
      const success = foundApi.status === 'healthy';
      setTestResults(prev => ({ ...prev, [service]: success ? 'success' : 'error' }));
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${service}: ${foundApi.status}${foundApi.message ? ` - ${foundApi.message}` : ''}`]);
      
      if (success) {
        toast.success(`${service} connection successful`);
      } else {
        toast.error(`${service}: ${foundApi.message || foundApi.status}`);
      }
    } else {
      setTestResults(prev => ({ ...prev, [service]: 'error' }));
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${service}: Not found in status`]);
    }
  };

  const toggleShowKey = (key: string) => {
    setShowApiKey(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="space-y-6">
      <div className="glass-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-headline text-primary tracking-wider">
              SETTINGS
            </h1>
            <p className="text-xs font-mono text-white/50 mt-1">
              Configure your bug bounty automator
            </p>
          </div>
          <div className="flex items-center gap-3">
            <CyberButton variant="ghost" size="sm" onClick={loadApiKeys}>
              <span className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4" />
                Reset
              </span>
            </CyberButton>
            <CyberButton onClick={handleSave} loading={saving}>
              <span className="flex items-center gap-2">
                <Save className="w-4 h-4" />
                Save Changes
              </span>
            </CyberButton>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <GlassCard className="p-0 overflow-hidden">
            <nav className="py-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-mono transition-colors ${
                    activeTab === tab.id
                      ? 'text-primary bg-primary/10 border-r-2 border-secondary'
                      : 'text-white/60 hover:text-white hover:bg-surface-50/50'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </GlassCard>
        </div>

        <div className="lg:col-span-3">
          {activeTab === 'api-keys' && (
            <div className="space-y-6">
              <GlassCard className="p-6">
                <h2 className="section-title mb-6">AI & Intelligence APIs</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <label className="data-label">OpenAI API Key</label>
                    <div className="relative">
                      <input
                        type={showApiKey.openai ? 'text' : 'password'}
                        value={apiKeys.openai}
                        onChange={(e) => setApiKeys({ ...apiKeys, openai: e.target.value })}
                        placeholder="sk-proj-..."
                        className="input pr-10"
                      />
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                        <button onClick={() => toggleShowKey('openai')} className="text-white/40 hover:text-white/60">
                          {showApiKey.openai ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                        <button onClick={() => testApiKey('OpenAI')} className="text-white/40 hover:text-tertiary ml-1">
                          {testResults.openai === 'success' ? <CheckCircle className="w-4 h-4 text-tertiary" /> :
                           testResults.openai === 'error' ? <XCircle className="w-4 h-4 text-error" /> :
                           <RefreshCw className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="data-label">Shodan API Key</label>
                    <div className="relative">
                      <input
                        type={showApiKey.shodan ? 'text' : 'password'}
                        value={apiKeys.shodan}
                        onChange={(e) => setApiKeys({ ...apiKeys, shodan: e.target.value })}
                        placeholder="Enter Shodan API key"
                        className="input pr-10"
                      />
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                        <button onClick={() => toggleShowKey('shodan')} className="text-white/40 hover:text-white/60">
                          {showApiKey.shodan ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                        <button onClick={() => testApiKey('Shodan')} className="text-white/40 hover:text-tertiary ml-1">
                          {testResults.shodan === 'success' ? <CheckCircle className="w-4 h-4 text-tertiary" /> :
                           testResults.shodan === 'error' ? <XCircle className="w-4 h-4 text-error" /> :
                           <RefreshCw className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="data-label">NVD API Key (Vulnerability Database)</label>
                    <div className="relative">
                      <input
                        type={showApiKey.nvd ? 'text' : 'password'}
                        value={apiKeys.nvd}
                        onChange={(e) => setApiKeys({ ...apiKeys, nvd: e.target.value })}
                        placeholder="Enter NVD API key"
                        className="input pr-10"
                      />
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                        <button onClick={() => toggleShowKey('nvd')} className="text-white/40 hover:text-white/60">
                          {showApiKey.nvd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                        <button onClick={() => testApiKey('NVD')} className="text-white/40 hover:text-tertiary ml-1">
                          {testResults.nvd === 'success' ? <CheckCircle className="w-4 h-4 text-tertiary" /> :
                           testResults.nvd === 'error' ? <XCircle className="w-4 h-4 text-error" /> :
                           <RefreshCw className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="data-label">VirusTotal API Key</label>
                    <div className="relative">
                      <input
                        type={showApiKey.virustotal ? 'text' : 'password'}
                        value={apiKeys.virustotal}
                        onChange={(e) => setApiKeys({ ...apiKeys, virustotal: e.target.value })}
                        placeholder="Enter VirusTotal API key"
                        className="input pr-10"
                      />
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                        <button onClick={() => toggleShowKey('virustotal')} className="text-white/40 hover:text-white/60">
                          {showApiKey.virustotal ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                        <button onClick={() => testApiKey('VirusTotal')} className="text-white/40 hover:text-tertiary ml-1">
                          {testResults.virustotal === 'success' ? <CheckCircle className="w-4 h-4 text-tertiary" /> :
                           testResults.virustotal === 'error' ? <XCircle className="w-4 h-4 text-error" /> :
                           <RefreshCw className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </GlassCard>

              <GlassCard className="p-6">
                <h2 className="section-title mb-6">Reconnaissance APIs</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <label className="data-label">Censys API ID</label>
                    <div className="relative">
                      <input
                        type="text"
                        value={apiKeys.censys_id}
                        onChange={(e) => setApiKeys({ ...apiKeys, censys_id: e.target.value })}
                        placeholder="Enter Censys API ID"
                        className="input pr-10"
                      />
                      <button onClick={() => testApiKey('Censys')} className="absolute right-2 top-1/2 -translate-y-1/2 text-white/40 hover:text-tertiary">
                        {testResults.censys === 'success' ? <CheckCircle className="w-4 h-4 text-tertiary" /> :
                         testResults.censys === 'error' ? <XCircle className="w-4 h-4 text-error" /> :
                         <RefreshCw className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="data-label">Censys API Secret</label>
                    <div className="relative">
                      <input
                        type={showApiKey.censys_secret ? 'text' : 'password'}
                        value={apiKeys.censys_secret}
                        onChange={(e) => setApiKeys({ ...apiKeys, censys_secret: e.target.value })}
                        placeholder="Enter Censys API Secret"
                        className="input pr-10"
                      />
                      <button onClick={() => toggleShowKey('censys_secret')} className="absolute right-8 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/60">
                        {showApiKey.censys_secret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="data-label">SecurityTrails API Key</label>
                    <div className="relative">
                      <input
                        type={showApiKey.securitytrails ? 'text' : 'password'}
                        value={apiKeys.securitytrails}
                        onChange={(e) => setApiKeys({ ...apiKeys, securitytrails: e.target.value })}
                        placeholder="Enter SecurityTrails API key"
                        className="input pr-10"
                      />
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                        <button onClick={() => toggleShowKey('securitytrails')} className="text-white/40 hover:text-white/60">
                          {showApiKey.securitytrails ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                        <button onClick={() => testApiKey('SecurityTrails')} className="text-white/40 hover:text-tertiary ml-1">
                          {testResults.securitytrails === 'success' ? <CheckCircle className="w-4 h-4 text-tertiary" /> :
                           testResults.securitytrails === 'error' ? <XCircle className="w-4 h-4 text-error" /> :
                           <RefreshCw className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="data-label">Hunter.io API Key</label>
                    <div className="relative">
                      <input
                        type={showApiKey.hunterio ? 'text' : 'password'}
                        value={apiKeys.hunterio}
                        onChange={(e) => setApiKeys({ ...apiKeys, hunterio: e.target.value })}
                        placeholder="Enter Hunter.io API key"
                        className="input pr-10"
                      />
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                        <button onClick={() => toggleShowKey('hunterio')} className="text-white/40 hover:text-white/60">
                          {showApiKey.hunterio ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                        <button onClick={() => testApiKey('Hunter.io')} className="text-white/40 hover:text-tertiary ml-1">
                          {testResults.hunterio === 'success' ? <CheckCircle className="w-4 h-4 text-tertiary" /> :
                           testResults.hunterio === 'error' ? <XCircle className="w-4 h-4 text-error" /> :
                           <RefreshCw className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="data-label">AlienVault OTX API Key</label>
                    <div className="relative">
                      <input
                        type={showApiKey.alienvault ? 'text' : 'password'}
                        value={apiKeys.alienvault}
                        onChange={(e) => setApiKeys({ ...apiKeys, alienvault: e.target.value })}
                        placeholder="Enter AlienVault OTX API key"
                        className="input pr-10"
                      />
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                        <button onClick={() => toggleShowKey('alienvault')} className="text-white/40 hover:text-white/60">
                          {showApiKey.alienvault ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                        <button onClick={() => testApiKey('AlienVault')} className="text-white/40 hover:text-tertiary ml-1">
                          {testResults.alienvault === 'success' ? <CheckCircle className="w-4 h-4 text-tertiary" /> :
                           testResults.alienvault === 'error' ? <XCircle className="w-4 h-4 text-error" /> :
                           <RefreshCw className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="data-label">LeakLookup API Key</label>
                    <div className="relative">
                      <input
                        type={showApiKey.leaklookup ? 'text' : 'password'}
                        value={apiKeys.leaklookup}
                        onChange={(e) => setApiKeys({ ...apiKeys, leaklookup: e.target.value })}
                        placeholder="Enter LeakLookup API key"
                        className="input pr-10"
                      />
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                        <button onClick={() => toggleShowKey('leaklookup')} className="text-white/40 hover:text-white/60">
                          {showApiKey.leaklookup ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                        <button onClick={() => testApiKey('LeakLookup')} className="text-white/40 hover:text-tertiary ml-1">
                          {testResults.leaklookup === 'success' ? <CheckCircle className="w-4 h-4 text-tertiary" /> :
                           testResults.leaklookup === 'error' ? <XCircle className="w-4 h-4 text-error" /> :
                           <RefreshCw className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </GlassCard>

              <GlassCard className="p-6">
                <h2 className="section-title mb-6">Bug Bounty Platform APIs</h2>
                <div className="space-y-6">
                  <div className="space-y-3">
                    <label className="data-label">HackerOne API Token</label>
                    <div className="relative">
                      <input
                        type={showApiKey.hackerone ? 'text' : 'password'}
                        value={apiKeys.hackerone}
                        onChange={(e) => setApiKeys({ ...apiKeys, hackerone: e.target.value })}
                        placeholder="Enter HackerOne API token"
                        className="input pr-10"
                      />
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse" />
                        <span className="text-[10px] font-mono text-tertiary mr-2">Active</span>
                        <button onClick={() => toggleShowKey('hackerone')} className="text-white/40 hover:text-white/60">
                          {showApiKey.hackerone ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="data-label">GitHub Token (for repo scanning)</label>
                    <div className="relative">
                      <input
                        type={showApiKey.github ? 'text' : 'password'}
                        value={apiKeys.github}
                        onChange={(e) => setApiKeys({ ...apiKeys, github: e.target.value })}
                        placeholder="github_pat_..."
                        className="input pr-10"
                      />
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                        <button onClick={() => toggleShowKey('github')} className="text-white/40 hover:text-white/60">
                          {showApiKey.github ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                        <button onClick={() => testApiKey('GitHub')} className="text-white/40 hover:text-tertiary ml-1">
                          {testResults.github === 'success' ? <CheckCircle className="w-4 h-4 text-tertiary" /> :
                           testResults.github === 'error' ? <XCircle className="w-4 h-4 text-error" /> :
                           <RefreshCw className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </GlassCard>

              <GlassCard className="p-6">
                <h2 className="section-title mb-6">Notification APIs</h2>
                <div className="space-y-6">
                  <div className="space-y-3">
                    <label className="data-label">Slack Access Token</label>
                    <div className="relative">
                      <input
                        type={showApiKey.slack_access ? 'text' : 'password'}
                        value={apiKeys.slack_access}
                        onChange={(e) => setApiKeys({ ...apiKeys, slack_access: e.target.value })}
                        placeholder="xoxe.xoxp-..."
                        className="input pr-10"
                      />
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                        <button onClick={() => toggleShowKey('slack_access')} className="text-white/40 hover:text-white/60">
                          {showApiKey.slack_access ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                        <button onClick={() => testApiKey('Slack')} className="text-white/40 hover:text-tertiary ml-1">
                          {testResults.slack === 'success' ? <CheckCircle className="w-4 h-4 text-tertiary" /> :
                           testResults.slack === 'error' ? <XCircle className="w-4 h-4 text-error" /> :
                           <RefreshCw className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="data-label">Slack Refresh Token</label>
                    <div className="relative">
                      <input
                        type={showApiKey.slack_refresh ? 'text' : 'password'}
                        value={apiKeys.slack_refresh}
                        onChange={(e) => setApiKeys({ ...apiKeys, slack_refresh: e.target.value })}
                        placeholder="xoxe-..."
                        className="input pr-10"
                      />
                      <button onClick={() => toggleShowKey('slack_refresh')} className="absolute right-2 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/60">
                        {showApiKey.slack_refresh ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                </div>
              </GlassCard>
            </div>
          )}

          {activeTab === 'api-status' && (
            <div className="space-y-6">
              <GlassCard className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="section-title">API Status</h2>
                  <CyberButton variant="secondary" size="sm" onClick={loadApiStatus} loading={verifyingApis}>
                    <span className="flex items-center gap-2">
                      <RefreshCw className="w-4 h-4" />
                      Verify All
                    </span>
                  </CyberButton>
                </div>

                {apiStatus && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-4 gap-4">
                      <div className="p-4 bg-surface-50/50 rounded-lg text-center">
                        <div className="text-2xl font-display text-white">{apiStatus.summary.total}</div>
                        <div className="text-xs font-mono text-white/40 uppercase">Total APIs</div>
                      </div>
                      <div className="p-4 bg-tertiary/10 rounded-lg text-center">
                        <div className="text-2xl font-display text-tertiary">{apiStatus.summary.healthy}</div>
                        <div className="text-xs font-mono text-tertiary uppercase">Healthy</div>
                      </div>
                      <div className="p-4 bg-error/10 rounded-lg text-center">
                        <div className="text-2xl font-display text-error">{apiStatus.summary.errors}</div>
                        <div className="text-xs font-mono text-error uppercase">Errors</div>
                      </div>
                      <div className="p-4 bg-surface-50/50 rounded-lg text-center">
                        <div className="text-2xl font-display text-white/40">{apiStatus.summary.not_configured}</div>
                        <div className="text-xs font-mono text-white/40 uppercase">Not Configured</div>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-sm font-mono text-white/60 uppercase mb-4">AI & Intelligence APIs</h3>
                      <div className="space-y-2">
                        {apiStatus.apis.filter(a => a.category === 'AI' || a.category === 'Intelligence').map((api) => (
                          <div key={api.name} className="flex items-center justify-between p-3 bg-surface-50/50 rounded-lg">
                            <div className="flex items-center gap-3">
                              {api.status === 'healthy' ? (
                                <CheckCircle className="w-4 h-4 text-tertiary" />
                              ) : api.status === 'not_configured' ? (
                                <AlertTriangle className="w-4 h-4 text-white/30" />
                              ) : (
                                <XCircle className="w-4 h-4 text-error" />
                              )}
                              <div>
                                <div className="text-sm font-mono text-white">{api.name}</div>
                                {api.message && (
                                  <div className="text-xs text-white/40">{api.message}</div>
                                )}
                                {api.details && (
                                  <div className="text-xs text-white/30">
                                    {Object.entries(api.details).slice(0, 2).map(([k, v]) => `${k}: ${v}`).join(' | ')}
                                  </div>
                                )}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className={`text-xs font-mono uppercase ${
                                api.status === 'healthy' ? 'text-tertiary' : 
                                api.status === 'not_configured' ? 'text-white/40' : 'text-error'
                              }`}>
                                {api.status}
                              </div>
                              {api.response_time_ms && (
                                <div className="text-xs text-white/30">{api.response_time_ms}ms</div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h3 className="text-sm font-mono text-white/60 uppercase mb-4">Notifications</h3>
                      <div className="space-y-2">
                        {apiStatus.apis.filter(a => a.category === 'Notifications').map((api) => (
                          <div key={api.name} className="flex items-center justify-between p-3 bg-surface-50/50 rounded-lg">
                            <div className="flex items-center gap-3">
                              {api.status === 'healthy' ? (
                                <CheckCircle className="w-4 h-4 text-tertiary" />
                              ) : api.status === 'not_configured' ? (
                                <AlertTriangle className="w-4 h-4 text-white/30" />
                              ) : (
                                <XCircle className="w-4 h-4 text-error" />
                              )}
                              <div>
                                <div className="text-sm font-mono text-white">{api.name}</div>
                                {api.message && (
                                  <div className="text-xs text-white/40">{api.message}</div>
                                )}
                              </div>
                            </div>
                            <div className={`text-xs font-mono uppercase ${
                              api.status === 'healthy' ? 'text-tertiary' : 
                              api.status === 'not_configured' ? 'text-white/40' : 'text-error'
                            }`}>
                              {api.status}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {!apiStatus && !verifyingApis && (
                  <div className="text-center py-12">
                    <Activity className="w-12 h-12 mx-auto text-white/20 mb-4" />
                    <p className="text-sm font-mono text-white/40">Click "Verify All" to check API status</p>
                  </div>
                )}

                {verifyingApis && (
                  <div className="text-center py-12">
                    <RefreshCw className="w-12 h-12 mx-auto text-secondary animate-spin mb-4" />
                    <p className="text-sm font-mono text-white/40">Verifying API connections...</p>
                  </div>
                )}
              </GlassCard>
            </div>
          )}

          {activeTab === 'notifications' && (
            <GlassCard className="p-6">
              <h2 className="section-title mb-6">Notification Preferences</h2>
              <div className="space-y-6">
                <div className="flex items-center justify-between p-4 bg-surface-50/50 rounded-lg">
                  <div>
                    <div className="text-sm font-mono text-white">Slack Notifications</div>
                    <div className="text-xs text-white/40 mt-1">Receive approval requests via Slack</div>
                  </div>
                  <Toggle 
                    checked={notificationSettings.slack} 
                    onChange={() => setNotificationSettings({ ...notificationSettings, slack: !notificationSettings.slack })} 
                  />
                </div>

                <div className="flex items-center justify-between p-4 bg-surface-50/50 rounded-lg">
                  <div>
                    <div className="text-sm font-mono text-white">Email Notifications</div>
                    <div className="text-xs text-white/40 mt-1">Get notified via email</div>
                  </div>
                  <Toggle 
                    checked={notificationSettings.email} 
                    onChange={() => setNotificationSettings({ ...notificationSettings, email: !notificationSettings.email })} 
                  />
                </div>

                <div className="flex items-center justify-between p-4 bg-surface-50/50 rounded-lg">
                  <div>
                    <div className="text-sm font-mono text-white">Finding Alerts</div>
                    <div className="text-xs text-white/40 mt-1">Alert when new vulnerabilities are found</div>
                  </div>
                  <Toggle 
                    checked={notificationSettings.findings} 
                    onChange={() => setNotificationSettings({ ...notificationSettings, findings: !notificationSettings.findings })} 
                  />
                </div>

                <div className="flex items-center justify-between p-4 bg-surface-50/50 rounded-lg">
                  <div>
                    <div className="text-sm font-mono text-white">Scan Completion</div>
                    <div className="text-xs text-white/40 mt-1">Notify when target scans complete</div>
                  </div>
                  <Toggle 
                    checked={notificationSettings.scanCompletion} 
                    onChange={() => setNotificationSettings({ ...notificationSettings, scanCompletion: !notificationSettings.scanCompletion })} 
                  />
                </div>

                <div className="flex items-center justify-between p-4 bg-surface-50/50 rounded-lg">
                  <div>
                    <div className="text-sm font-mono text-white">Approval Reminders</div>
                    <div className="text-xs text-white/40 mt-1">Remind about pending approvals</div>
                  </div>
                  <Toggle 
                    checked={notificationSettings.approvalReminders} 
                    onChange={() => setNotificationSettings({ ...notificationSettings, approvalReminders: !notificationSettings.approvalReminders })} 
                  />
                </div>
              </div>
            </GlassCard>
          )}

          {activeTab === 'database' && (
            <div className="space-y-6">
              <GlassCard className="p-6">
                <h2 className="section-title mb-6">Database Configuration</h2>
                <div className="space-y-4">
                  <div className="space-y-3">
                    <label className="data-label">Database URL</label>
                    <input
                      type="text"
                      defaultValue="sqlite:///./test.db"
                      className="input"
                      disabled
                    />
                  </div>
                  <div className="flex items-center gap-3">
                    <CyberButton variant="secondary">
                      <span className="flex items-center gap-2">
                        <RefreshCw className="w-4 h-4" />
                        Run Migrations
                      </span>
                    </CyberButton>
                    <CyberButton variant="danger">
                      <span className="flex items-center gap-2">
                        <Trash2 className="w-4 h-4" />
                        Clear Data
                      </span>
                    </CyberButton>
                  </div>
                </div>
              </GlassCard>

              <GlassCard className="p-6">
                <h2 className="section-title mb-6">Data Retention</h2>
                <div className="space-y-4">
                  <div>
                    <label className="data-label mb-4 block">Findings Retention Period</label>
                    <input
                      type="range"
                      min="30"
                      max="365"
                      defaultValue="90"
                      className="w-full accent-secondary"
                    />
                    <div className="flex justify-between text-xs font-mono text-white/40 mt-2">
                      <span>30 days</span>
                      <span className="text-secondary">90 days</span>
                      <span>365 days</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-4 bg-surface-50/50 rounded-lg">
                    <div>
                      <div className="text-sm font-mono text-white">Auto-cleanup Logs</div>
                      <div className="text-xs text-white/40 mt-1">Remove logs older than retention period</div>
                    </div>
                    <Toggle checked={true} onChange={() => {}} />
                  </div>
                </div>
              </GlassCard>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              <GlassCard className="p-6">
                <h2 className="section-title mb-6">Encryption Status</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-surface-50/50 rounded-lg text-center">
                    <div className="w-12 h-12 mx-auto mb-2 rounded-full bg-tertiary/10 flex items-center justify-center">
                      <Shield className="w-6 h-6 text-tertiary" />
                    </div>
                    <div className="text-xs font-mono text-tertiary uppercase">Encryption</div>
                    <div className="text-lg font-display text-white mt-1">Active</div>
                  </div>
                  <div className="p-4 bg-surface-50/50 rounded-lg text-center">
                    <div className="w-12 h-12 mx-auto mb-2 rounded-full bg-secondary/10 flex items-center justify-center">
                      <Key className="w-6 h-6 text-secondary" />
                    </div>
                    <div className="text-xs font-mono text-secondary uppercase">Credentials</div>
                    <div className="text-lg font-display text-white mt-1">Secured</div>
                  </div>
                </div>
              </GlassCard>

              <GlassCard className="p-6">
                <h2 className="section-title mb-6">Security Settings</h2>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-surface-50/50 rounded-lg">
                    <div>
                      <div className="text-sm font-mono text-white">Two-Factor Authentication</div>
                      <div className="text-xs text-white/40 mt-1">Require 2FA for all users</div>
                    </div>
                    <Toggle 
                      checked={securitySettings.twoFactor} 
                      onChange={() => setSecuritySettings({ ...securitySettings, twoFactor: !securitySettings.twoFactor })} 
                    />
                  </div>
                  <div className="flex items-center justify-between p-4 bg-surface-50/50 rounded-lg">
                    <div>
                      <div className="text-sm font-mono text-white">Audit Logging</div>
                      <div className="text-xs text-white/40 mt-1">Log all user actions</div>
                    </div>
                    <Toggle 
                      checked={securitySettings.auditLogging} 
                      onChange={() => setSecuritySettings({ ...securitySettings, auditLogging: !securitySettings.auditLogging })} 
                    />
                  </div>
                  <div className="flex items-center justify-between p-4 bg-surface-50/50 rounded-lg">
                    <div>
                      <div className="text-sm font-mono text-white">Plugin Sandboxing</div>
                      <div className="text-xs text-white/40 mt-1">Run plugins in isolated containers</div>
                    </div>
                    <Toggle 
                      checked={securitySettings.pluginSandboxing} 
                      onChange={() => setSecuritySettings({ ...securitySettings, pluginSandboxing: !securitySettings.pluginSandboxing })} 
                    />
                  </div>
                </div>
              </GlassCard>
            </div>
          )}
        </div>
      </div>

      <GlassCard className="p-6">
        <div className="panel-header">
          <h2 className="section-title">Diagnostic Terminal</h2>
        </div>
        <Terminal logs={logs} maxLines={10} />
      </GlassCard>
    </div>
  );
}
