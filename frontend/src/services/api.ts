import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error('Unauthorized')
    }
    return Promise.reject(error)
  }
)

// ============================================
// PROGRAMS
// ============================================
export const programsApi = {
  list: () => api.get('/programs'),
  get: (id: string) => api.get(`/programs/${id}`),
  create: (data: any) => api.post('/programs', data),
  update: (id: string, data: any) => api.put(`/programs/${id}`, data),
  delete: (id: string) => api.delete(`/programs/${id}`),
  parse: (data: { policy_text: string; use_ai?: boolean }) => api.post('/programs/parse', data),
  import: (data: { policy_text: string; use_ai?: boolean }) => api.post('/programs/import', data),
  getConfig: (id: string) => api.get(`/programs/${id}/config`),
  analyze: (policyText: string, files: File[]) => {
    const formData = new FormData();
    formData.append('policy_text', policyText);
    files.forEach(file => formData.append('files', file));
    return api.post('/programs/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  uploadAttachment: (programId: string, file: File, pfxPassword?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (pfxPassword) {
      formData.append('pfx_password', pfxPassword);
    }
    return api.post(`/programs/${programId}/attachments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  uploadAttachmentDirect: (formData: FormData, options?: { programId?: string }) => {
    const endpoint = options?.programId 
      ? `/programs/${options.programId}/attachments` 
      : '/programs/attachments/upload';
    return api.post(endpoint, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  addCredential: (programId: string, credential: any) => 
    api.post(`/programs/${programId}/credentials`, credential),
  listAttachments: (programId: string) => 
    api.get(`/programs/${programId}/attachments`),
}

// ============================================
// TARGETS
// ============================================
export const targetsApi = {
  list: () => api.get('/targets'),
  get: (id: string) => api.get(`/targets/${id}`),
  create: (data: any) => api.post('/targets', data),
  update: (id: string, data: any) => api.put(`/targets/${id}`, data),
  delete: (id: string) => api.delete(`/targets/${id}`),
  start: (id: string) => api.post(`/targets/${id}/start`),
  pause: (id: string) => api.post(`/targets/${id}/pause`),
  resume: (id: string) => api.post(`/targets/${id}/resume`),
  status: (id: string) => api.get(`/targets/${id}/status`),
}

// ============================================
// FINDINGS
// ============================================
export const findingsApi = {
  list: (params?: any) => api.get('/findings', { params }),
  get: (id: string) => api.get(`/findings/${id}`),
  create: (data: any) => api.post('/findings', data),
  update: (id: string, data: any) => api.patch(`/findings/${id}`, data),
  delete: (id: string) => api.delete(`/findings/${id}`),
  stats: () => api.get('/findings/stats/summary'),
  enhance: (id: string) => api.post(`/findings/${id}/enhance`),
  batchEnhance: (ids: string[]) => api.post('/findings/batch-enhance', { ids }),
  classify: (data: { description: string }) => api.post('/findings/ai/classify', data),
  cacheStats: () => api.get('/findings/ai/cache/stats'),
  clearCache: () => api.post('/findings/ai/cache/clear'),
}

// ============================================
// FLOWS
// ============================================
export const flowsApi = {
  list: (targetId: string) => api.get(`/flows/target/${targetId}`),
  get: (id: string) => api.get(`/flows/${id}`),
  create: (data: any) => api.post('/flows', data),
  update: (id: string, data: any) => api.put(`/flows/${id}`, data),
  start: (id: string) => api.post(`/flows/${id}/start`),
  done: (id: string) => api.post(`/flows/${id}/done`),
  getDag: (targetId: string) => api.get(`/flows/target/${targetId}/dag`),
  generate: (data: any) => api.post('/flows/generate', data),
  generateForProgram: (programId: string) => api.post(`/flows/program/${programId}/generate`),
  getProgramWorkflow: (programId: string) => api.get(`/flows/program/${programId}/workflow`),
  executeStep: (data: any) => api.post('/flows/execute-step', data),
  requestApproval: (data: any) => api.post('/flows/approval-request', {
    step_id: data.step_id,
    workflow_data: data.workflow_data,
    target: data.target,
    reason: data.reason,
  }),
}

// ============================================
// APPROVALS
// ============================================
export const approvalsApi = {
  list: (params?: any) => api.get('/approvals', { params }),
  get: (id: string) => api.get(`/approvals/${id}`),
  approve: (id: string) => api.post(`/approvals/${id}/approve`),
  deny: (id: string) => api.post(`/approvals/${id}/deny`),
  timeout: (id: string) => api.post(`/approvals/${id}/timeout`),
  queue: () => api.get('/approvals/queue'),
}

// ============================================
// PLUGINS
// ============================================
export const pluginsApi = {
  list: () => api.get('/plugins'),
  get: (name: string) => api.get(`/plugins/${name}`),
  run: (name: string, data?: any) => api.post(`/plugins/${name}/run`, data),
  logs: (name: string) => api.get(`/plugins/${name}/logs`),
}

// ============================================
// COVERAGE
// ============================================
export const coverageApi = {
  get: (targetId: string) => api.get(`/coverage/${targetId}`),
  missing: (targetId: string) => api.get(`/coverage/${targetId}/missing`),
  dashboard: (targetId: string) => api.get(`/coverage/${targetId}/dashboard`),
}

// ============================================
// REPORTING
// ============================================
export const reportingApi = {
  generate: (data: any) => api.post('/reports/generate', data),
  save: (data: any) => api.post('/reports/save', data),
  export: (id: string, format: string = 'html') => api.get(`/reports/export/${id}`, { params: { format } }),
  summary: (targetId: string) => api.get(`/reports/summary/${targetId}`),
  submitHackerOne: (data: any) => api.post('/reports/submit/hackerone', data),
  submitBugcrowd: (data: any) => api.post('/reports/submit/bugcrowd', data),
  getTemplate: (platform: string) => api.get(`/reports/templates/${platform}`),
  validate: (data: any) => api.post('/reports/validate', data),
  summarize: (data: any) => api.post('/reports/summarize', data),
  aiStatus: () => api.get('/reports/ai/status'),
}

// ============================================
// INTEL / CVE / THREAT INTELLIGENCE
// ============================================
export const intelApi = {
  cards: () => api.get('/intel/cards'),
  submitFinding: (data: any) => api.post('/intel/findings', data),
  sources: () => api.get('/intel/sources'),
  
  // CVE
  recentCVEs: (days?: number, limit?: number) => api.get('/intel/cve/recent', { params: { days, limit } }),
  cveForProduct: (product: string, vendor?: string, days?: number, limit?: number) => 
    api.post('/intel/cve/product', { product, vendor, days_back: days, limit }),
  correlate: (data: { target_id: string; target_url: string; technologies: string[]; versions?: Record<string, string> }) =>
    api.post('/intel/cve/correlate', data),
  riskScore: (cvssScore: number, cvssVector?: string, dataSensitivity?: string, assetTier?: number) =>
    api.get('/intel/cve/risk-score', { params: { cvss_score: cvssScore, cvss_vector: cvssVector, data_sensitivity: dataSensitivity, asset_tier: assetTier } }),
  getCVE: (cveId: string) => api.get(`/intel/cve/${cveId}`),
  
  // Tech Detection
  detectTech: (data: { content: string; source: string }) => api.post('/intel/tech/detect', data),
  
  // GitHub
  githubSearch: (data: { query: string; language?: string; limit?: number }) => api.post('/intel/github/search', data),
  githubMonitorOrg: (data: { organization: string; scan_secrets?: boolean; scan_vulnerabilities?: boolean }) =>
    api.post('/intel/github/monitor-org', data),
  githubRepos: (org: string) => api.get(`/intel/github/repos/${org}`),
  githubScanFile: (data: { content: string; source: string }) => api.post('/intel/github/scan-file', data),
  githubRateLimit: () => api.get('/intel/github/rate-limit'),
  
  // Leaks
  leakScan: (data: { content: string; source: string }) => api.post('/intel/leak/scan', data),
  
  // Flow Expansion
  autoExpand: (data: { target_id: string; endpoints: Array<{ path: string; method: string; parameters?: any }> }) =>
    api.post('/intel/auto-expand', data),
  
  // AI Hypotheses
  aiHypotheses: (data: { target_id: string; endpoints: Array<{ path: string; method: string; parameters?: any }>; use_ai?: boolean }) =>
    api.post('/intel/ai-hypotheses', data),
}

// ============================================
// CREDENTIALS
// ============================================
export const credentialsApi = {
  list: () => api.get('/credentials'),
  get: (id: string) => api.get(`/credentials/${id}`),
  create: (data: any) => api.post('/credentials', data),
  update: (id: string, data: any) => api.patch(`/credentials/${id}`, data),
  delete: (id: string) => api.delete(`/credentials/${id}`),
}

// ============================================
// CUSTOM HEADERS
// ============================================
export const headersApi = {
  list: () => api.get('/headers'),
  add: (data: { name: string; value: string; source?: string }) => api.post('/headers', data),
  remove: (name: string) => api.delete(`/headers/${name}`),
  clear: (source?: string) => api.delete('/headers', { params: source ? { source } : undefined }),
  inject: (data: { credentials: any[]; headers: string[] }) => api.post('/headers/inject', data),
  getConfig: () => api.get('/headers/config'),
  applyPolicy: (data: { policy: any }) => api.post('/headers/policy', data),
}

// ============================================
// MIXED MODE TESTING
// ============================================
export const testingApi = {
  mixedMode: (data: { target_id: string; strategy?: string }) => api.post('/testing/mixed-mode', data),
  strategies: () => api.get('/testing/mixed-mode/strategies'),
  
  // Account Requests
  createAccountRequest: (data: any) => api.post('/testing/account-requests', data),
  getAccountRequest: (id: string) => api.get(`/testing/account-requests/${id}`),
  getPending: () => api.get('/testing/account-requests/pending'),
  getForProgram: (programId: string) => api.get(`/testing/account-requests/program/${programId}`),
  getFollowup: (days?: number) => api.get('/testing/account-requests/followup', { params: { days } }),
  updateAccountRequest: (id: string, data: any) => api.patch(`/testing/account-requests/${id}`, data),
  markReceived: (id: string) => api.post(`/testing/account-requests/${id}/received`),
}

// ============================================
// CREDENTIAL ENGINE
// ============================================
export const authLevelsApi = {
  decision: (data: { auth_level: string; program_id?: string; target_id?: string }) =>
    api.post('/auth-levels/decision', data),
  decisionForLevel: (level: string) => api.get(`/auth-levels/decision/${level}`),
  test: (data: { credential_id: string; endpoint: string }) => api.post('/auth-levels/test', data),
  checkExpiry: (credential_ids: string[]) => api.post('/auth-levels/check-expiry', { credential_ids }),
  validateDomain: (email: string) => api.get('/auth-levels/validate-domain', { params: { email } }),
  levels: () => api.get('/auth-levels/levels'),
  validate: (data: { credential: any }) => api.post('/auth-levels/validate', data),
  setPolicy: (data: { level: string; policy: any }) => api.post('/auth-levels/policy', data),
  policyTemplates: () => api.get('/auth-levels/policy/templates'),
  emailTemplate: (level: string) => api.get('/auth-levels/policy/email-template', { params: { level } }),
  checkCompliance: (data: { credential: any; policy: any }) => api.post('/auth-levels/policy/check-compliance', data),
}

// ============================================
// JOBS
// ============================================
export const jobsApi = {
  list: () => api.get('/jobs'),
  get: (name: string) => api.get(`/jobs/${name}`),
  trigger: (name: string) => api.post(`/jobs/${name}/trigger`),
  enable: (name: string) => api.post(`/jobs/${name}/enable`),
  disable: (name: string) => api.post(`/jobs/${name}/disable`),
}

// ============================================
// SLACK / NOTIFICATIONS
// ============================================
export const notificationsApi = {
  slackConfig: () => api.get('/notifications/slack/config'),
  slackSend: (data: { channel?: string; message: string; metadata?: any }) => api.post('/notifications/slack/send', data),
  slackApprovalRequest: (data: { approval_id: string }) => api.post('/notifications/slack/approval-request', data),
}

// ============================================
// SETTINGS
// ============================================
export const settingsApi = {
  get: () => api.get('/settings'),
  update: (data: any) => api.patch('/settings', data),
  verifyApis: () => api.get('/verify/apis'),
}

// Legacy ENDPOINTS object for backward compatibility
export const ENDPOINTS = {
  // Programs
  programs: '/programs',
  program: (id: string) => `/programs/${id}`,
  programParse: '/programs/parse',
  
  // Targets
  targets: '/targets',
  target: (id: string) => `/targets/${id}`,
  targetStart: (id: string) => `/targets/${id}/start`,
  targetPause: (id: string) => `/targets/${id}/pause`,
  targetResume: (id: string) => `/targets/${id}/resume`,
  targetStatus: (id: string) => `/targets/${id}/status`,
  
  // Flows
  flows: '/flows',
  flow: (id: string) => `/flows/${id}`,
  targetFlows: (targetId: string) => `/flows/target/${targetId}`,
  flowDag: (targetId: string) => `/flows/target/${targetId}/dag`,
  flowStart: (id: string) => `/flows/${id}/start`,
  flowDone: (id: string) => `/flows/${id}/done`,
  
  // Approvals
  approvals: '/approvals',
  approval: (id: string) => `/approvals/${id}`,
  approvalApprove: (id: string) => `/approvals/${id}/approve`,
  approvalDeny: (id: string) => `/approvals/${id}/deny`,
  approvalTimeout: (id: string) => `/approvals/${id}/timeout`,
  approvalQueue: '/approvals/queue',
  
  // Plugins
  plugins: '/plugins',
  plugin: (name: string) => `/plugins/${name}`,
  pluginRun: (name: string) => `/plugins/${name}/run`,
  pluginLogs: (name: string) => `/plugins/${name}/logs`,
  
  // Findings
  findings: '/findings',
  finding: (id: string) => `/findings/${id}`,
  findingEnhance: (id: string) => `/findings/${id}/enhance`,
  findingsBatchEnhance: '/findings/batch-enhance',
  findingsStats: '/findings/stats/summary',
  findingsClassify: '/findings/ai/classify',
  findingsCacheStats: '/findings/ai/cache/stats',
  findingsClearCache: '/findings/ai/cache/clear',
  
  // Coverage
  coverage: (targetId: string) => `/coverage/${targetId}`,
  coverageMissing: (targetId: string) => `/coverage/${targetId}/missing`,
  coverageDashboard: (targetId: string) => `/coverage/${targetId}/dashboard`,
  
  // Reporting
  reporting: '/reports',
  reportGenerate: '/reports/generate',
  reportSave: '/reports/save',
  reportExport: (id: string) => `/reports/export/${id}`,
  reportSummary: (targetId: string) => `/reports/summary/${targetId}`,
  reportSubmitHackerOne: '/reports/submit/hackerone',
  reportSubmitBugcrowd: '/reports/submit/bugcrowd',
  reportTemplate: (platform: string) => `/reports/templates/${platform}`,
  reportValidate: '/reports/validate',
  reportSummarize: '/reports/summarize',
  reportAiStatus: '/reports/ai/status',
  
  // Intel
  intel: '/intel',
  intelCards: '/intel/cards',
  intelSources: '/intel/sources',
  intelCVERecent: '/intel/cve/recent',
  intelCVEProduct: '/intel/cve/product',
  intelCVECorrelate: '/intel/cve/correlate',
  intelCVEDetails: (cveId: string) => `/intel/cve/${cveId}`,
  intelCVERiskScore: '/intel/cve/risk-score',
  intelTechDetect: '/intel/tech/detect',
  intelGithubSearch: '/intel/github/search',
  intelGithubMonitorOrg: '/intel/github/monitor-org',
  intelGithubRepos: (org: string) => `/intel/github/repos/${org}`,
  intelGithubScanFile: '/intel/github/scan-file',
  intelGithubRateLimit: '/intel/github/rate-limit',
  intelLeakScan: '/intel/leak/scan',
  intelAutoExpand: '/intel/auto-expand',
  intelAIHypotheses: '/intel/ai-hypotheses',
  
  // Settings
  verifyApis: '/verify/apis',
  settings: '/settings',
  
  // Credentials
  credentials: '/credentials',
  credential: (id: string) => `/credentials/${id}`,
  
  // Custom Headers
  headers: '/headers',
  header: (name: string) => `/headers/${name}`,
  headersInject: '/headers/inject',
  headersConfig: '/headers/config',
  headersPolicy: '/headers/policy',
  
  // Testing / Mixed Mode
  testingMixedMode: '/testing/mixed-mode',
  testingStrategies: '/testing/mixed-mode/strategies',
  testingAccountRequests: '/testing/account-requests',
  testingAccountRequest: (id: string) => `/testing/account-requests/${id}`,
  testingAccountRequestsPending: '/testing/account-requests/pending',
  testingAccountRequestsFollowup: '/testing/account-requests/followup',
  testingAccountRequestsProgram: (programId: string) => `/testing/account-requests/program/${programId}`,
  testingAccountRequestReceived: (id: string) => `/testing/account-requests/${id}/received`,
  
  // Auth Levels / Credential Engine
  authLevelsDecision: '/auth-levels/decision',
  authLevelsDecisionLevel: (level: string) => `/auth-levels/decision/${level}`,
  authLevelsTest: '/auth-levels/test',
  authLevelsCheckExpiry: '/auth-levels/check-expiry',
  authLevelsValidateDomain: '/auth-levels/validate-domain',
  authLevelsLevels: '/auth-levels/levels',
  authLevelsValidate: '/auth-levels/validate',
  authLevelsPolicy: '/auth-levels/policy',
  authLevelsPolicyTemplates: '/auth-levels/policy/templates',
  authLevelsEmailTemplate: '/auth-levels/policy/email-template',
  authLevelsCheckCompliance: '/auth-levels/policy/check-compliance',
  
  // Jobs
  jobs: '/jobs',
  job: (name: string) => `/jobs/${name}`,
  jobTrigger: (name: string) => `/jobs/${name}/trigger`,
  jobEnable: (name: string) => `/jobs/${name}/enable`,
  jobDisable: (name: string) => `/jobs/${name}/disable`,
  
  // Slack / Notifications
  slackSend: '/notifications/slack/send',
  slackConfig: '/notifications/slack/config',
  slackApprovalRequest: '/notifications/slack/approval-request',
}

export default api
