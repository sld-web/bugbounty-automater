import { useState, useRef } from 'react';
import { 
  Upload, 
  File, 
  FileText, 
  Video, 
  Key, 
  X, 
  Check, 
  AlertTriangle,
  Loader2,
  Eye,
  EyeOff,
  Save,
  Trash2,
  Sparkles,
  Lock,
} from 'lucide-react';
import { GlassCard, CyberButton } from '@/components/ui';
import { programsApi } from '@/services/api';
import toast from 'react-hot-toast';

interface ProcessedFile {
  filename: string;
  type: string;
  size: number;
  status: 'pending' | 'processing' | 'processing_ai' | 'processed' | 'error';
  ai_used?: boolean;
  credentials_found?: Array<{
    type: string;
    value: string;
    confidence: string;
    source?: string;
  }>;
  certificate_info?: any;
  ai_extraction?: {
    credentials?: Array<{ type: string; value: string; context?: string }>;
    certificates?: Array<{ format: string; subject: string; purpose?: string }>;
    ip_addresses?: string[];
    domains?: string[];
    endpoints?: string[];
    notes?: string[];
    test_accounts?: Array<{ username: string; password: string; purpose?: string }>;
  };
  warnings?: string[];
}

interface CredentialPreview {
  type: string;
  value: string;
  confidence: string;
  visible: boolean;
  save: boolean;
  source: string;
}

interface AttachmentUploadProps {
  programId: string;
  attachments?: Array<{
    name: string;
    size: string;
    type: string;
    status: string;
  }>;
  onComplete?: () => void;
}

export default function AttachmentUpload({ programId, attachments = [], onComplete }: AttachmentUploadProps) {
  const [files, setFiles] = useState<ProcessedFile[]>([]);
  const [uploading] = useState(false);
  const [credentials, setCredentials] = useState<CredentialPreview[]>([]);
  const [pfxPasswords, setPfxPasswords] = useState<Record<string, string>>({});
  const [showPfxPasswordModal, setShowPfxPasswordModal] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = event.target.files;
    if (!selectedFiles || selectedFiles.length === 0) return;

    const pendingPfx: Array<{ file: File }> = [];
    
    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      const ext = file.name.split('.').pop()?.toLowerCase();
      
      if (ext === 'pfx' || ext === 'p12') {
        pendingPfx.push({ file });
      } else {
        await processFile(file);
      }
    }

    for (const { file } of pendingPfx) {
      setShowPfxPasswordModal(file.name);
      const password = pfxPasswords[file.name];
      if (password !== undefined) {
        await processFile(file, password);
      }
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handlePfxPasswordSubmit = (filename: string, password: string) => {
    setPfxPasswords(prev => ({ ...prev, [filename]: password }));
    setShowPfxPasswordModal(null);
    const fileInput = fileInputRef.current;
    if (fileInput?.files) {
      const file = Array.from(fileInput.files).find(f => f.name === filename);
      if (file) {
        processFile(file, password);
      }
    }
  };

  const processFile = async (file: File, pfxPassword?: string) => {
    const fileInfo: ProcessedFile = {
      filename: file.name,
      type: file.type,
      size: file.size,
      status: 'processing',
    };

    setFiles(prev => [...prev, fileInfo]);

    try {
      const res = await programsApi.uploadAttachment(programId, file, pfxPassword);
      
      const newFileInfo: ProcessedFile = {
        ...fileInfo,
        ...res.data,
        status: res.data.ai_used ? 'processing_ai' : 'processed',
      };
      
      setFiles(prev => prev.map(f => 
        f.filename === file.name 
          ? newFileInfo
          : f
      ));

      if (res.data.ai_used) {
        setTimeout(() => {
          setFiles(prev => prev.map(f => 
            f.filename === file.name 
              ? { ...f, status: 'processed' as const }
              : f
          ));
        }, 2000);
      }

      if (res.data.credentials_found && res.data.credentials_found.length > 0) {
        const newCreds = res.data.credentials_found.map((c: any) => ({
          ...c,
          visible: false,
          save: true,
          source: c.source || 'regex',
        }));
        setCredentials(prev => [...prev, ...newCreds]);
        toast.success(`Found ${res.data.credentials_found.length} credential(s) in ${file.name}`);
      }

      if (res.data.certificate_info) {
        toast.success(`Certificate parsed: ${file.name}`);
      }

      if (res.data.ai_used) {
        toast.success(`AI extraction completed for ${file.name}`);
      }

    } catch (err: any) {
      setFiles(prev => prev.map(f => 
        f.filename === file.name 
          ? { ...f, status: 'error', warnings: [err.message] }
          : f
      ));
      toast.error(`Failed to process ${file.name}`);
    }
  };

  const toggleCredentialVisibility = (index: number) => {
    setCredentials(prev => prev.map((c, i) => 
      i === index ? { ...c, visible: !c.visible } : c
    ));
  };

  const toggleCredentialSave = (index: number) => {
    setCredentials(prev => prev.map((c, i) => 
      i === index ? { ...c, save: !c.save } : c
    ));
  };

  const handleSaveCredentials = async () => {
    const toSave = credentials.filter(c => c.save);
    
    if (toSave.length === 0) {
      toast.error('No credentials selected to save');
      return;
    }

    try {
      for (const cred of toSave) {
        await programsApi.addCredential(programId, {
          name: `${cred.type}: ${cred.value.substring(0, 20)}...`,
          type: cred.type,
          username: cred.type === 'email' ? cred.value : undefined,
          password: cred.type === 'password' ? cred.value : undefined,
          metadata: { confidence: cred.confidence, source: cred.source },
          source: 'attachment_upload',
        });
      }

      toast.success(`Saved ${toSave.length} credential(s) to vault`);
      setCredentials([]);
      onComplete?.();
    } catch (err) {
      toast.error('Failed to save credentials');
    }
  };

  const removeFile = (filename: string) => {
    setFiles(prev => prev.filter(f => f.filename !== filename));
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (ext === 'pdf' || ext === 'doc' || ext === 'docx') return FileText;
    if (ext === 'mp4' || ext === 'avi' || ext === 'mov') return Video;
    if (ext === 'pfx' || ext === 'p12' || ext === 'cer' || ext === 'crt') return Key;
    return File;
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getStatusBadge = (file: ProcessedFile) => {
    if (file.status === 'processing') {
      return (
        <span className="flex items-center gap-1 text-xs text-white/60">
          <Loader2 className="w-3 h-3 animate-spin" />
          Extracting text...
        </span>
      );
    }
    if (file.status === 'processing_ai') {
      return (
        <span className="flex items-center gap-1 text-xs text-primary">
          <Sparkles className="w-3 h-3 animate-pulse" />
          AI analyzing...
        </span>
      );
    }
    if (file.status === 'processed') {
      const credCount = file.credentials_found?.length || 0;
      const hasCert = !!file.certificate_info;
      return (
        <span className="flex items-center gap-1 text-xs text-tertiary">
          <Check className="w-3 h-3" />
          {file.ai_used && <Sparkles className="w-3 h-3" />}
          {credCount} cred{credCount !== 1 ? 's' : ''}{hasCert ? ', cert' : ''}
        </span>
      );
    }
    if (file.status === 'error') {
      return (
        <span className="flex items-center gap-1 text-xs text-error">
          <AlertTriangle className="w-3 h-3" />
          Failed
        </span>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      <GlassCard className="p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-display text-sm text-primary tracking-wider">
              UPLOAD ATTACHMENTS
            </h3>
            <p className="text-xs text-white/40 mt-1">
              Upload PDF, certificates, or documents to extract credentials
            </p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.pfx,.p12,.cer,.crt,.pem,.txt,.json"
            onChange={handleFileSelect}
            className="hidden"
          />
          <CyberButton 
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            size="sm"
          >
            {uploading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Upload className="w-4 h-4 mr-2" />
            )}
            Choose Files
          </CyberButton>
        </div>

        {files.length > 0 && (
          <div className="space-y-3">
            {files.map((file, index) => {
              const Icon = getFileIcon(file.filename);
              return (
                <div key={index} className="flex items-center gap-3 p-3 bg-surface-50/30 rounded-lg">
                  <Icon className="w-5 h-5 text-white/60" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-white truncate font-mono">
                      {file.filename}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-white/40">
                        {formatSize(file.size)}
                      </span>
                      {getStatusBadge(file)}
                    </div>
                    {file.warnings && file.warnings.length > 0 && (
                      <div className="mt-1 text-xs text-warning">
                        {file.warnings[0]}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => removeFile(file.filename)}
                    className="p-1 hover:bg-white/10 rounded"
                  >
                    <X className="w-4 h-4 text-white/40" />
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {attachments.length > 0 && (
          <div className="mt-4 pt-4 border-t border-white/10">
            <p className="text-xs text-white/40 mb-2">
              Expected from program policy:
            </p>
            <div className="flex flex-wrap gap-2">
              {attachments.map((att, i) => (
                <span 
                  key={i}
                  className="px-2 py-1 bg-warning/10 border border-warning/30 rounded text-xs text-warning"
                >
                  {att.name} ({att.size})
                </span>
              ))}
            </div>
          </div>
        )}
      </GlassCard>

      {credentials.length > 0 && (
        <GlassCard className="p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-display text-sm text-tertiary tracking-wider">
                EXTRACTED CREDENTIALS
              </h3>
              <p className="text-xs text-white/40 mt-1">
                Review and save credentials to vault
              </p>
            </div>
            <CyberButton onClick={handleSaveCredentials} size="sm">
              <Save className="w-4 h-4 mr-2" />
              Save {credentials.filter(c => c.save).length} Credential(s)
            </CyberButton>
          </div>

          <div className="space-y-2">
            {credentials.map((cred, index) => (
              <div 
                key={index}
                className="flex items-center gap-3 p-3 bg-surface-50/30 rounded-lg"
              >
                <input
                  type="checkbox"
                  checked={cred.save}
                  onChange={() => toggleCredentialSave(index)}
                  className="w-4 h-4 accent-primary"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-white/60 uppercase">
                      {cred.type}
                    </span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      cred.confidence === 'high' 
                        ? 'bg-tertiary/20 text-tertiary' 
                        : 'bg-warning/20 text-warning'
                    }`}>
                      {cred.confidence}
                    </span>
                    {cred.source === 'ai_extraction' && (
                      <span className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-primary/20 text-primary">
                        <Sparkles className="w-3 h-3" />
                        AI
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <code className="text-sm text-white font-mono">
                      {cred.visible ? cred.value : '•'.repeat(Math.min(cred.value.length, 20))}
                    </code>
                    <button
                      onClick={() => toggleCredentialVisibility(index)}
                      className="p-1 hover:bg-white/10 rounded"
                    >
                      {cred.visible ? (
                        <EyeOff className="w-4 h-4 text-white/40" />
                      ) : (
                        <Eye className="w-4 h-4 text-white/40" />
                      )}
                    </button>
                  </div>
                </div>
                <button
                  onClick={() => setCredentials(prev => prev.filter((_, i) => i !== index))}
                  className="p-1 hover:bg-error/20 rounded text-error/60 hover:text-error"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {showPfxPasswordModal && (
        <PfxPasswordModal
          filename={showPfxPasswordModal}
          onSubmit={(password) => handlePfxPasswordSubmit(showPfxPasswordModal, password)}
          onCancel={() => setShowPfxPasswordModal(null)}
        />
      )}
    </div>
  );
}

function PfxPasswordModal({ filename, onSubmit, onCancel }: {
  filename: string;
  onSubmit: (password: string) => void;
  onCancel: () => void;
}) {
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <GlassCard className="p-6 max-w-md w-full mx-4">
        <div className="flex items-center gap-3 mb-4">
          <Lock className="w-6 h-6 text-warning" />
          <h3 className="font-display text-lg text-white">PFX Password Required</h3>
        </div>
        
        <p className="text-sm text-white/60 mb-4">
          The file <span className="font-mono text-primary">{filename}</span> requires a password to decrypt.
        </p>
        
        <div className="relative mb-4">
          <input
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter PFX password"
            className="w-full px-4 py-2 pr-10 bg-surface-50/50 border border-white/20 rounded text-white placeholder-white/40 focus:border-primary focus:outline-none"
            onKeyDown={(e) => e.key === 'Enter' && onSubmit(password)}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white"
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 bg-white/10 text-white/60 rounded hover:bg-white/20 transition"
          >
            Cancel
          </button>
          <button
            onClick={() => onSubmit(password)}
            className="flex-1 px-4 py-2 bg-primary text-white rounded hover:bg-primary/80 transition"
          >
            Decrypt
          </button>
        </div>
      </GlassCard>
    </div>
  );
}
