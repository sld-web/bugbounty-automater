import { useState, useRef } from 'react';
import { 
  ChevronRight,
  ChevronLeft,
  Upload,
  FileText,
  Brain,
  CheckCircle,
  AlertCircle,
  X,
  ChevronDown,
  ChevronUp,
  Shield,
  Target,
  DollarSign,
  Wrench,
  Info,
  Loader2,
  Lock,
  Eye,
  Edit2,
  Server,
  Globe,
  Wifi,
  Check,
  File
} from 'lucide-react';
import { GlassCard, CyberButton } from '@/components/ui';
import { programsApi } from '@/services/api';
import toast from 'react-hot-toast';

interface UploadedFile {
  id: string;
  name: string;
  content: string;
  size: number;
  type: string;
  needsPassword?: boolean;
  password?: string;
}

interface ToolSuggestion {
  name: string;
  available: boolean;
  reason: string;
}

interface TargetAnalysis {
  name: string;
  type: string;
  description: string | null;
  suggested_tools: ToolSuggestion[];
  scope_domains: string[];
  scope_ips: string[];
  excluded: string[];
  reward_tiers?: Record<string, { min: number; max: number }>;
}

interface AnalysisResult {
  introduction: string;
  rules: string[];
  targets: TargetAnalysis[];
  rewards_summary: Record<string, { min: number; max: number }>;
  out_of_scope: string[];
  testing_notes: string | null;
  severity_mapping: Record<string, string[]>;
}

type Step = 'text' | 'uploads' | 'analyze' | 'review';

export default function ProgramIngestionWizard() {
  const [currentStep, setCurrentStep] = useState<Step>('text');
  const [policyText, setPolicyText] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [editableResult, setEditableResult] = useState<AnalysisResult | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [expandedTargets, setExpandedTargets] = useState<Set<number>>(new Set([0]));
  const [pfxPasswordModal, setPfxPasswordModal] = useState<{fileId: string; filename: string} | null>(null);
  const [pfxPassword, setPfxPassword] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const fileRefs = useRef<Map<string, File>>(new Map());

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setIsUploading(true);

    const newFiles: UploadedFile[] = [];
    for (const file of Array.from(files)) {
      const ext = file.name.split('.').pop()?.toLowerCase() || '';
      const isPfx = ['pfx', 'p12'].includes(ext);
      const fileId = Date.now().toString() + Math.random().toString();
      
      fileRefs.current.set(fileId, file);
      
      newFiles.push({
        id: fileId,
        name: file.name,
        content: '',
        size: file.size,
        type: file.type || ext || 'unknown',
        needsPassword: isPfx,
        password: '',
      });
    }

    setUploadedFiles(prev => [...prev, ...newFiles]);
    setIsUploading(false);
    toast.success(`${files.length} file(s) uploaded`);
  };

  const removeFile = (id: string) => {
    fileRefs.current.delete(id);
    setUploadedFiles(prev => prev.filter(f => f.id !== id));
  };

  const handlePfxPasswordSubmit = () => {
    if (pfxPasswordModal) {
      setUploadedFiles(prev => prev.map(f => 
        f.id === pfxPasswordModal.fileId 
          ? { ...f, password: pfxPassword }
          : f
      ));
    }
    setPfxPasswordModal(null);
    setPfxPassword('');
  };

  const handleAnalyze = async () => {
    if (!policyText.trim() && uploadedFiles.length === 0) {
      toast.error('Please paste program text or upload files first');
      return;
    }

    setIsAnalyzing(true);

    console.log('Starting analysis with', uploadedFiles.length, 'files');
    
    const formData = new FormData();
    formData.append('policy_text', policyText);
    
    for (const uploadedFile of uploadedFiles) {
      const file = fileRefs.current.get(uploadedFile.id);
      if (file) {
        console.log('Adding file from ref:', uploadedFile.name);
        formData.append('files', file);
        if (uploadedFile.needsPassword && uploadedFile.password) {
          formData.append(`pfx_password_${uploadedFile.name}`, uploadedFile.password);
        }
      }
    }

    console.log('Sending request to /api/programs/analyze');
    setCurrentStep('analyze');

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000);

    try {
      const res = await fetch('/api/programs/analyze', {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      console.log('Response status:', res.status);
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      
      const text = await res.text();
      console.log('Response text length:', text.length);
      
      if (!text.trim()) {
        throw new Error('Empty response from server');
      }
      
      const result = JSON.parse(text);
      console.log('Analysis result:', result);
      
      if (result.error) {
        toast.error(result.error);
        setCurrentStep('text');
      } else {
        setAnalysisResult(result);
        setEditableResult(result);
        setCurrentStep('review');
        toast.success('Analysis complete!');
      }
    } catch (err: any) {
      console.error('Analysis error:', err);
      if (err.name === 'AbortError') {
        toast.error('Analysis timed out after 2 minutes');
      } else {
        toast.error('Analysis failed: ' + err.message);
      }
      setCurrentStep('text');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleEditToggle = () => {
    if (isEditing && editableResult) {
      setAnalysisResult(editableResult);
    }
    setIsEditing(!isEditing);
  };

  const updateEditableResult = (field: string, value: any) => {
    if (!editableResult) return;
    setEditableResult({
      ...editableResult,
      [field]: value
    });
  };

  const toggleTargetExpanded = (index: number) => {
    const newExpanded = new Set(expandedTargets);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedTargets(newExpanded);
  };

  const handleCreateProgram = async () => {
    if (!analysisResult) return;

    try {
      const allDomains = analysisResult.targets.flatMap(t => t.scope_domains || []);
      
      const targetConfigs = analysisResult.targets.map(t => ({
        name: t.name,
        type: t.type || 'webapp',
        description: t.description || '',
        scope_domains: t.scope_domains || [],
        scope_ips: t.scope_ips || [],
        excluded: t.excluded || [],
        suggested_tools: t.suggested_tools || [],
      }));
      
      const response = await programsApi.create({
        name: analysisResult.targets[0]?.name || 'Imported Program',
        platform: 'hackerone',
        scope: {
          domains: [...new Set(allDomains)],
          excluded: analysisResult.out_of_scope || [],
        },
        scope_domains: [...new Set(allDomains)],
        scope_excluded: analysisResult.out_of_scope || [],
        reward_tiers: analysisResult.rewards_summary || {},
        severity_mapping: analysisResult.severity_mapping || {},
        priority_areas: analysisResult.targets.map(t => t.name),
        target_configs: targetConfigs,
        out_of_scope: analysisResult.out_of_scope || [],
        raw_policy: policyText,
        special_requirements: {
          testing_notes: analysisResult.testing_notes,
          rules: analysisResult.rules,
        },
      });

      toast.success('Program created successfully!');
      
      setTimeout(() => {
        window.location.href = `/programs/${response.data.id}`;
      }, 1000);
    } catch (err: any) {
      toast.error('Failed to create program: ' + err.message);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const steps: { key: Step; label: string; icon: any }[] = [
    { key: 'text', label: 'Policy Text', icon: FileText },
    { key: 'uploads', label: 'Uploads', icon: Upload },
    { key: 'analyze', label: 'AI Analysis', icon: Brain },
    { key: 'review', label: 'Review', icon: CheckCircle },
  ];

  const currentStepIndex = steps.findIndex(s => s.key === currentStep);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl text-primary tracking-wider">
          PROGRAM INGESTION WIZARD
        </h1>
        <div className="flex items-center gap-2">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = index === currentStepIndex;
            const isComplete = index < currentStepIndex;
            return (
              <div key={step.key} className="flex items-center">
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
                  isActive ? 'bg-primary text-white' :
                  isComplete ? 'bg-tertiary/20 text-tertiary' :
                  'bg-surface-50/20 text-white/40'
                }`}>
                  <Icon className="w-4 h-4" />
                  <span className="text-sm font-mono hidden sm:inline">{step.label}</span>
                </div>
                {index < steps.length - 1 && (
                  <ChevronRight className="w-4 h-4 text-white/20 mx-1" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {currentStep === 'text' && (
        <GlassCard className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <FileText className="w-5 h-5 text-primary" />
            <h2 className="font-display text-lg text-primary">STEP 1: PASTE PROGRAM POLICY TEXT</h2>
          </div>
          <p className="text-sm text-white/60 mb-4">
            Paste the complete bug bounty program policy text. This will be shown as-is for your review.
          </p>
          <textarea
            value={policyText}
            onChange={(e) => setPolicyText(e.target.value)}
            placeholder="Paste the full program policy here...

Example:
Cloud Software Group Bug Bounty Program
https://hackerone.com/cloudsoftwaregroup

Scope:
- NetScaler AAA
- NetScaler Gateway

Rewards:
- Critical: $10,000
- High: $4,000
..."
            className="input min-h-[400px] font-mono text-sm"
          />
          <div className="flex items-center justify-between mt-4">
            <div className="text-xs text-white/40">
              {policyText.length} characters
            </div>
            <div className="flex gap-2">
              <CyberButton 
                onClick={() => setCurrentStep('uploads')}
                disabled={!policyText.trim() && uploadedFiles.length === 0}
              >
                Next: Uploads
                <ChevronRight className="w-4 h-4 ml-2" />
              </CyberButton>
            </div>
          </div>
        </GlassCard>
      )}

      {currentStep === 'uploads' && (
        <div className="space-y-4">
          <GlassCard className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <Upload className="w-5 h-5 text-primary" />
              <h2 className="font-display text-lg text-primary">STEP 2: UPLOAD ATTACHMENTS (OPTIONAL)</h2>
            </div>
            <p className="text-sm text-white/60 mb-4">
              Upload any additional files: PDFs, text files, certificates, etc. These will be extracted and analyzed together with the policy text.
            </p>
            
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.txt,.md,.json,.xml,.log,.csv,.pfx,.p12,.cer,.crt,.pem"
              onChange={(e) => handleFileUpload(e.target.files)}
              className="hidden"
            />
            
            <CyberButton onClick={() => fileInputRef.current?.click()} disabled={isUploading}>
              {isUploading ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Upload className="w-4 h-4 mr-2" />
              )}
              Choose Files
            </CyberButton>

            {uploadedFiles.length > 0 && (
              <div className="mt-6 space-y-3">
                <h3 className="text-sm font-mono text-tertiary">UPLOADED FILES ({uploadedFiles.length})</h3>
                {uploadedFiles.map((file) => (
                  <div key={file.id} className="bg-surface-50/30 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between p-3 border-b border-white/10">
                      <div className="flex items-center gap-3">
                        {file.needsPassword ? (
                          <Lock className="w-4 h-4 text-warning" />
                        ) : (
                          <File className="w-4 h-4 text-white/60" />
                        )}
                        <div>
                          <div className="text-sm text-white font-mono">{file.name}</div>
                          <div className="flex items-center gap-2">
                            <div className="text-xs text-white/40">{formatSize(file.size)} • {file.type}</div>
                            {file.needsPassword && (
                              <span className="px-2 py-0.5 bg-warning/20 text-warning text-xs rounded">
                                Encrypted
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <button 
                        onClick={() => removeFile(file.id)}
                        className="p-1 hover:bg-white/10 rounded text-white/40 hover:text-error"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                    
                    {file.needsPassword && (
                      <div className="p-3 bg-warning/10 border-b border-white/10">
                        <div className="flex items-center gap-2 mb-2">
                          <Lock className="w-4 h-4 text-warning" />
                          <span className="text-sm text-warning">Password Required</span>
                        </div>
                        {file.password ? (
                          <div className="flex items-center gap-2">
                            <Check className="w-4 h-4 text-tertiary" />
                            <span className="text-xs text-tertiary">Password set</span>
                          </div>
                        ) : (
                          <button
                            onClick={() => setPfxPasswordModal({ fileId: file.id, filename: file.name })}
                            className="px-3 py-1 bg-warning/20 text-warning text-xs rounded hover:bg-warning/30 transition"
                          >
                            Set Password
                          </button>
                        )}
                      </div>
                    )}
                    
                    {file.content && (
                      <div className="max-h-[200px] overflow-y-auto p-3">
                        <pre className="text-xs text-white/70 font-mono whitespace-pre-wrap">
                          {file.content.substring(0, 1000)}
                          {file.content.length > 1000 && '...'}
                        </pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </GlassCard>

          <div className="flex justify-between">
            <CyberButton variant="ghost" onClick={() => setCurrentStep('text')}>
              <ChevronLeft className="w-4 h-4 mr-2" />
              Back
            </CyberButton>
            <CyberButton onClick={handleAnalyze} disabled={isAnalyzing}>
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Brain className="w-4 h-4 mr-2" />
                  Analyze with AI
                </>
              )}
            </CyberButton>
          </div>
        </div>
      )}

      {currentStep === 'analyze' && (
        <GlassCard className="p-12 text-center">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-16 h-16 text-primary animate-spin" />
            <h2 className="font-display text-xl text-primary">AI IS ANALYZING YOUR PROGRAM</h2>
            <p className="text-white/60 max-w-md">
              Extracting structured information from policy text and attachments...
            </p>
            <div className="mt-4 p-4 bg-surface-50/20 rounded-lg max-w-lg">
              <h4 className="text-xs text-white/40 mb-2">Processing:</h4>
              <ul className="text-sm text-white/70 space-y-1 text-left">
                <li>✓ Policy text ({policyText.length} chars)</li>
                {uploadedFiles.map(f => (
                  <li key={f.id}>✓ {f.name}</li>
                ))}
              </ul>
            </div>
          </div>
        </GlassCard>
      )}

      {currentStep === 'review' && analysisResult && (
        <div className="space-y-4">
          <GlassCard className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-6 h-6 text-tertiary" />
                <div>
                  <h2 className="font-display text-lg text-tertiary">AI ANALYSIS RESULTS</h2>
                  <p className="text-xs text-white/60">Review and edit the extracted information</p>
                </div>
              </div>
              <div className="flex gap-2">
                <CyberButton variant="ghost" onClick={handleEditToggle}>
                  {isEditing ? (
                    <>
                      <Eye className="w-4 h-4 mr-2" />
                      Preview
                    </>
                  ) : (
                    <>
                      <Edit2 className="w-4 h-4 mr-2" />
                      Edit
                    </>
                  )}
                </CyberButton>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="data-label flex items-center gap-2">
                  <Info className="w-4 h-4" />
                  INTRODUCTION
                </h3>
                {isEditing ? (
                  <textarea
                    value={analysisResult.introduction}
                    onChange={(e) => updateEditableResult('introduction', e.target.value)}
                    className="input min-h-[100px] text-sm"
                  />
                ) : (
                  <div className="p-3 bg-surface-50/30 rounded-lg text-sm text-white/80">
                    {analysisResult.introduction}
                  </div>
                )}
              </div>

              <div>
                <h3 className="data-label flex items-center gap-2">
                  <DollarSign className="w-4 h-4" />
                  REWARDS
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(analysisResult.rewards_summary || {}).map(([level, amounts]) => (
                    <div key={level} className={`p-3 rounded-lg border ${
                      level === 'critical' ? 'bg-error/10 border-error/30' :
                      level === 'high' ? 'bg-warning/10 border-warning/30' :
                      level === 'medium' ? 'bg-secondary/10 border-secondary/30' :
                      'bg-tertiary/10 border-tertiary/30'
                    }`}>
                      <div className="text-xs font-mono uppercase text-white/60">{level}</div>
                      <div className="text-lg font-mono text-white">
                        ${amounts.min.toLocaleString()}{amounts.max > amounts.min && ` - $${amounts.max.toLocaleString()}`}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="data-label flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  RULES ({analysisResult.rules?.length || 0})
                </h3>
                <div className="max-h-[200px] overflow-y-auto space-y-1">
                  {analysisResult.rules?.map((rule, i) => (
                    <div key={i} className="p-2 bg-surface-50/30 rounded text-xs text-white/70 flex items-start gap-2">
                      <span className="text-tertiary">{i + 1}.</span>
                      <span>{rule}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="data-label flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  OUT OF SCOPE ({analysisResult.out_of_scope?.length || 0})
                </h3>
                <div className="max-h-[200px] overflow-y-auto space-y-1">
                  {analysisResult.out_of_scope?.map((item, i) => (
                    <div key={i} className="p-2 bg-error/10 border border-error/20 rounded text-xs text-white/60 line-through">
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {analysisResult.testing_notes && (
              <div className="mt-6 pt-6 border-t border-white/10">
                <h3 className="data-label flex items-center gap-2">
                  <Info className="w-4 h-4" />
                  TESTING NOTES
                </h3>
                <div className="p-3 bg-tertiary/10 border border-tertiary/30 rounded-lg text-sm text-white/80">
                  {analysisResult.testing_notes}
                </div>
              </div>
            )}
          </GlassCard>

          <GlassCard className="p-6">
            <h3 className="data-label flex items-center gap-2 mb-4">
              <Target className="w-4 h-4" />
              TARGETS ({analysisResult.targets?.length || 0})
            </h3>
            <div className="space-y-4">
              {analysisResult.targets?.map((target, index) => (
                <div key={index} className="bg-surface-50/30 rounded-lg overflow-hidden">
                  <div 
                    className="flex items-center justify-between p-4 cursor-pointer hover:bg-white/5"
                    onClick={() => toggleTargetExpanded(index)}
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-primary/10 rounded-lg">
                        <Server className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <div className="text-white font-mono">{target.name}</div>
                        <div className="flex items-center gap-2 text-xs text-white/50">
                          <span className="px-2 py-0.5 bg-surface-50 rounded">{target.type}</span>
                          <span>{(target.scope_domains || []).length} domains</span>
                          <span>{(target.scope_ips || []).length} IPs</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex gap-1">
                        {target.suggested_tools?.slice(0, 3).map((tool, i) => (
                          <span key={i} className={`px-2 py-0.5 text-xs rounded ${
                            tool.available ? 'bg-tertiary/20 text-tertiary' : 'bg-warning/20 text-warning'
                          }`}>
                            {tool.name}
                          </span>
                        ))}
                        {(target.suggested_tools?.length || 0) > 3 && (
                          <span className="px-2 py-0.5 text-xs rounded bg-surface-50 text-white/60">
                            +{target.suggested_tools.length - 3}
                          </span>
                        )}
                      </div>
                      {expandedTargets.has(index) ? (
                        <ChevronUp className="w-4 h-4 text-white/40" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-white/40" />
                      )}
                    </div>
                  </div>

                  {expandedTargets.has(index) && (
                    <div className="p-4 border-t border-white/10 space-y-4">
                      {target.description && (
                        <div>
                          <h4 className="text-xs text-white/50 mb-1">Description</h4>
                          <p className="text-sm text-white/80">{target.description}</p>
                        </div>
                      )}

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {(target.scope_domains || []).length > 0 && (
                          <div>
                            <h4 className="text-xs text-white/50 mb-2 flex items-center gap-1">
                              <Globe className="w-3 h-3" />
                              In-Scope Domains
                            </h4>
                            <div className="flex flex-wrap gap-1">
                              {target.scope_domains.map((d, i) => (
                                <span key={i} className="px-2 py-1 bg-secondary/10 border border-secondary/30 rounded text-xs text-secondary">
                                  {d}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {(target.scope_ips || []).length > 0 && (
                          <div>
                            <h4 className="text-xs text-white/50 mb-2 flex items-center gap-1">
                              <Wifi className="w-3 h-3" />
                              In-Scope IPs
                            </h4>
                            <div className="flex flex-wrap gap-1">
                              {target.scope_ips.map((ip, i) => (
                                <span key={i} className="px-2 py-1 bg-tertiary/10 border border-tertiary/30 rounded text-xs text-tertiary font-mono">
                                  {ip}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {(target.excluded || []).length > 0 && (
                        <div>
                          <h4 className="text-xs text-white/50 mb-2">Excluded</h4>
                          <div className="flex flex-wrap gap-1">
                            {target.excluded.map((e, i) => (
                              <span key={i} className="px-2 py-1 bg-error/10 border border-error/30 rounded text-xs text-error line-through">
                                {e}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      <div>
                        <h4 className="text-xs text-white/50 mb-2 flex items-center gap-1">
                          <Wrench className="w-3 h-3" />
                          Suggested Tools
                        </h4>
                        <div className="space-y-2">
                          {target.suggested_tools?.map((tool, i) => (
                            <div key={i} className="flex items-center gap-3 p-2 bg-surface-50/30 rounded">
                              <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                                tool.available ? 'bg-tertiary/20 text-tertiary' : 'bg-warning/20 text-warning'
                              }`}>
                                {tool.available ? <Check className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                              </div>
                              <div className="flex-1">
                                <div className="text-sm text-white font-mono">{tool.name}</div>
                                <div className="text-xs text-white/50">{tool.reason}</div>
                              </div>
                              <span className={`text-xs px-2 py-0.5 rounded ${
                                tool.available ? 'bg-tertiary/20 text-tertiary' : 'bg-warning/20 text-warning'
                              }`}>
                                {tool.available ? 'Available' : 'Not Installed'}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </GlassCard>

          <div className="flex justify-between">
            <CyberButton variant="ghost" onClick={() => setCurrentStep('uploads')}>
              <ChevronLeft className="w-4 h-4 mr-2" />
              Back to Uploads
            </CyberButton>
            <CyberButton onClick={handleCreateProgram} variant="action" size="lg">
              <CheckCircle className="w-4 h-4 mr-2" />
              Create Program
            </CyberButton>
          </div>
        </div>
      )}

      {pfxPasswordModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <GlassCard className="p-6 max-w-md w-full mx-4">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-warning/10 rounded-lg">
                <Lock className="w-6 h-6 text-warning" />
              </div>
              <div>
                <h3 className="font-display text-lg text-warning">PFX Password Required</h3>
                <p className="text-xs text-white/50">This certificate file is encrypted</p>
              </div>
            </div>
            
            <p className="text-sm text-white/70 mb-4">
              The file <span className="font-mono text-secondary">{pfxPasswordModal.filename}</span> requires a password to decrypt.
            </p>
            
            <div className="relative mb-4">
              <input
                type={pfxPassword ? 'text' : 'password'}
                value={pfxPassword}
                onChange={(e) => setPfxPassword(e.target.value)}
                placeholder="Enter password"
                className="w-full px-4 py-2 pr-10 bg-surface-50/50 border border-white/20 rounded text-white placeholder-white/40 focus:border-warning focus:outline-none"
                onKeyDown={(e) => e.key === 'Enter' && handlePfxPasswordSubmit()}
                autoFocus
              />
              <button
                type="button"
                onClick={() => setPfxPassword(pfxPassword ? '' : '1234')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white"
                title="Try '1234' as password"
              >
                <Eye className="w-4 h-4" />
              </button>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => setPfxPasswordModal(null)}
                className="flex-1 px-4 py-2 bg-white/10 text-white/60 rounded hover:bg-white/20 transition"
              >
                Cancel
              </button>
              <button
                onClick={handlePfxPasswordSubmit}
                className="flex-1 px-4 py-2 bg-warning text-white rounded hover:bg-warning/80 transition"
              >
                Use Password
              </button>
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  );
}
