import { useState, useRef } from 'react';
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  Plus,
  Trash2,
  DollarSign,
  Target,
  Shield,
  Clock,
  Paperclip,
  Key,
  Loader2,
  Server,
  Globe,
  Wifi,
  FileCheck,
  X,
  Eye
} from 'lucide-react';
import { GlassCard, CyberButton } from '@/components/ui';
import { programsApi } from '@/services/api';
import toast from 'react-hot-toast';

interface Attachment {
  name: string;
  size: string;
  type: string;
  status: string;
}

interface ParsedProgram {
  name: string;
  platform: string;
  auth_level: string;
  scope_domains: string[];
  scope_excluded: string[];
  reward_tiers: Record<string, { min: number; max: number }>;
  severity_mapping: Record<string, string[]>;
  out_of_scope: string[];
  rules: string[];
  testing_header?: string;
  email_requirement?: string;
  response_times: Record<string, string>;
  attachments?: Attachment[];
  assets?: { name: string; max_severity: string }[];
}

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'pending' | 'uploading' | 'processing' | 'done' | 'error';
  credentials?: Array<{ type: string; value: string; confidence: string }>;
  certificate_info?: any;
  extracted_data?: {
    ips?: string[];
    domains?: string[];
    endpoints?: string[];
    notes?: string[];
    usernames?: string[];
  };
  error?: string;
}

export default function ProgramImport() {
  const [policyText, setPolicyText] = useState('');
  const [parsedProgram, setParsedProgram] = useState<ParsedProgram | null>(null);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [programName, setProgramName] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [allExtractedData, setAllExtractedData] = useState<{
    ips: Set<string>;
    domains: Set<string>;
    endpoints: Set<string>;
    notes: string[];
    credentials: Array<{ username: string; password: string }>;
  }>({
    ips: new Set(),
    domains: new Set(),
    endpoints: new Set(),
    notes: [],
    credentials: [],
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleParse = async () => {
    if (!policyText.trim()) {
      toast.error('Please paste program policy text first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await programsApi.parse({
        policy_text: policyText,
        use_ai: true,
      });

      if (res.data.success) {
        setParsedProgram(res.data.program);
        toast.success('Policy parsed successfully!');
      } else {
        setError(res.data.error || 'Failed to parse policy');
        toast.error('Failed to parse policy');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to parse policy');
      toast.error('Failed to parse policy');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const tempId = Date.now().toString();
    
    for (const file of Array.from(files)) {
      const uploadedFile: UploadedFile = {
        id: `${tempId}-${file.name}`,
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'uploading',
      };
      
      setUploadedFiles(prev => [...prev, uploadedFile]);

      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const res = await programsApi.uploadAttachmentDirect(formData);
        
        const processedFile: UploadedFile = {
          id: uploadedFile.id,
          name: file.name,
          size: file.size,
          type: file.type,
          status: 'done',
          credentials: res.data.credentials_found,
          certificate_info: res.data.certificate_info,
          extracted_data: {
            ips: extractIPs(res.data),
            domains: extractDomains(res.data),
            endpoints: extractEndpoints(res.data),
            notes: extractNotes(res.data),
            usernames: extractUsernames(res.data),
          },
        };
        
        setUploadedFiles(prev => prev.map(f => 
          f.id === uploadedFile.id ? processedFile : f
        ));
        
        mergeExtractedData(processedFile.extracted_data);
        toast.success(`Processed: ${file.name}`);
        
      } catch (err: any) {
        setUploadedFiles(prev => prev.map(f => 
          f.id === uploadedFile.id ? { ...f, status: 'error', error: err.message } : f
        ));
        toast.error(`Failed: ${file.name}`);
      }
    }
  };

  const extractIPs = (data: any): string[] => {
    const ips = new Set<string>();
    if (data.ai_extraction?.ip_addresses) {
      data.ai_extraction.ip_addresses.forEach((ip: string) => ips.add(ip));
    }
    const ipRegex = /\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b/g;
    const text = data.text_content || '';
    let match;
    while ((match = ipRegex.exec(text)) !== null) {
      ips.add(match[0]);
    }
    return Array.from(ips);
  };

  const extractDomains = (data: any): string[] => {
    const domains = new Set<string>();
    if (data.ai_extraction?.domains) {
      data.ai_extraction.domains.forEach((d: string) => domains.add(d));
    }
    const domainRegex = /\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b/g;
    const text = data.text_content || '';
    let match;
    while ((match = domainRegex.exec(text)) !== null) {
      if (!match[0].includes('example') && !match[0].includes('test')) {
        domains.add(match[0]);
      }
    }
    return Array.from(domains);
  };

  const extractEndpoints = (data: any): string[] => {
    const endpoints = new Set<string>();
    if (data.ai_extraction?.endpoints) {
      data.ai_extraction.endpoints.forEach((e: string) => endpoints.add(e));
    }
    const urlRegex = /https?:\/\/[^\s<>"{}|\\^`\[\]]+/g;
    const text = data.text_content || '';
    let match;
    while ((match = urlRegex.exec(text)) !== null) {
      endpoints.add(match[0]);
    }
    return Array.from(endpoints);
  };

  const extractNotes = (data: any): string[] => {
    const notes: string[] = [];
    if (data.ai_extraction?.notes) {
      data.ai_extraction.notes.forEach((n: string) => notes.push(n));
    }
    if (data.ai_extraction?.test_accounts) {
      data.ai_extraction.test_accounts.forEach((acc: any) => {
        if (acc.purpose) notes.push(acc.purpose);
      });
    }
    return notes;
  };

  const extractUsernames = (data: any): string[] => {
    const users = new Set<string>();
    if (data.ai_extraction?.test_accounts) {
      data.ai_extraction.test_accounts.forEach((acc: any) => {
        if (acc.username) users.add(acc.username);
      });
    }
    if (data.credentials_found) {
      data.credentials_found.forEach((c: any) => {
        if (c.type === 'username' || c.type === 'email') {
          users.add(c.value);
        }
      });
    }
    return Array.from(users);
  };

  const mergeExtractedData = (data: any) => {
    setAllExtractedData(prev => ({
      ips: new Set([...prev.ips, ...(data.ips || [])]),
      domains: new Set([...prev.domains, ...(data.domains || [])]),
      endpoints: new Set([...prev.endpoints, ...(data.endpoints || [])]),
      notes: [...prev.notes, ...(data.notes || [])],
      credentials: prev.credentials,
    }));
  };

  const removeUploadedFile = (id: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== id));
  };

  const handleImport = async () => {
    if (!parsedProgram) return;

    setImporting(true);

    try {
      await programsApi.create({
        name: parsedProgram.name,
        platform: parsedProgram.platform,
        auth_level: parsedProgram.auth_level,
        scope: {
          domains: parsedProgram.scope_domains,
          excluded: parsedProgram.scope_excluded,
        },
        reward_tiers: parsedProgram.reward_tiers,
        severity_mapping: parsedProgram.severity_mapping,
        out_of_scope: parsedProgram.out_of_scope,
        rules: parsedProgram.rules,
        program_policy: policyText,
        metadata: {
          testing_header: parsedProgram.testing_header,
          email_requirement: parsedProgram.email_requirement,
          response_times: parsedProgram.response_times,
          extracted_ips: Array.from(allExtractedData.ips),
          extracted_domains: Array.from(allExtractedData.domains),
          extracted_endpoints: Array.from(allExtractedData.endpoints),
          extracted_notes: allExtractedData.notes,
        },
      });

      for (const file of uploadedFiles.filter(f => f.status === 'done')) {
        try {
          const formData = new FormData();
          const blob = new Blob([await fetch(URL.createObjectURL(new globalThis.File([], file.name))).then(r => r.blob())], { type: file.type });
          formData.append('file', new globalThis.File([blob], file.name));
          await programsApi.uploadAttachmentDirect(formData);
        } catch (e) {
          console.error('Failed to re-upload file:', file.name);
        }
      }

      toast.success(`Program "${parsedProgram.name}" imported!`);
      setParsedProgram(null);
      setPolicyText('');
      setProgramName('');
      setUploadedFiles([]);
      setAllExtractedData({ ips: new Set(), domains: new Set(), endpoints: new Set(), notes: [], credentials: [] });
    } catch (err: any) {
      toast.error(err.message || 'Failed to import program');
    } finally {
      setImporting(false);
    }
  };

  const handleReset = () => {
    setPolicyText('');
    setParsedProgram(null);
    setError(null);
    setProgramName('');
    setUploadedFiles([]);
    setAllExtractedData({ ips: new Set(), domains: new Set(), endpoints: new Set(), notes: [], credentials: [] });
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      <GlassCard className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-secondary/10 rounded-lg">
            <Upload className="w-6 h-6 text-secondary" />
          </div>
          <div>
            <h1 className="font-display text-headline text-primary tracking-wider">
              IMPORT PROGRAM
            </h1>
            <p className="text-xs font-mono text-white/50 mt-1">
              Paste program policy text to auto-parse
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="data-label">Program Name (optional)</label>
            <input
              type="text"
              value={programName}
              onChange={(e) => setProgramName(e.target.value)}
              placeholder="e.g., DoorDash, Shopify, Uber"
              className="input"
            />
          </div>

          <div>
            <label className="data-label">Paste Program Policy Text</label>
            <textarea
              value={policyText}
              onChange={(e) => setPolicyText(e.target.value)}
              placeholder="Paste the full program policy text here...

Example:
DoorDash Bug Bounty Program
www.doordash.com in scope
Rewards: Critical $5000-$12000, High $1000-$5000
No automated scanners allowed"
              className="input min-h-[200px] font-mono text-sm resize-y"
            />
            <p className="text-xs text-white/40 mt-2">
              Paste the complete program policy text from HackerOne, Bugcrowd, etc.
            </p>
          </div>

          {error && (
            <div className="p-4 bg-error/10 border border-error/30 rounded-lg">
              <div className="flex items-center gap-2 text-error">
                <AlertCircle className="w-4 h-4" />
                <span className="font-mono text-sm">{error}</span>
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <CyberButton onClick={handleParse} loading={loading}>
              <span className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Parse Policy
              </span>
            </CyberButton>
            {parsedProgram && (
              <CyberButton variant="ghost" onClick={handleReset}>
                <span className="flex items-center gap-2">
                  <Trash2 className="w-4 h-4" />
                  Clear
                </span>
              </CyberButton>
            )}
          </div>
        </div>
      </GlassCard>

      {parsedProgram && (
        <GlassCard className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-tertiary/10 rounded-lg">
              <CheckCircle className="w-5 h-5 text-tertiary" />
            </div>
            <div>
              <h2 className="font-display text-xl text-tertiary">Parsed Program</h2>
              <p className="text-xs font-mono text-white/50">
                Review and confirm before importing
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="data-label mb-3">Basic Info</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-surface-50/50 rounded-lg">
                  <span className="text-xs font-mono text-white/60">Name</span>
                  <span className="text-sm font-mono text-white">{parsedProgram.name}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-surface-50/50 rounded-lg">
                  <span className="text-xs font-mono text-white/60">Platform</span>
                  <span className="text-sm font-mono text-secondary">{parsedProgram.platform}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-surface-50/50 rounded-lg">
                  <span className="text-xs font-mono text-white/60">Auth Level</span>
                  <span className="text-sm font-mono text-warning">{parsedProgram.auth_level}</span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="data-label mb-3 flex items-center gap-2">
                <DollarSign className="w-4 h-4" />
                Reward Tiers
              </h3>
              <div className="space-y-2">
                {Object.entries(parsedProgram.reward_tiers).map(([level, amounts]) => (
                  <div 
                    key={level}
                    className={`p-3 rounded-lg border ${
                      level === 'critical' ? 'bg-error/10 border-error/30' :
                      level === 'high' ? 'bg-warning/10 border-warning/30' :
                      level === 'medium' ? 'bg-secondary/10 border-secondary/30' :
                      'bg-tertiary/10 border-tertiary/30'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono uppercase">{level}</span>
                      <span className="text-sm font-mono text-white">
                        ${amounts.min.toLocaleString()} - ${amounts.max.toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="data-label mb-3 flex items-center gap-2">
                <Target className="w-4 h-4" />
                In-Scope Domains ({parsedProgram.scope_domains.length})
              </h3>
              <div className="max-h-[200px] overflow-y-auto space-y-1">
                {parsedProgram.scope_domains.length > 0 ? (
                  parsedProgram.scope_domains.map((domain, i) => (
                    <div key={i} className="p-2 bg-surface-50/50 rounded text-xs font-mono text-secondary">
                      {domain}
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-white/40 font-mono p-2">No domains found</div>
                )}
              </div>
            </div>

            <div>
              <h3 className="data-label mb-3 flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Excluded ({parsedProgram.scope_excluded.length})
              </h3>
              <div className="max-h-[200px] overflow-y-auto space-y-1">
                {parsedProgram.scope_excluded.length > 0 ? (
                  parsedProgram.scope_excluded.map((domain, i) => (
                    <div key={i} className="p-2 bg-surface-50/50 rounded text-xs font-mono text-white/50 line-through">
                      {domain}
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-white/40 font-mono p-2">No exclusions</div>
                )}
              </div>
            </div>

            {parsedProgram.testing_header && (
              <div className="md:col-span-2">
                <h3 className="data-label mb-3 flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  Testing Header
                </h3>
                <div className="p-3 bg-surface-50/50 rounded-lg">
                  <code className="text-xs font-mono text-tertiary">{parsedProgram.testing_header}</code>
                </div>
              </div>
            )}

            {parsedProgram.rules.length > 0 && (
              <div className="md:col-span-2">
                <h3 className="data-label mb-3">Rules ({parsedProgram.rules.length})</h3>
                <div className="max-h-[150px] overflow-y-auto space-y-1">
                  {parsedProgram.rules.slice(0, 10).map((rule, i) => (
                    <div key={i} className="flex items-start gap-2 p-2 bg-surface-50/50 rounded text-xs font-mono text-white/70">
                      <span className="text-tertiary">•</span>
                      <span>{rule}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </GlassCard>
      )}

      <GlassCard className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Paperclip className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="font-display text-lg text-primary">UPLOAD ATTACHMENTS</h2>
              <p className="text-xs font-mono text-white/50">
                Upload PDFs, certificates to extract IPs, domains, credentials
              </p>
            </div>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.pfx,.p12,.cer,.crt,.pem,.txt,.json"
            onChange={(e) => handleFileUpload(e.target.files)}
            className="hidden"
          />
          <CyberButton onClick={() => fileInputRef.current?.click()}>
            <Upload className="w-4 h-4 mr-2" />
            Choose Files
          </CyberButton>
        </div>

        {uploadedFiles.length > 0 && (
          <div className="space-y-3">
            {uploadedFiles.map((file) => (
              <div key={file.id} className="p-4 bg-surface-50/30 rounded-lg border border-white/10">
                <div className="flex items-center gap-3">
                  <FileCheck className="w-5 h-5 text-white/60" />
                  <div className="flex-1">
                    <div className="text-sm text-white font-mono">{file.name}</div>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-xs text-white/40">{formatSize(file.size)}</span>
                      {file.status === 'uploading' && (
                        <span className="flex items-center gap-1 text-xs text-warning">
                          <Loader2 className="w-3 h-3 animate-spin" /> Uploading...
                        </span>
                      )}
                      {file.status === 'done' && (
                        <span className="flex items-center gap-1 text-xs text-tertiary">
                          <CheckCircle className="w-3 h-3" /> Done
                        </span>
                      )}
                      {file.status === 'error' && (
                        <span className="flex items-center gap-1 text-xs text-error">
                          <AlertCircle className="w-3 h-3" /> {file.error}
                        </span>
                      )}
                    </div>
                  </div>
                  <button onClick={() => removeUploadedFile(file.id)} className="p-1 hover:bg-white/10 rounded">
                    <X className="w-4 h-4 text-white/40" />
                  </button>
                </div>

                {file.extracted_data && file.status === 'done' && (
                  <div className="mt-3 pt-3 border-t border-white/10 grid grid-cols-2 md:grid-cols-4 gap-3">
                    {file.extracted_data.ips && file.extracted_data.ips.length > 0 && (
                      <div className="bg-surface-50/30 p-2 rounded">
                        <div className="flex items-center gap-1 text-xs text-tertiary mb-1">
                          <Wifi className="w-3 h-3" /> IPs ({file.extracted_data.ips.length})
                        </div>
                        <div className="space-y-1">
                          {file.extracted_data.ips.slice(0, 3).map((ip, i) => (
                            <div key={i} className="text-xs font-mono text-white/70">{ip}</div>
                          ))}
                          {file.extracted_data.ips.length > 3 && (
                            <div className="text-xs text-white/40">+{file.extracted_data.ips.length - 3} more</div>
                          )}
                        </div>
                      </div>
                    )}
                    {file.extracted_data.domains && file.extracted_data.domains.length > 0 && (
                      <div className="bg-surface-50/30 p-2 rounded">
                        <div className="flex items-center gap-1 text-xs text-tertiary mb-1">
                          <Globe className="w-3 h-3" /> Domains ({file.extracted_data.domains.length})
                        </div>
                        <div className="space-y-1">
                          {file.extracted_data.domains.slice(0, 3).map((d, i) => (
                            <div key={i} className="text-xs font-mono text-white/70 truncate">{d}</div>
                          ))}
                          {file.extracted_data.domains.length > 3 && (
                            <div className="text-xs text-white/40">+{file.extracted_data.domains.length - 3} more</div>
                          )}
                        </div>
                      </div>
                    )}
                    {file.extracted_data.endpoints && file.extracted_data.endpoints.length > 0 && (
                      <div className="bg-surface-50/30 p-2 rounded">
                        <div className="flex items-center gap-1 text-xs text-tertiary mb-1">
                          <Server className="w-3 h-3" /> Endpoints ({file.extracted_data.endpoints.length})
                        </div>
                        <div className="space-y-1">
                          {file.extracted_data.endpoints.slice(0, 2).map((e, i) => (
                            <div key={i} className="text-xs font-mono text-white/70 truncate">{e}</div>
                          ))}
                          {file.extracted_data.endpoints.length > 2 && (
                            <div className="text-xs text-white/40">+{file.extracted_data.endpoints.length - 2} more</div>
                          )}
                        </div>
                      </div>
                    )}
                    {file.credentials && file.credentials.length > 0 && (
                      <div className="bg-surface-50/30 p-2 rounded">
                        <div className="flex items-center gap-1 text-xs text-tertiary mb-1">
                          <Key className="w-3 h-3" /> Credentials ({file.credentials.length})
                        </div>
                        <div className="text-xs text-white/40">Found in file</div>
                      </div>
                    )}
                  </div>
                )}

                {file.certificate_info && (
                  <div className="mt-3 pt-3 border-t border-white/10">
                    <div className="flex items-center gap-2 text-xs text-tertiary">
                      <FileCheck className="w-4 h-4" />
                      Certificate: {file.certificate_info.subject || file.certificate_info.certificates?.[0]?.subject || 'Parsed'}
                      {file.certificate_info.private_key_found && <span className="text-warning">(Has Private Key)</span>}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {(allExtractedData.ips.size > 0 || allExtractedData.domains.size > 0 || allExtractedData.endpoints.size > 0) && (
          <div className="mt-6 pt-6 border-t border-white/10">
            <h3 className="data-label mb-4 flex items-center gap-2">
              <Eye className="w-4 h-4" />
              EXTRACTED DATA SUMMARY
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-tertiary/10 border border-tertiary/30 rounded-lg p-4">
                <div className="flex items-center gap-2 text-tertiary mb-2">
                  <Wifi className="w-4 h-4" />
                  <span className="font-display text-sm">IP ADDRESSES</span>
                </div>
                <div className="space-y-1 max-h-[150px] overflow-y-auto">
                  {Array.from(allExtractedData.ips).map((ip, i) => (
                    <div key={i} className="text-xs font-mono text-white bg-surface-50/30 p-1 rounded">
                      {ip}
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-tertiary/10 border border-tertiary/30 rounded-lg p-4">
                <div className="flex items-center gap-2 text-tertiary mb-2">
                  <Globe className="w-4 h-4" />
                  <span className="font-display text-sm">DOMAINS</span>
                </div>
                <div className="space-y-1 max-h-[150px] overflow-y-auto">
                  {Array.from(allExtractedData.domains).map((d, i) => (
                    <div key={i} className="text-xs font-mono text-white bg-surface-50/30 p-1 rounded truncate">
                      {d}
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-tertiary/10 border border-tertiary/30 rounded-lg p-4">
                <div className="flex items-center gap-2 text-tertiary mb-2">
                  <Server className="w-4 h-4" />
                  <span className="font-display text-sm">ENDPOINTS</span>
                </div>
                <div className="space-y-1 max-h-[150px] overflow-y-auto">
                  {Array.from(allExtractedData.endpoints).map((e, i) => (
                    <div key={i} className="text-xs font-mono text-white bg-surface-50/30 p-1 rounded truncate">
                      {e}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </GlassCard>

      {parsedProgram && (
        <div className="flex gap-3">
          <CyberButton onClick={handleImport} loading={importing} variant="action" size="lg">
            <span className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Import Program
            </span>
          </CyberButton>
          <CyberButton variant="ghost" onClick={handleReset} size="lg">
            Cancel
          </CyberButton>
        </div>
      )}
    </div>
  );
}
