import { useState, useEffect } from 'react';
import { 
  Shield, Search, RefreshCw, ExternalLink, AlertTriangle,
  Database, GitBranch, Bug, Globe,
  Zap
} from 'lucide-react';
import { GlassCard, CyberButton } from '@/components/ui';
import { intelApi } from '@/services/api';
import toast from 'react-hot-toast';

interface CVE {
  cve_id: string;
  description: string;
  severity: string;
  cvss_score: number;
  published_date: string;
  last_modified: string;
}

export default function Intel() {
  const [activeTab, setActiveTab] = useState<'cve' | 'github' | 'leaks' | 'threat'>('cve');
  const [loading, setLoading] = useState(false);
  const [intelCards, setIntelCards] = useState<{ cves: any[]; leaks: any[] }>({ cves: [], leaks: [] });
  
  // CVE Search
  const [cveSearch, setCveSearch] = useState('');
  const [cveDays, setCveDays] = useState(7);
  const [cveLimit, setCveLimit] = useState(50);
  const [cveResults, setCveResults] = useState<CVE[]>([]);
  const [selectedCVE, setSelectedCVE] = useState<CVE | null>(null);
  
  // GitHub Search
  const [githubQuery, setGithubQuery] = useState('');
  const [githubLanguage, setGithubLanguage] = useState('');
  const [githubResults, setGithubResults] = useState<any[]>([]);
  const [githubLoading, setGithubLoading] = useState(false);
  
  // Tech Detection
  const [techContent, setTechContent] = useState('');
  const [techResults, setTechResults] = useState<any>(null);
  
  // Risk Score Calculator
  const [riskScore, setRiskScore] = useState<number | null>(null);
  const [cvssInput, setCvssInput] = useState(7.5);

  useEffect(() => {
    loadIntel();
  }, []);

  const loadIntel = async () => {
    try {
      setLoading(true);
      const res = await intelApi.cards();
      setIntelCards(res.data);
    } catch (error) {
      toast.error('Failed to load intelligence data');
    } finally {
      setLoading(false);
    }
  };

  const searchCVEs = async () => {
    try {
      setLoading(true);
      const res = await intelApi.recentCVEs(cveDays, cveLimit);
      setCveResults(res.data.cves || []);
    } catch (error) {
      toast.error('Failed to search CVEs');
    } finally {
      setLoading(false);
    }
  };

  const searchByProduct = async () => {
    if (!cveSearch.trim()) return;
    try {
      setLoading(true);
      const res = await intelApi.cveForProduct(cveSearch, undefined, 365, 50);
      setCveResults(res.data.cves || []);
    } catch (error) {
      toast.error('Failed to search product CVEs');
    } finally {
      setLoading(false);
    }
  };

  const getCVEDetails = async (cveId: string) => {
    try {
      const res = await intelApi.getCVE(cveId);
      setSelectedCVE(res.data);
    } catch (error) {
      toast.error('Failed to get CVE details');
    }
  };

  const searchGitHub = async () => {
    if (!githubQuery.trim()) return;
    try {
      setGithubLoading(true);
      const res = await intelApi.githubSearch({
        query: githubQuery,
        language: githubLanguage || undefined,
        limit: 50
      });
      setGithubResults(res.data.results || []);
    } catch (error) {
      toast.error('GitHub search failed');
    } finally {
      setGithubLoading(false);
    }
  };

  const detectTechnologies = async () => {
    if (!techContent.trim()) return;
    try {
      setLoading(true);
      const res = await intelApi.detectTech({ content: techContent, source: 'manual' });
      setTechResults(res.data);
    } catch (error) {
      toast.error('Technology detection failed');
    } finally {
      setLoading(false);
    }
  };

  const calculateRiskScore = async () => {
    try {
      const res = await intelApi.riskScore(cvssInput);
      setRiskScore(res.data.adjusted_risk_score);
    } catch (error) {
      toast.error('Risk calculation failed');
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

  const tabs = [
    { id: 'cve', label: 'CVE Database', icon: Database },
    { id: 'github', label: 'GitHub Monitor', icon: GitBranch },
    { id: 'threat', label: 'Threat Intel', icon: Shield },
  ];

  return (
    <div className="space-y-6">
      <div className="glass-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-headline text-primary tracking-wider">
              INTELLIGENCE
            </h1>
            <p className="text-xs font-mono text-white/50 mt-1">
              CVE Database, GitHub Monitoring, Threat Intelligence
            </p>
          </div>
          <CyberButton variant="secondary" onClick={loadIntel} loading={loading}>
            <RefreshCw className="w-4 h-4" />
          </CyberButton>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <GlassCard className="p-0 overflow-hidden">
            <nav className="py-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
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
          {activeTab === 'cve' && (
            <div className="space-y-6">
              <GlassCard className="p-6">
                <h2 className="section-title mb-4">Search CVEs</h2>
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="data-label">Product Name</label>
                      <input
                        type="text"
                        value={cveSearch}
                        onChange={(e) => setCveSearch(e.target.value)}
                        placeholder="e.g., nginx, wordpress"
                        className="input"
                      />
                    </div>
                    <div>
                      <label className="data-label">Days Back</label>
                      <select
                        value={cveDays}
                        onChange={(e) => setCveDays(Number(e.target.value))}
                        className="input"
                      >
                        <option value={7}>7 days</option>
                        <option value={30}>30 days</option>
                        <option value={90}>90 days</option>
                        <option value={365}>1 year</option>
                      </select>
                    </div>
                    <div>
                      <label className="data-label">Limit</label>
                      <select
                        value={cveLimit}
                        onChange={(e) => setCveLimit(Number(e.target.value))}
                        className="input"
                      >
                        <option value={25}>25</option>
                        <option value={50}>50</option>
                        <option value={100}>100</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <CyberButton onClick={searchCVEs} loading={loading}>
                      <Search className="w-4 h-4" />
                      Recent CVEs
                    </CyberButton>
                    <CyberButton variant="secondary" onClick={searchByProduct}>
                      <Bug className="w-4 h-4" />
                      Search Product
                    </CyberButton>
                  </div>
                </div>
              </GlassCard>

              <GlassCard className="p-6">
                <h2 className="section-title mb-4">Risk Score Calculator</h2>
                <div className="flex items-end gap-4">
                  <div className="flex-1">
                    <label className="data-label">CVSS Score (0-10)</label>
                    <input
                      type="number"
                      min="0"
                      max="10"
                      step="0.1"
                      value={cvssInput}
                      onChange={(e) => setCvssInput(Number(e.target.value))}
                      className="input"
                    />
                  </div>
                  <CyberButton onClick={calculateRiskScore}>
                    <Zap className="w-4 h-4" />
                    Calculate Risk
                  </CyberButton>
                  {riskScore !== null && (
                    <div className="px-4 py-2 bg-surface-50/50 rounded-lg">
                      <span className="text-xs font-mono text-white/50">Adjusted Risk:</span>
                      <span className="ml-2 text-lg font-display text-tertiary">{riskScore.toFixed(2)}</span>
                    </div>
                  )}
                </div>
              </GlassCard>

              <GlassCard className="p-6">
                <h2 className="section-title mb-4">CVE Results ({cveResults.length})</h2>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {cveResults.map((cve) => (
                    <div
                      key={cve.cve_id}
                      onClick={() => getCVEDetails(cve.cve_id)}
                      className="p-3 bg-surface-50/50 rounded-lg cursor-pointer hover:bg-surface-100/50"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-mono text-tertiary">{cve.cve_id}</span>
                          <span className={`px-2 py-0.5 rounded text-xs font-mono ${getSeverityColor(cve.severity)}`}>
                            {cve.severity}
                          </span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-mono text-white/60">
                            CVSS: {cve.cvss_score?.toFixed(1) || 'N/A'}
                          </span>
                          <ExternalLink className="w-4 h-4 text-white/30" />
                        </div>
                      </div>
                      <p className="text-xs text-white/50 mt-1 line-clamp-1">
                        {cve.description}
                      </p>
                    </div>
                  ))}
                  {cveResults.length === 0 && !loading && (
                    <div className="text-center py-8 text-white/30">
                      No CVEs found. Try searching or adjust filters.
                    </div>
                  )}
                </div>
              </GlassCard>
            </div>
          )}

          {activeTab === 'github' && (
            <div className="space-y-6">
              <GlassCard className="p-6">
                <h2 className="section-title mb-4">GitHub Code Search</h2>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="data-label">Search Query</label>
                      <input
                        type="text"
                        value={githubQuery}
                        onChange={(e) => setGithubQuery(e.target.value)}
                        placeholder="password= OR api_key= OR secret="
                        className="input"
                      />
                    </div>
                    <div>
                      <label className="data-label">Language (optional)</label>
                      <select
                        value={githubLanguage}
                        onChange={(e) => setGithubLanguage(e.target.value)}
                        className="input"
                      >
                        <option value="">All</option>
                        <option value="python">Python</option>
                        <option value="javascript">JavaScript</option>
                        <option value="typescript">TypeScript</option>
                        <option value="go">Go</option>
                        <option value="java">Java</option>
                      </select>
                    </div>
                  </div>
                  <CyberButton onClick={searchGitHub} loading={githubLoading}>
                    <GitBranch className="w-4 h-4" />
                    Search GitHub
                  </CyberButton>
                </div>
              </GlassCard>

              <GlassCard className="p-6">
                <h2 className="section-title mb-4">Technology Detection</h2>
                <div className="space-y-4">
                  <div>
                    <label className="data-label">Paste HTTP Response or Source Code</label>
                    <textarea
                      value={techContent}
                      onChange={(e) => setTechContent(e.target.value)}
                      placeholder="Paste response headers, HTML content, or source code..."
                      className="input min-h-[100px]"
                    />
                  </div>
                  <CyberButton onClick={detectTechnologies} loading={loading}>
                    <Globe className="w-4 h-4" />
                    Detect Technologies
                  </CyberButton>
                  {techResults && (
                    <div className="mt-4 p-4 bg-surface-50/50 rounded-lg">
                      <h3 className="text-sm font-mono text-white/60 mb-2">Detected Technologies:</h3>
                      <div className="flex flex-wrap gap-2">
                        {techResults.technologies?.map((tech: string, i: number) => (
                          <span key={i} className="px-2 py-1 bg-secondary/20 text-secondary text-xs rounded">
                            {tech}
                          </span>
                        ))}
                        {(!techResults.technologies || techResults.technologies.length === 0) && (
                          <span className="text-white/30 text-xs">No technologies detected</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </GlassCard>

              <GlassCard className="p-6">
                <h2 className="section-title mb-4">GitHub Search Results ({githubResults.length})</h2>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {githubResults.map((result, i) => (
                    <div key={i} className="p-3 bg-surface-50/50 rounded-lg">
                      <div className="flex items-center justify-between">
                        <a
                          href={result.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm font-mono text-tertiary hover:underline"
                        >
                          {result.path || result.name}
                        </a>
                        <ExternalLink className="w-4 h-4 text-white/30" />
                      </div>
                      <p className="text-xs text-white/50 mt-1 line-clamp-2">
                        {result.text || result.description}
                      </p>
                    </div>
                  ))}
                  {githubResults.length === 0 && !githubLoading && (
                    <div className="text-center py-8 text-white/30">
                      No results. Try a different search query.
                    </div>
                  )}
                </div>
              </GlassCard>
            </div>
          )}

          {activeTab === 'threat' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <GlassCard className="p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Database className="w-5 h-5 text-tertiary" />
                    <h2 className="section-title">Recent CVEs</h2>
                  </div>
                  <div className="text-3xl font-display text-white">
                    {intelCards.cves?.length || 0}
                  </div>
                  <div className="text-xs font-mono text-white/50 mt-1">
                    From NVD in last 7 days
                  </div>
                </GlassCard>
                <GlassCard className="p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <AlertTriangle className="w-5 h-5 text-error" />
                    <h2 className="section-title">Leak Detections</h2>
                  </div>
                  <div className="text-3xl font-display text-white">
                    {intelCards.leaks?.length || 0}
                  </div>
                  <div className="text-xs font-mono text-white/50 mt-1">
                    From GitHub monitoring
                  </div>
                </GlassCard>
              </div>

              <GlassCard className="p-6">
                <h2 className="section-title mb-4">Intelligence Sources</h2>
                <div className="space-y-3">
                  {[
                    { name: 'NVD CVE Feed', type: 'cve', enabled: true },
                    { name: 'GitHub Monitor', type: 'github', enabled: true },
                    { name: 'AlienVault OTX', type: 'otx', enabled: true },
                    { name: 'Shodan', type: 'shodan', enabled: true },
                  ].map((source) => (
                    <div key={source.name} className="flex items-center justify-between p-3 bg-surface-50/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${source.enabled ? 'bg-tertiary animate-pulse' : 'bg-white/20'}`} />
                        <span className="text-sm font-mono text-white">{source.name}</span>
                      </div>
                      <span className="text-xs font-mono text-white/40 uppercase">{source.type}</span>
                    </div>
                  ))}
                </div>
              </GlassCard>
            </div>
          )}
        </div>
      </div>

      {selectedCVE && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <GlassCard className="w-full max-w-2xl max-h-[80vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-display text-white">{selectedCVE.cve_id}</h2>
              <button onClick={() => setSelectedCVE(null)} className="text-white/40 hover:text-white">
                ×
              </button>
            </div>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <span className={`px-3 py-1 rounded text-sm font-mono ${getSeverityColor(selectedCVE.severity)}`}>
                  {selectedCVE.severity}
                </span>
                <span className="text-white/60">CVSS: {selectedCVE.cvss_score?.toFixed(1)}</span>
              </div>
              <div>
                <label className="text-xs font-mono text-white/50 uppercase">Description</label>
                <p className="text-white/80 text-sm mt-1">{selectedCVE.description}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-mono text-white/50 uppercase">Published</label>
                  <div className="text-white text-sm">{selectedCVE.published_date}</div>
                </div>
                <div>
                  <label className="text-xs font-mono text-white/50 uppercase">Last Modified</label>
                  <div className="text-white text-sm">{selectedCVE.last_modified}</div>
                </div>
              </div>
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  );
}
