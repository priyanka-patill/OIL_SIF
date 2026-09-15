import {
  HealthStatus,
  DatasetItem,
  DatasetSchemaInfo,
  DataQualitySummary,
  SafetyReport,
  SafetyReportCreate,
  ReportCounts,
  ReportAnalysis,
  SIFSummary,
  RecurringIssuesResponse,
  AIFeedback,
  MetadataFieldsResponse,
  PaginatedResponse,
  ActionItem,
  ActionStats,
  ActionHistoryItem,
  NotificationConfigItem,
  EmailPreviewData,
  EmailLogItem,
  ExportPreviewData,
  ExportFilterParams
} from '../types/safety';

const API_BASE = '/api';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const errorBody = await res.text();
    let msg = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const parsed = JSON.parse(errorBody);
      msg = parsed.detail || parsed.message || msg;
    } catch {
      // keep fallback msg
    }
    throw new Error(msg);
  }
  return res.json();
}

export const api = {
  // Health
  getHealth: () => fetchJSON<HealthStatus>(`${API_BASE}/health`),

  // Datasets
  getDatasets: (page = 1, pageSize = 20) =>
    fetchJSON<PaginatedResponse<DatasetItem>>(`${API_BASE}/datasets?page=${page}&page_size=${pageSize}`),
  
  getDataset: (id: string) => fetchJSON<DatasetItem>(`${API_BASE}/datasets/${id}`),
  
  getDatasetSchema: (id: string) => fetchJSON<DatasetSchemaInfo>(`${API_BASE}/datasets/${id}/schema`),
  
  getDataQuality: (datasetId: string) =>
    fetchJSON<DataQualitySummary>(`${API_BASE}/data-quality/${datasetId}`),

  // Reports
  getReports: (params: Record<string, any> = {}) => {
    const cleanParams = Object.entries(params)
      .filter(([_, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
      .join('&');
    return fetchJSON<PaginatedResponse<SafetyReport>>(`${API_BASE}/reports?${cleanParams}`);
  },

  getReport: (id: string) => fetchJSON<SafetyReport>(`${API_BASE}/reports/${id}`),

  createReport: (reportData: SafetyReportCreate) =>
    fetchJSON<SafetyReport>(`${API_BASE}/reports`, {
      method: 'POST',
      body: JSON.stringify(reportData),
    }),

  updateReport: (id: string, reportData: Partial<SafetyReport>) =>
    fetchJSON<SafetyReport>(`${API_BASE}/reports/${id}`, {
      method: 'PUT',
      body: JSON.stringify(reportData),
    }),

  getReportCounts: (datasetId?: string) => {
    const url = datasetId ? `${API_BASE}/reports/count?dataset_id=${encodeURIComponent(datasetId)}` : `${API_BASE}/reports/count`;
    return fetchJSON<ReportCounts>(url);
  },

  // Metadata & Filters
  getMetadataFields: () => fetchJSON<MetadataFieldsResponse>(`${API_BASE}/metadata/fields`),

  // SIF & AI Intelligence
  getSIFSummary: (datasetId?: string) => {
    const url = datasetId ? `${API_BASE}/sif/summary?dataset_id=${encodeURIComponent(datasetId)}` : `${API_BASE}/sif/summary`;
    return fetchJSON<SIFSummary>(url);
  },

  getHighRiskReports: (datasetId?: string, page = 1, pageSize = 20) => {
    const q = datasetId ? `dataset_id=${encodeURIComponent(datasetId)}&` : '';
    return fetchJSON<PaginatedResponse<ReportAnalysis>>(`${API_BASE}/sif/high-risk?${q}page=${page}&page_size=${pageSize}`);
  },

  getRecurringIssues: (datasetId?: string) => {
    const url = datasetId ? `${API_BASE}/sif/recurring?dataset_id=${encodeURIComponent(datasetId)}` : `${API_BASE}/sif/recurring`;
    return fetchJSON<RecurringIssuesResponse>(url);
  },

  getSIFDensity: (datasetId?: string) => {
    const url = datasetId ? `${API_BASE}/sif/density?dataset_id=${encodeURIComponent(datasetId)}` : `${API_BASE}/sif/density`;
    return fetchJSON<any>(url);
  },

  getMultiFactorAnalytics: (datasetId?: string) => {
    const url = datasetId ? `${API_BASE}/sif/multi-factor?dataset_id=${encodeURIComponent(datasetId)}` : `${API_BASE}/sif/multi-factor`;
    return fetchJSON<any>(url);
  },

  getReportAnalysis: (reportId: string) =>
    fetchJSON<ReportAnalysis>(`${API_BASE}/reports/${reportId}/analysis`),

  analyzeReport: (reportId: string) =>
    fetchJSON<ReportAnalysis>(`${API_BASE}/reports/${reportId}/analyze`, { method: 'POST' }),

  batchAnalyze: (datasetId?: string) => {
    const url = datasetId ? `${API_BASE}/reports/analyze-all?dataset_id=${encodeURIComponent(datasetId)}` : `${API_BASE}/reports/analyze-all`;
    return fetchJSON<any>(url, { method: 'POST' });
  },

  submitAIFeedback: (feedback: {
    report_id: string;
    reviewer_name: string;
    agrees_with_ai: boolean;
    human_risk_level?: string;
    human_sif_precursor?: string;
    feedback_reason: string;
  }) =>
    fetchJSON<AIFeedback>(`${API_BASE}/ai-feedback`, {
      method: 'POST',
      body: JSON.stringify(feedback),
    }),

  getAIFeedback: (reportId: string) =>
    fetchJSON<AIFeedback[]>(`${API_BASE}/ai-feedback/${reportId}`),

  // Chat
  sendChatMessage: (message: string, reportId?: string, datasetId?: string) =>
    fetchJSON<{
      reply: string;
      suggested_actions: string[];
      relevant_reports: any[];
      category: string;
    }>(`${API_BASE}/chat`, {
      method: 'POST',
      body: JSON.stringify({ message, report_id: reportId, dataset_id: datasetId }),
    }),

  // --- PART 4: ACTIONS & HISTORY ---
  getActions: (params: Record<string, any> = {}) => {
    const cleanParams = Object.entries(params)
      .filter(([_, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
      .join('&');
    return fetchJSON<PaginatedResponse<ActionItem>>(`${API_BASE}/actions?${cleanParams}`);
  },

  getActionStats: (datasetId?: string) => {
    const url = datasetId ? `${API_BASE}/actions/stats?dataset_id=${encodeURIComponent(datasetId)}` : `${API_BASE}/actions/stats`;
    return fetchJSON<ActionStats>(url);
  },

  updateAction: (reportId: string, payload: Record<string, any>) =>
    fetchJSON<ActionItem>(`${API_BASE}/actions/${reportId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  getActionHistory: (reportId: string) =>
    fetchJSON<ActionHistoryItem[]>(`${API_BASE}/actions/${reportId}/history`),

  getAllActionHistories: (page = 1, pageSize = 20) =>
    fetchJSON<PaginatedResponse<ActionHistoryItem>>(`${API_BASE}/audit-logs/actions?page=${page}&page_size=${pageSize}`),

  // --- PART 4: NOTIFICATIONS & ESCALATION ---
  getNotificationConfigs: () =>
    fetchJSON<NotificationConfigItem[]>(`${API_BASE}/notifications/config`),

  createNotificationConfig: (payload: Partial<NotificationConfigItem>) =>
    fetchJSON<NotificationConfigItem>(`${API_BASE}/notifications/config`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateNotificationConfig: (configId: string, payload: Partial<NotificationConfigItem>) =>
    fetchJSON<NotificationConfigItem>(`${API_BASE}/notifications/config/${configId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),

  deleteNotificationConfig: (configId: string) =>
    fetch(`${API_BASE}/notifications/config/${configId}`, { method: 'DELETE' }),

  previewEmail: (payload: { report_id: string; notification_type?: string; target_tier?: string }) =>
    fetchJSON<EmailPreviewData>(`${API_BASE}/notifications/preview`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  sendNotificationEmail: (payload: {
    report_id: string;
    notification_type: string;
    recipient_emails: string[];
    subject: string;
    body_html: string;
    triggered_by?: string;
    escalation_tier?: string;
  }) =>
    fetchJSON<{ success: boolean; message: string; email_log_id: string; recipients_count: number; sent_at: string }>(
      `${API_BASE}/notifications/send`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    ),

  getEmailLogs: (reportId?: string, page = 1, pageSize = 20) => {
    const q = reportId ? `report_id=${encodeURIComponent(reportId)}&` : '';
    return fetchJSON<PaginatedResponse<EmailLogItem>>(`${API_BASE}/notifications/logs?${q}page=${page}&page_size=${pageSize}`);
  },

  // --- PART 4: REPORT EXPORT ---
  getExportPreview: (params: ExportFilterParams = {}) => {
    const cleanParams = Object.entries(params)
      .filter(([_, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
      .join('&');
    return fetchJSON<ExportPreviewData>(`${API_BASE}/reports/export/preview?${cleanParams}`);
  },

  getExportPdfUrl: (params: ExportFilterParams = {}) => {
    const cleanParams = Object.entries(params)
      .filter(([_, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
      .join('&');
    return `${API_BASE}/reports/export/pdf?${cleanParams}`;
  },

  getExportExcelUrl: (params: ExportFilterParams = {}) => {
    const cleanParams = Object.entries(params)
      .filter(([_, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
      .join('&');
    return `${API_BASE}/reports/export/excel?${cleanParams}`;
  },

  getExportCsvUrl: (params: ExportFilterParams = {}) => {
    const cleanParams = Object.entries(params)
      .filter(([_, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
      .join('&');
    return `${API_BASE}/reports/export/csv?${cleanParams}`;
  },

  // --- PART 4: AUDIT LOGS ---
  getAuditLogs: (params: Record<string, any> = {}) => {
    const cleanParams = Object.entries(params)
      .filter(([_, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
      .join('&');
    return fetchJSON<PaginatedResponse<any>>(`${API_BASE}/audit-logs?${cleanParams}`);
  },

  // --- MULTI-DATASET & FACTOR INTELLIGENCE ---
  getFactorSummary: (datasetId?: string) => {
    const url = datasetId ? `${API_BASE}/factors/summary?dataset_id=${encodeURIComponent(datasetId)}` : `${API_BASE}/factors/summary`;
    return fetchJSON<any>(url);
  },

  getFactorCombinations: (datasetId?: string) => {
    const url = datasetId ? `${API_BASE}/factors/combinations?dataset_id=${encodeURIComponent(datasetId)}` : `${API_BASE}/factors/combinations`;
    return fetchJSON<any>(url);
  },

  compareDatasets: (datasetIdA: string, datasetIdB: string) => {
    return fetchJSON<any>(`${API_BASE}/datasets/compare?dataset_a=${encodeURIComponent(datasetIdA)}&dataset_b=${encodeURIComponent(datasetIdB)}`);
  },

  getHighPotentialIntelligence: () => {
    return fetchJSON<any>(`${API_BASE}/sif/high-potential`);
  },

  uploadWorkbook: (formData: FormData) => {
    return fetch(`${API_BASE}/datasets/ingest-workbook`, {
      method: 'POST',
      body: formData,
    }).then((res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}: Upload failed`);
      return res.json();
    });
  },

  // --- PHASE 2: SWISS CHEESE SAFETY BARRIERS ---
  getBarrierSummary: (datasetId?: string) => {
    const url = datasetId ? `${API_BASE}/barriers/summary?dataset_id=${encodeURIComponent(datasetId)}` : `${API_BASE}/barriers/summary`;
    return fetchJSON<any>(url);
  },

  getReportBarriers: (reportId: string) =>
    fetchJSON<any>(`${API_BASE}/barriers/report/${reportId}`),

  getCriticalBarriers: (datasetId?: string) => {
    const url = datasetId ? `${API_BASE}/barriers/critical?dataset_id=${encodeURIComponent(datasetId)}` : `${API_BASE}/barriers/critical`;
    return fetchJSON<any>(url);
  },

  // --- PHASE 3: BARRIER DEGRADATION INDEX (BDI) ---
  getBDISummary: (datasetId?: string) => {
    const url = datasetId ? `${API_BASE}/bdi/summary?dataset_id=${encodeURIComponent(datasetId)}` : `${API_BASE}/bdi/summary`;
    return fetchJSON<any>(url);
  },

  getReportBDI: (reportId: string) =>
    fetchJSON<any>(`${API_BASE}/bdi/report/${reportId}`),

  getHighBDI: (minScore = 60.1, datasetId?: string) => {
    const q = datasetId ? `&dataset_id=${encodeURIComponent(datasetId)}` : '';
    return fetchJSON<any>(`${API_BASE}/bdi/high?min_score=${minScore}${q}`);
  },

  getBDITrends: (datasetId?: string) => {
    const url = datasetId ? `${API_BASE}/bdi/trends?dataset_id=${encodeURIComponent(datasetId)}` : `${API_BASE}/bdi/trends`;
    return fetchJSON<any>(url);
  },

  // --- PHASE 4: SIF PRECURSOR ESCALATION ENGINE ---
  getSIFEscalationSummary: (datasetId?: string) => {
    const url = datasetId ? `${API_BASE}/sif/escalation/summary?dataset_id=${encodeURIComponent(datasetId)}` : `${API_BASE}/sif/escalation/summary`;
    return fetchJSON<any>(url);
  },

  getReportSIFEscalation: (reportId: string) =>
    fetchJSON<any>(`${API_BASE}/sif/escalation/report/${reportId}`),

  getCriticalSIFEscalations: (datasetId?: string) => {
    const url = datasetId ? `${API_BASE}/sif/escalation/critical?dataset_id=${encodeURIComponent(datasetId)}` : `${API_BASE}/sif/escalation/critical`;
    return fetchJSON<any>(url);
  },

  getHighSIFEscalations: (datasetId?: string) => {
    const url = datasetId ? `${API_BASE}/sif/escalation/high?dataset_id=${encodeURIComponent(datasetId)}` : `${API_BASE}/sif/escalation/high`;
    return fetchJSON<any>(url);
  },

  // --- PHASE 5: AGENTIC SAFETY ACTION ORCHESTRATOR ---
  getOrchestratorSummary: () =>
    fetchJSON<any>(`${API_BASE}/orchestrator/summary`),

  getSafetyActions: (params: Record<string, any> = {}) => {
    const cleanParams = Object.entries(params)
      .filter(([_, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
      .join('&');
    return fetchJSON<any>(`${API_BASE}/orchestrator/actions?${cleanParams}`);
  },

  getSafetyActionById: (actionId: string) =>
    fetchJSON<any>(`${API_BASE}/orchestrator/actions/${actionId}`),

  approveSafetyAction: (actionId: string, body: any) =>
    fetchJSON<any>(`${API_BASE}/orchestrator/actions/${actionId}/approve`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  transitionSafetyAction: (actionId: string, body: any) =>
    fetchJSON<any>(`${API_BASE}/orchestrator/actions/${actionId}/transition`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  // --- PHASE 6: DIGITAL SAFETY HOLDS & SLA MONITORING ---
  getSafetyHolds: (params: Record<string, any> = {}) => {
    const cleanParams = Object.entries(params)
      .filter(([_, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
      .join('&');
    return fetchJSON<any>(`${API_BASE}/safety-holds?${cleanParams}`);
  },

  getSafetyHoldById: (holdId: string) =>
    fetchJSON<any>(`${API_BASE}/safety-holds/${holdId}`),

  requestSafetyHold: (body: any) =>
    fetchJSON<any>(`${API_BASE}/safety-holds/request`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  reviewSafetyHold: (holdId: string, body: any) =>
    fetchJSON<any>(`${API_BASE}/safety-holds/${holdId}/review`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  verifyAndReleaseSafetyHold: (holdId: string, body: any) =>
    fetchJSON<any>(`${API_BASE}/safety-holds/${holdId}/verify-release`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  getSLADashboard: () =>
    fetchJSON<any>(`${API_BASE}/sla/dashboard`),

  getSLAPolicies: () =>
    fetchJSON<any>(`${API_BASE}/sla/policies`),

  getActionCountdown: (actionId: string) =>
    fetchJSON<any>(`${API_BASE}/sla/countdown/${actionId}`),

  acknowledgeAction: (actionId: string, body: any) =>
    fetchJSON<any>(`${API_BASE}/sla/acknowledge/${actionId}`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  // --- PHASE 8: DEMO SIMULATION, AUDIT TRAIL, HUMAN FEEDBACK & ADMIN SETTINGS ---
  // Demo / Simulation Engine
  getDemoStatus: () =>
    fetchJSON<any>(`${API_BASE}/demo/status`),

  toggleDemoMode: (enabled: boolean) =>
    fetchJSON<any>(`${API_BASE}/demo/toggle`, {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    }),

  loadDemoScenario: (scenarioType: string, refineryUnit?: string) =>
    fetchJSON<any>(`${API_BASE}/demo/load-scenario`, {
      method: 'POST',
      body: JSON.stringify({ scenario_type: scenarioType, refinery_unit: refineryUnit }),
    }),

  timeTravelDemo: (advanceMinutes: number, actionId?: string) =>
    fetchJSON<any>(`${API_BASE}/demo/time-travel`, {
      method: 'POST',
      body: JSON.stringify({ advance_minutes: advanceMinutes, action_id: actionId }),
    }),

  simulateDemoStep: (body: { step: string; action_id?: string; actor_name?: string; actor_role?: string; notes?: string }) =>
    fetchJSON<any>(`${API_BASE}/demo/simulate-step`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  resetDemoState: () =>
    fetchJSON<any>(`${API_BASE}/demo/reset`, {
      method: 'POST',
    }),

  // Audit Trail
  getSystemAuditLogs: (params: Record<string, any> = {}) => {
    const cleanParams = Object.entries(params)
      .filter(([_, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
      .join('&');
    return fetchJSON<any>(`${API_BASE}/audit-trail?${cleanParams}`);
  },

  getReportAuditTimeline: (reportId: string) =>
    fetchJSON<any>(`${API_BASE}/audit-trail/report/${reportId}`),

  getActionAuditTimeline: (actionId: string) =>
    fetchJSON<any>(`${API_BASE}/audit-trail/action/${actionId}`),

  getAuditStats: () =>
    fetchJSON<any>(`${API_BASE}/audit-trail/stats`),

  // Human Feedback
  submitHumanFeedback: (body: any) =>
    fetchJSON<any>(`${API_BASE}/feedback`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  listHumanFeedbacks: (params: Record<string, any> = {}) => {
    const cleanParams = Object.entries(params)
      .filter(([_, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
      .join('&');
    return fetchJSON<any>(`${API_BASE}/feedback?${cleanParams}`);
  },

  getFeedbackStats: () =>
    fetchJSON<any>(`${API_BASE}/feedback/stats`),

  // Admin Settings
  getAdminSettings: () =>
    fetchJSON<any>(`${API_BASE}/admin/settings`),

  updateAdminSettings: (body: any) =>
    fetchJSON<any>(`${API_BASE}/admin/settings`, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),
};


