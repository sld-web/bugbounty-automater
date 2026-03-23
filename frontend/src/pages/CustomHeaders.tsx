import { useState, useEffect } from 'react';
import { 
  Plus, Trash2, Key, Shield, RefreshCw
} from 'lucide-react';
import { GlassCard, CyberButton } from '@/components/ui';
import { headersApi } from '@/services/api';
import toast from 'react-hot-toast';

interface CustomHeader {
  name: string;
  value: string;
  source: string;
  enabled: boolean;
}

export default function CustomHeaders() {
  const [headers, setHeaders] = useState<CustomHeader[]>([]);
  const [loading, setLoading] = useState(true);
  const [newHeader, setNewHeader] = useState({ name: '', value: '', source: 'manual' });
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    loadHeaders();
  }, []);

  const loadHeaders = async () => {
    try {
      setLoading(true);
      const res = await headersApi.list();
      setHeaders(res.data.headers || res.data || []);
    } catch (error) {
      toast.error('Failed to load headers');
    } finally {
      setLoading(false);
    }
  };

  const addHeader = async () => {
    if (!newHeader.name || !newHeader.value) {
      toast.error('Name and value are required');
      return;
    }
    try {
      await headersApi.add(newHeader);
      toast.success('Header added');
      setNewHeader({ name: '', value: '', source: 'manual' });
      setShowAddForm(false);
      loadHeaders();
    } catch (error) {
      toast.error('Failed to add header');
    }
  };

  const removeHeader = async (name: string) => {
    try {
      await headersApi.remove(name);
      toast.success('Header removed');
      loadHeaders();
    } catch (error) {
      toast.error('Failed to remove header');
    }
  };

  const clearAll = async () => {
    if (!confirm('Clear all custom headers?')) return;
    try {
      await headersApi.clear();
      toast.success('All headers cleared');
      loadHeaders();
    } catch (error) {
      toast.error('Failed to clear headers');
    }
  };

  return (
    <div className="space-y-6">
      <div className="glass-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-headline text-primary tracking-wider">
              CUSTOM HEADERS
            </h1>
            <p className="text-xs font-mono text-white/50 mt-1">
              Manage authentication headers for testing
            </p>
          </div>
          <div className="flex items-center gap-3">
            <CyberButton variant="secondary" onClick={loadHeaders} loading={loading}>
              <RefreshCw className="w-4 h-4" />
            </CyberButton>
            <CyberButton variant="danger" onClick={clearAll}>
              <Trash2 className="w-4 h-4" />
              Clear All
            </CyberButton>
            <CyberButton onClick={() => setShowAddForm(!showAddForm)}>
              <Plus className="w-4 h-4" />
              Add Header
            </CyberButton>
          </div>
        </div>
      </div>

      {showAddForm && (
        <GlassCard className="p-6">
          <h2 className="section-title mb-4">Add Custom Header</h2>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="data-label">Header Name</label>
              <input
                type="text"
                value={newHeader.name}
                onChange={(e) => setNewHeader({ ...newHeader, name: e.target.value })}
                placeholder="e.g., X-Custom-Auth"
                className="input"
              />
            </div>
            <div>
              <label className="data-label">Header Value</label>
              <input
                type="text"
                value={newHeader.value}
                onChange={(e) => setNewHeader({ ...newHeader, value: e.target.value })}
                placeholder="e.g., Bearer token..."
                className="input"
              />
            </div>
            <div>
              <label className="data-label">Source</label>
              <select
                value={newHeader.source}
                onChange={(e) => setNewHeader({ ...newHeader, source: e.target.value })}
                className="input"
              >
                <option value="manual">Manual</option>
                <option value="program">Program Policy</option>
                <option value="credential">Credential Engine</option>
              </select>
            </div>
          </div>
          <div className="mt-4 flex gap-3">
            <CyberButton onClick={addHeader}>Add Header</CyberButton>
            <CyberButton variant="ghost" onClick={() => setShowAddForm(false)}>Cancel</CyberButton>
          </div>
        </GlassCard>
      )}

      <GlassCard className="p-6">
        <h2 className="section-title mb-4">Active Headers ({headers.length})</h2>
        <div className="space-y-2">
          {headers.map((header) => (
            <div key={header.name} className="flex items-center justify-between p-4 bg-surface-50/50 rounded-lg">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-tertiary/10 flex items-center justify-center">
                  <Key className="w-5 h-5 text-tertiary" />
                </div>
                <div>
                  <div className="text-white font-mono">{header.name}</div>
                  <div className="text-xs text-white/40 font-mono truncate max-w-md">
                    {header.value.substring(0, 50)}...
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-white/40 uppercase">{header.source}</span>
                <button
                  onClick={() => removeHeader(header.name)}
                  className="p-2 hover:bg-error/10 rounded text-error/50 hover:text-error"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
          {headers.length === 0 && !loading && (
            <div className="text-center py-12 text-white/30">
              <Key className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No custom headers configured</p>
            </div>
          )}
        </div>
      </GlassCard>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <GlassCard className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-tertiary" />
            <h2 className="section-title">Security Info</h2>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-white/50">Headers Encrypted</span>
              <span className="text-tertiary">Yes</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Storage</span>
              <span className="text-white">Encrypted Database</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Auto-clear on logout</span>
              <span className="text-tertiary">Yes</span>
            </div>
          </div>
        </GlassCard>

        <GlassCard className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Key className="w-5 h-5 text-secondary" />
            <h2 className="section-title">Usage</h2>
          </div>
          <div className="space-y-3 text-sm text-white/70">
            <p>Custom headers are automatically injected into all HTTP requests during testing.</p>
            <p>Headers from program policies are automatically synced based on the target program.</p>
            <p>Credential engine headers are generated from stored credentials.</p>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
