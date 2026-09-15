import React, { useState, useEffect } from 'react';
import { HealthStatus, UserRole, AdminSettingsResponse, SystemAuditLogItem, FeedbackStatsResponse } from '../../types/safety';
import { api } from '../../services/api';

interface SettingsViewProps {
  health: HealthStatus | null;
  activeRole: UserRole;
  onRoleChange: (role: UserRole) => void;
  onOpenDemo?: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ health, activeRole, onRoleChange, onOpenDemo }) => {
  const [activeTab, setActiveTab] = useState<'admin_params' | 'sla_matrix' | 'security' | 'audit_stream' | 'feedback_stats'>('admin_params');

  // Admin Settings State
  const [adminSettings, setAdminSettings] = useState<AdminSettingsResponse | null>(null);
  const [loadingSettings, setLoadingSettings] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);
  const [settingsSuccess, setSettingsSuccess] = useState(false);

  // Editable Form State
  const [bdiMethodology, setBdiMethodology] = useState<string>('WEIGHTED_DEFENSE_IN_DEPTH');
  const [demoModeActive, setDemoModeActive] = useState<boolean>(false);
  const [humanApprovalRequired, setHumanApprovalRequired] = useState<boolean>(true);
  const [highBdiCutoff, setHighBdiCutoff] = useState<number>(60.0);
  const [criticalBdiCutoff, setCriticalBdiCutoff] = useState<number>(80.0);

  // System Audit Stream State
  const [systemAuditLogs, setSystemAuditLogs] = useState<SystemAuditLogItem[]>([]);
  const [auditFilterType, setAuditFilterType] = useState<string>('');
  const [loadingAudit, setLoadingAudit] = useState(false);

  // Human Feedback Stats State
  const [feedbackStats, setFeedbackStats] = useState<FeedbackStatsResponse | null>(null);
  const [loadingFeedback, setLoadingFeedback] = useState(false);

  const fetchAdminSettings = async () => {
    setLoadingSettings(true);
    try {
      const data = await api.getAdminSettings();
      setAdminSettings(data);
      setBdiMethodology(data.bdi_methodology.methodology);
      setDemoModeActive(data.demo_mode_active);
      setHumanApprovalRequired(data.human_approval_required);
      setHighBdiCutoff(data.sif_thresholds.high_bdi_cutoff);
      setCriticalBdiCutoff(data.sif_thresholds.critical_bdi_cutoff);
    } catch (err) {
      console.error('Failed to load admin settings:', err);
    } finally {
      setLoadingSettings(false);
    }
  };

  const fetchAuditStream = async () => {
    setLoadingAudit(true);
    try {
      const data = await api.getSystemAuditLogs({
        event_type: auditFilterType || undefined,
        page: 1,
        page_size: 40,
      });
      setSystemAuditLogs(data.items || []);
    } catch (err) {
      console.error('Failed to load system audit logs:', err);
    } finally {
      setLoadingAudit(false);
    }
  };

  const fetchFeedbackStats = async () => {
    setLoadingFeedback(true);
    try {
      const data = await api.getFeedbackStats();
      setFeedbackStats(data);
    } catch (err) {
      console.error('Failed to load feedback stats:', err);
    } finally {
      setLoadingFeedback(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'admin_params' || activeTab === 'sla_matrix' || activeTab === 'security') {
      fetchAdminSettings();
    } else if (activeTab === 'audit_stream') {
      fetchAuditStream();
    } else if (activeTab === 'feedback_stats') {
      fetchFeedbackStats();
    }
  }, [activeTab, auditFilterType]);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    if (activeRole !== 'Administrator') {
      alert('Governance settings modifications require Administrator role.');
      return;
    }
    setSavingSettings(true);
    try {
      const updated = await api.updateAdminSettings({
        demo_mode_active: demoModeActive,
        human_approval_required: humanApprovalRequired,
        bdi_methodology: {
          methodology: bdiMethodology,
          include_historical_penalty: true,
          near_miss_multiplier: 1.25,
        },
        sif_thresholds: {
          high_bdi_cutoff: highBdiCutoff,
          critical_bdi_cutoff: criticalBdiCutoff,
          min_failed_barriers_for_critical: 2,
          require_toxic_or_flammable_exposure: true,
        },
        updated_by: `${activeRole} Operator`,
      });
      setAdminSettings(updated);
      setSettingsSuccess(true);
      setTimeout(() => setSettingsSuccess(false), 2500);
    } catch (err: any) {
      alert(`Failed to save settings: ${err.message}`);
    } finally {
      setSavingSettings(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Role Switcher & Demo Shortcut */}
      <div className="bg-white border border-[#D9E2EA] rounded-2xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
        <div>
          <h2 className="text-base font-mono font-bold text-[#172B3A] uppercase tracking-wider mb-1 flex items-center gap-2">
            Platform Governance, Analytical Engine & Security Settings
          </h2>
          <p className="text-xs font-sans text-[#526575]">
            Configure BDI thresholds, Swiss Cheese methodology, SLA governance policies, masked credentials, and audit streams.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {onOpenDemo && (
            <button
              onClick={onOpenDemo}
              className="px-3 py-2 bg-[#1769AA] hover:bg-[#123B5D] text-white rounded-xl text-xs font-mono font-bold transition-all shadow-sm flex items-center gap-1.5"
            >
              Launch Demo Controller
            </button>
          )}

          {/* Role Switcher */}
          <div className="flex items-center gap-2 bg-[#F4F7FA] p-2 rounded-xl border border-[#D9E2EA] text-xs font-mono">
            <span className="text-[#718394] uppercase text-[10px] pl-1 font-bold">ROLE:</span>
            <select
              value={activeRole}
              onChange={(e) => onRoleChange(e.target.value as UserRole)}
              className="bg-white border border-[#D9E2EA] text-[#1769AA] font-bold rounded-lg px-2.5 py-1 focus:outline-none cursor-pointer"
            >
              <option value="Safety Officer">Safety Officer</option>
              <option value="Management">Management</option>
              <option value="Administrator">Administrator</option>
            </select>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-[#D9E2EA] pb-2 text-xs font-mono">
        <button
          onClick={() => setActiveTab('admin_params')}
          className={`px-4 py-2 rounded-lg transition-all ${
            activeTab === 'admin_params' ? 'bg-[#1769AA] text-white font-bold shadow-sm' : 'text-[#526575] hover:text-[#172B3A] hover:bg-[#EEF3F7]'
          }`}
        >
           Engine & BDI Parameters
        </button>
        <button
          onClick={() => setActiveTab('sla_matrix')}
          className={`px-4 py-2 rounded-lg transition-all ${
            activeTab === 'sla_matrix' ? 'bg-[#1769AA] text-white font-bold shadow-sm' : 'text-[#526575] hover:text-[#172B3A] hover:bg-[#EEF3F7]'
          }`}
        >
           SLA & Escalation Policies
        </button>
        <button
          onClick={() => setActiveTab('security')}
          className={`px-4 py-2 rounded-lg transition-all ${
            activeTab === 'security' ? 'bg-[#1769AA] text-white font-bold shadow-sm' : 'text-[#526575] hover:text-[#172B3A] hover:bg-[#EEF3F7]'
          }`}
        >
           Security & Notifications
        </button>
        <button
          onClick={() => setActiveTab('audit_stream')}
          className={`px-4 py-2 rounded-lg transition-all flex items-center gap-1.5 ${
            activeTab === 'audit_stream' ? 'bg-[#1769AA] text-white font-bold shadow-sm' : 'text-[#526575] hover:text-[#172B3A] hover:bg-[#EEF3F7]'
          }`}
        >
          Immutable Audit Stream
        </button>
        <button
          onClick={() => setActiveTab('feedback_stats')}
          className={`px-4 py-2 rounded-lg transition-all flex items-center gap-1.5 ${
            activeTab === 'feedback_stats' ? 'bg-[#1769AA] text-white font-bold shadow-sm' : 'text-[#526575] hover:text-[#172B3A] hover:bg-[#EEF3F7]'
          }`}
        >
          Human Calibration Analytics
        </button>
      </div>

      {/* TAB 1: ENGINE & BDI PARAMETERS */}
      {activeTab === 'admin_params' && (
        <form onSubmit={handleSaveSettings} className="space-y-6 text-xs font-mono">
          {settingsSuccess && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl font-bold flex items-center gap-2">
              Governance parameters successfully updated and logged to audit trail!
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Analytical Methodology Card */}
            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-4 shadow-sm">
              <h3 className="text-xs font-bold text-[#1769AA] uppercase tracking-wider border-b border-[#D9E2EA] pb-2 flex items-center justify-between">
                <span>Analytical Engine & Version</span>
                <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200 text-[10px]">
                  {adminSettings?.ai_engine_version || 'v2.0.0-phase8'}
                </span>
              </h3>

              <div className="space-y-3 text-[#172B3A]">
                <div>
                  <label className="text-[10px] text-[#718394] uppercase block mb-1 font-bold">BDI Scoring Methodology</label>
                  <select
                    value={bdiMethodology}
                    onChange={(e) => setBdiMethodology(e.target.value)}
                    disabled={activeRole !== 'Administrator'}
                    className="w-full bg-[#F4F7FA] border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA] disabled:opacity-60"
                  >
                    <option value="WEIGHTED_DEFENSE_IN_DEPTH">Weighted Defense-in-Depth (Reason Barrier Layers)</option>
                    <option value="REASON_SWISS_CHEESE_MULTIPLICATIVE">Reason Swiss Cheese Multiplicative Degradation</option>
                  </select>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-[#F4F7FA] border border-[#D9E2EA]">
                  <div>
                    <span className="font-bold text-[#172B3A] block">Demonstration / Simulation Mode</span>
                    <span className="text-[#526575] text-[10px]">Suppress external notifications for hackathon presentations</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={demoModeActive}
                    onChange={(e) => setDemoModeActive(e.target.checked)}
                    disabled={activeRole !== 'Administrator'}
                    className="w-4 h-4 accent-[#1769AA] cursor-pointer"
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-[#F4F7FA] border border-[#D9E2EA]">
                  <div>
                    <span className="font-bold text-[#172B3A] block">Human Approval Guard</span>
                    <span className="text-[#526575] text-[10px]">Require safety officer review before dispatching actions</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={humanApprovalRequired}
                    onChange={(e) => setHumanApprovalRequired(e.target.checked)}
                    disabled={activeRole !== 'Administrator'}
                    className="w-4 h-4 accent-[#1769AA] cursor-pointer"
                  />
                </div>
              </div>
            </div>

            {/* Thresholds Card */}
            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-4 shadow-sm">
              <h3 className="text-xs font-bold text-[#1769AA] uppercase tracking-wider border-b border-[#D9E2EA] pb-2">
                BDI & SIF Escalation Cutoffs
              </h3>

              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-[11px] mb-1">
                    <span className="text-[#526575]">HIGH SIF PRECURSOR BDI CUTOFF:</span>
                    <span className="text-[#E5A11A] font-bold">{highBdiCutoff} / 100</span>
                  </div>
                  <input
                    type="range"
                    min={40}
                    max={75}
                    step={5}
                    value={highBdiCutoff}
                    onChange={(e) => setHighBdiCutoff(Number(e.target.value))}
                    disabled={activeRole !== 'Administrator'}
                    className="w-full accent-[#E5A11A]"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-[11px] mb-1">
                    <span className="text-[#526575]">CRITICAL SIF PRECURSOR BDI CUTOFF:</span>
                    <span className="text-rose-700 font-bold">{criticalBdiCutoff} / 100</span>
                  </div>
                  <input
                    type="range"
                    min={70}
                    max={95}
                    step={5}
                    value={criticalBdiCutoff}
                    onChange={(e) => setCriticalBdiCutoff(Number(e.target.value))}
                    disabled={activeRole !== 'Administrator'}
                    className="w-full accent-rose-600"
                  />
                </div>

                <div className="p-3 bg-[#F4F7FA] rounded-xl border border-[#D9E2EA] space-y-1 text-[10px] text-[#526575]">
                  <div>• Normal: 0–20 BDI</div>
                  <div>• Low Degradation: 20–40 BDI</div>
                  <div>• Moderate Degradation: 40–60 BDI</div>
                  <div>• High Precursor: 60–80 BDI</div>
                  <div>• Critical Precursor: 80–100 BDI</div>
                </div>
              </div>
            </div>
          </div>

          {activeRole === 'Administrator' && (
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={savingSettings}
                className="px-6 py-2.5 bg-[#1769AA] hover:bg-[#123B5D] text-white rounded-xl font-bold transition-all shadow-sm disabled:opacity-50"
              >
                {savingSettings ? 'Saving Governance Changes...' : ' Save Governance Settings'}
              </button>
            </div>
          )}
        </form>
      )}

      {/* TAB 2: SLA & ESCALATION MATRIX */}
      {activeTab === 'sla_matrix' && (
        <div className="space-y-4 text-xs font-mono">
          <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-4 shadow-sm">
            <h3 className="text-xs font-bold text-[#1769AA] uppercase tracking-wider border-b border-[#D9E2EA] pb-2 flex items-center justify-between">
              <span>SLA Response Windows & Multi-Tier Escalation Hierarchy</span>
              <span className="text-[#718394] text-[10px]">Demonstration Critical Default: 60m</span>
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-[#D9E2EA] bg-[#EEF3F7] text-[#526575] text-[10px] uppercase font-bold">
                    <th className="py-2.5 px-3">Severity</th>
                    <th className="py-2.5 px-3">SLA Window</th>
                    <th className="py-2.5 px-3">Reminder</th>
                    <th className="py-2.5 px-3">Warning</th>
                    <th className="py-2.5 px-3">Level 0 Role</th>
                    <th className="py-2.5 px-3">Level 1 Escalation</th>
                    <th className="py-2.5 px-3">Level 2 Escalation</th>
                    <th className="py-2.5 px-3">Level 3 Escalation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#D9E2EA]">
                  {(adminSettings?.sla_policies || []).map((p) => (
                    <tr key={p.severity} className="hover:bg-[#EEF3F7]/50 transition-colors">
                      <td className="py-2.5 px-3 font-bold">
                        <span className={`px-2 py-0.5 rounded text-[10px] ${
                          p.severity === 'CRITICAL' ? 'bg-rose-50 text-rose-800 border border-rose-200' :
                          p.severity === 'HIGH' ? 'bg-orange-50 text-orange-800 border border-orange-200' :
                          p.severity === 'ELEVATED' ? 'bg-amber-50 text-amber-800 border border-amber-200' :
                          'bg-blue-50 text-blue-800 border border-blue-200'
                        }`}>
                          {p.severity}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-bold text-[#172B3A]">{p.target_sla_minutes}m ({Math.round(p.target_sla_minutes / 60)}h)</td>
                      <td className="py-2.5 px-3 text-[#526575]">{p.reminder_interval_minutes}m</td>
                      <td className="py-2.5 px-3 text-[#E5A11A] font-bold">{p.warning_interval_minutes}m</td>
                      <td className="py-2.5 px-3 text-[#172B3A]">{p.level_0_role}</td>
                      <td className="py-2.5 px-3 text-[#1769AA] font-bold">{p.level_1_role}</td>
                      <td className="py-2.5 px-3 text-indigo-700 font-bold">{p.level_2_role}</td>
                      <td className="py-2.5 px-3 text-purple-700 font-bold">{p.level_3_role}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: SECURITY & NOTIFICATIONS */}
      {activeTab === 'security' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs font-mono">
          <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-4 shadow-sm">
            <h3 className="text-xs font-bold text-[#1769AA] uppercase tracking-wider border-b border-[#D9E2EA] pb-2">
               Protected SMTP & Email Settings
            </h3>
            <div className="space-y-2 text-[#172B3A]">
              <div className="flex justify-between py-1 border-b border-[#D9E2EA]">
                <span className="text-[#718394]">MOCK DELIVERY MODE:</span>
                <span className="font-bold text-[#2E8B57]">ENABLED (Zero Network Leak Risk)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#D9E2EA]">
                <span className="text-[#718394]">SMTP HOST:</span>
                <span className="text-[#172B3A]">{adminSettings?.notification_channels.smtp_host}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#D9E2EA]">
                <span className="text-[#718394]">SMTP PORT:</span>
                <span className="text-[#172B3A]">{adminSettings?.notification_channels.smtp_port}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#D9E2EA]">
                <span className="text-[#718394]">SMTP USER:</span>
                <span className="text-[#172B3A]">{adminSettings?.notification_channels.smtp_user}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#D9E2EA]">
                <span className="text-[#718394]">CREDENTIALS:</span>
                <span className="font-mono text-[#1769AA]">•••••••• (Protected / Environment-based)</span>
              </div>
            </div>
          </div>

          <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-4 shadow-sm">
            <h3 className="text-xs font-bold text-[#1769AA] uppercase tracking-wider border-b border-[#D9E2EA] pb-2">
               Webhook Dispatch Security & Signatures
            </h3>
            <div className="space-y-2 text-[#172B3A]">
              <div className="flex justify-between py-1 border-b border-[#D9E2EA]">
                <span className="text-[#718394]">WEBHOOK STATUS:</span>
                <span className="font-bold text-[#2E8B57]">ACTIVE (Internal Mock)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#D9E2EA]">
                <span className="text-[#718394]">ENDPOINT URL:</span>
                <span className="text-[#172B3A] truncate max-w-[200px]">{adminSettings?.notification_channels.webhook_url_masked}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#D9E2EA]">
                <span className="text-[#718394]">PAYLOAD HASHING:</span>
                <span className="text-[#1769AA] font-bold">SHA-256 Immutable Audit Signature</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#D9E2EA]">
                <span className="text-[#718394]">AUDIT IMMUTABILITY:</span>
                <span className="text-[#2E8B57] font-bold">STRICT READ-ONLY</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: IMMUTABLE AUDIT STREAM */}
      {activeTab === 'audit_stream' && (
        <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-4 text-xs font-mono shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#D9E2EA] pb-3">
            <div>
              <h3 className="font-bold text-[#1769AA] uppercase tracking-wider flex items-center gap-2">
                Platform Governance & Lifecycle Audit Stream ({systemAuditLogs.length} Events)
              </h3>
              <p className="text-[11px] font-sans text-[#526575]">
                Immutable, append-only logs tracking detection, BDI, SIF escalation, actions, holds, SLAs, and reviews.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={auditFilterType}
                onChange={(e) => setAuditFilterType(e.target.value)}
                className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-lg px-2.5 py-1 text-[#172B3A] focus:outline-none text-xs"
              >
                <option value="">All Event Types</option>
                <option value="DETECTION">Detection</option>
                <option value="CORRELATION">Correlation</option>
                <option value="BARRIER_ASSESSMENT">Barrier Assessment</option>
                <option value="BDI_CALCULATION">BDI Calculation</option>
                <option value="SIF_ESCALATION">SIF Escalation</option>
                <option value="ACTION_CREATION">Action Creation</option>
                <option value="SAFETY_HOLD">Safety Hold</option>
                <option value="SLA_BREACH">SLA Breach</option>
                <option value="ACKNOWLEDGEMENT">Acknowledgement</option>
                <option value="CONTAINMENT">Containment</option>
                <option value="VERIFICATION">Verification</option>
                <option value="CLOSURE">Closure</option>
                <option value="HUMAN_FEEDBACK">Human Feedback</option>
              </select>

              <button
                onClick={fetchAuditStream}
                disabled={loadingAudit}
                className="px-3 py-1 bg-[#EEF3F7] hover:bg-slate-200 text-[#172B3A] border border-[#D9E2EA] rounded-lg font-bold"
              >
                {loadingAudit ? 'Loading...' : 'Refresh Stream'}
              </button>
            </div>
          </div>

          <div className="space-y-2 max-h-[500px] overflow-y-auto">
            {loadingAudit ? (
              <div className="py-12 text-center text-[#1769AA] animate-pulse">Loading system audit stream...</div>
            ) : systemAuditLogs.length === 0 ? (
              <div className="py-12 text-center text-[#718394]">No audit records found matching criteria.</div>
            ) : (
              systemAuditLogs.map((log) => (
                <div key={log.event_id} className="p-3 rounded-xl bg-[#F4F7FA] border border-[#D9E2EA] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 hover:border-[#1769AA]/40 transition-colors">
                  <div className="flex items-center gap-2.5">
                    <span className="px-2 py-0.5 rounded bg-white text-[#1769AA] border border-[#D9E2EA] font-bold text-[10px]">
                      {log.event_type}
                    </span>
                    {log.is_simulated && (
                      <span className="px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 text-[9px] font-bold">
                        SIMULATED
                      </span>
                    )}
                    <span className="font-bold text-[#172B3A]">{log.trigger}</span>
                  </div>

                  <div className="flex items-center gap-3 text-[#526575] text-[11px] shrink-0">
                    <span>Actor: <strong className="text-[#172B3A]">{log.actor}</strong></span>
                    {log.report_id && <span>Report: <strong className="text-[#1769AA]">{log.report_id}</strong></span>}
                    <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB 5: HUMAN CALIBRATION ANALYTICS */}
      {activeTab === 'feedback_stats' && (
        <div className="space-y-6 text-xs font-mono">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-4 shadow-sm">
              <span className="text-[10px] text-[#718394] uppercase block font-bold">Total Expert Reviews</span>
              <div className="text-2xl font-bold text-[#172B3A] mt-1">{feedbackStats?.total_feedback_count || 0}</div>
            </div>

            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-4 shadow-sm">
              <span className="text-[10px] text-[#718394] uppercase block font-bold">Model Agreement Rate</span>
              <div className="text-2xl font-bold text-[#2E8B57] mt-1">
                {feedbackStats?.agreement_rate_percentage || 0}%
              </div>
            </div>

            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-4 shadow-sm">
              <span className="text-[10px] text-[#718394] uppercase block font-bold">Ratings Breakdown</span>
              <div className="text-[11px] text-[#172B3A] mt-1 space-y-0.5">
                <div>Correct: {feedbackStats?.ratings_breakdown?.CORRECT || 0}</div>
                <div>Partial: {feedbackStats?.ratings_breakdown?.PARTIALLY_CORRECT || 0}</div>
                <div>Incorrect: {feedbackStats?.ratings_breakdown?.INCORRECT || 0}</div>
              </div>
            </div>

            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-4 shadow-sm">
              <span className="text-[10px] text-[#718394] uppercase block font-bold">Top Category</span>
              <div className="text-base font-bold text-[#1769AA] mt-1">SIF Precursor Calibration</div>
            </div>
          </div>

          <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-3 shadow-sm">
            <h4 className="font-bold text-[#1769AA] uppercase tracking-wider border-b border-[#D9E2EA] pb-2">
              Recent Expert Human Review Submissions
            </h4>
            <div className="space-y-2">
              {loadingFeedback ? (
                <div className="py-8 text-center text-[#1769AA] animate-pulse">Loading feedback submissions...</div>
              ) : !feedbackStats?.recent_feedbacks?.length ? (
                <div className="py-8 text-center text-[#718394]">No human reviews submitted yet. Submit reviews in Report Detail Modal.</div>
              ) : (
                feedbackStats.recent_feedbacks.map((fb) => (
                  <div key={fb.id} className="p-3.5 rounded-xl bg-[#F4F7FA] border border-[#D9E2EA] space-y-1.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                          fb.rating === 'CORRECT' ? 'bg-emerald-50 text-emerald-800 border-emerald-200' :
                          fb.rating === 'PARTIALLY_CORRECT' ? 'bg-amber-50 text-amber-800 border-amber-200' :
                          'bg-rose-50 text-rose-800 border-rose-200'
                        }`}>
                          {fb.rating}
                        </span>
                        <span className="font-bold text-[#172B3A]">{fb.reviewer_name} ({fb.reviewer_role})</span>
                        <span className="text-[#526575]">• Report: <strong className="text-[#1769AA]">{fb.report_id}</strong></span>
                      </div>
                      <span className="text-[#718394] text-[11px]">{new Date(fb.submitted_at).toLocaleString()}</span>
                    </div>
                    {fb.comments && (
                      <p className="text-xs font-sans text-[#172B3A] bg-white p-2 rounded-lg border border-[#D9E2EA]">
                        "{fb.comments}"
                      </p>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
