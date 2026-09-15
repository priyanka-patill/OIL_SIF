import React, { useState, useEffect } from 'react';
import {
  SafetyReport,
  ReportAnalysis,
  AIFeedback,
  ReportBarrierResponse,
  BDIResponse,
  ReportSIFEscalationResponse,
  SafetyActionResponse,
  SafetyHoldResponse,
} from '../../types/safety';
import { Modal } from '../common/Modal';
import { RiskBadge } from '../common/RiskBadge';
import { SIFBadge } from '../common/SIFBadge';
import { EmailPreviewModal } from '../notifications/EmailPreviewModal';
import { AuditTimelineView } from '../audit/AuditTimelineView';
import { api } from '../../services/api';

interface ReportDetailModalProps {
  report: SafetyReport | null;
  isOpen: boolean;
  onClose: () => void;
  onActionUpdated?: () => void;
}

interface ChatMessage {
  sender: 'user' | 'ai';
  text: string;
  suggestedActions?: string[];
  timestamp: string;
}

export const ReportDetailModal: React.FC<ReportDetailModalProps> = ({
  report,
  isOpen,
  onClose,
  onActionUpdated,
}) => {
  const [activeTab, setActiveTab] = useState<
    'intelligence' | 'sif_pathway' | 'recommendations' | 'action_sla' | 'ask_ai' | 'feedback' | 'audit_trail'
  >('intelligence');


  // Core Data States
  const [analysis, setAnalysis] = useState<ReportAnalysis | null>(null);
  const [barrierData, setBarrierData] = useState<ReportBarrierResponse | null>(null);
  const [bdiData, setBdiData] = useState<BDIResponse | null>(null);
  const [sifEscData, setSifEscData] = useState<ReportSIFEscalationResponse | null>(null);
  const [actionsData, setActionsData] = useState<SafetyActionResponse[]>([]);
  const [holdsData, setHoldsData] = useState<SafetyHoldResponse[]>([]);
  const [feedbackList, setFeedbackList] = useState<AIFeedback[]>([]);
  const [loading, setLoading] = useState(false);

  // Action Management Form State
  const [actionStatus, setActionStatus] = useState<string>('Open');
  const [assignedTo, setAssignedTo] = useState<string>('');
  const [assignedDept, setAssignedDept] = useState<string>('');
  const [dueDate, setDueDate] = useState<string>('');
  const [comments, setComments] = useState<string>('');
  const [verifiedBy, setVerifiedBy] = useState<string>('');
  const [updatingAction, setUpdatingAction] = useState(false);
  const [actionSuccess, setActionSuccess] = useState(false);

  // Email Preview Modal State
  const [isEmailModalOpen, setIsEmailModalOpen] = useState(false);
  const [notificationType, setNotificationType] = useState<
    'HIGH_RISK' | 'ACTION_ASSIGNMENT' | 'OVERDUE_ACTION' | 'MANAGEMENT_ESCALATION'
  >('HIGH_RISK');

  // Report Specific Chat State
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Human Feedback Form State
  const [reviewerName, setReviewerName] = useState('Safety Officer');
  const [agreesWithAI, setAgreesWithAI] = useState(true);
  const [humanRisk, setHumanRisk] = useState<string>('High');
  const [humanSIF, setHumanSIF] = useState<string>('YES');
  const [feedbackReason, setFeedbackReason] = useState('');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);

  useEffect(() => {
    if (!report || !isOpen) return;

    setLoading(true);
    setFeedbackSuccess(false);
    setActionSuccess(false);
    setActiveTab('intelligence');

    // Sync action form with report fields
    setActionStatus(report.action_status || 'Open');
    setAssignedTo(report.assigned_to || '');
    setAssignedDept(report.assigned_department || report.department || '');
    setDueDate(report.due_date ? report.due_date.split('T')[0] : '');
    setComments(report.action_comments || '');
    setVerifiedBy(report.closure_verified_by || '');

    // Reset report-specific chat
    setChatMessages([
      {
        sender: 'ai',
        text: `### OIL Safety Intelligence: Report ${report.original_id || report.id}\n\nI have loaded full telemetry for this report, including **Barrier Degradation (BDI)**, **Swiss Cheese Defense Layers**, **SIF Precursor Escalation**, and **Action SLA Governance**.\n\nAsk me any questions below:`,
        suggestedActions: [
          'Why was this report escalated?',
          'Why is BDI high?',
          'Which barriers are degraded?',
          'What is the 7-stage precursor pathway?',
          'What immediate containment is recommended?',
          'What is the SLA and Safety Hold status?',
        ],
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);

    // Fetch all Phase 1-6 Intelligence endpoints in parallel
    Promise.allSettled([
      api.getReportAnalysis(report.id),
      api.getReportBarriers(report.id),
      api.getReportBDI(report.id),
      api.getReportSIFEscalation(report.id),
      api.getSafetyActions({ report_id: report.id }),
      api.getSafetyHolds({ report_id: report.id }),
      api.getAIFeedback(report.id),
    ])
      .then(([aRes, bRes, bdiRes, sifRes, actRes, hldRes, fbRes]) => {
        if (aRes.status === 'fulfilled') setAnalysis(aRes.value);
        if (bRes.status === 'fulfilled') setBarrierData(bRes.value);
        if (bdiRes.status === 'fulfilled') setBdiData(bdiRes.value);
        if (sifRes.status === 'fulfilled') setSifEscData(sifRes.value);
        if (actRes.status === 'fulfilled') setActionsData(actRes.value || []);
        if (hldRes.status === 'fulfilled') setHoldsData(hldRes.value || []);
        if (fbRes.status === 'fulfilled') setFeedbackList(fbRes.value || []);
      })
      .finally(() => setLoading(false));
  }, [report, isOpen]);

  const handleSendReportChat = async (queryText?: string) => {
    const text = queryText || chatInput;
    if (!text.trim() || !report || chatLoading) return;

    const userMsg: ChatMessage = {
      sender: 'user',
      text: text,
      timestamp: new Date().toLocaleTimeString(),
    };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput('');
    setChatLoading(true);

    try {
      const res = await api.sendChatMessage(text, report.id);
      const aiMsg: ChatMessage = {
        sender: 'ai',
        text: res.reply,
        suggestedActions: res.suggested_actions,
        timestamp: new Date().toLocaleTimeString(),
      };
      setChatMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'ai',
          text: ` Query error: ${err.message}`,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleUpdateAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!report) return;

    setUpdatingAction(true);
    setActionSuccess(false);

    try {
      await api.updateAction(report.id, {
        action_status: actionStatus,
        assigned_to: assignedTo || null,
        assigned_department: assignedDept || null,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
        action_comments: comments || null,
        closure_verified_by: actionStatus === 'Closed' ? (verifiedBy || 'Safety Officer') : null,
        actor_name: reviewerName || 'Safety Officer',
        actor_role: 'Safety Officer',
      });
      setActionSuccess(true);
      onActionUpdated?.();
    } catch (err: any) {
      alert(`Failed to update action: ${err.message}`);
    } finally {
      setUpdatingAction(false);
    }
  };

  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!report || !feedbackReason.trim()) return;

    setSubmittingFeedback(true);
    try {
      const fb = await api.submitAIFeedback({
        report_id: report.id,
        reviewer_name: reviewerName,
        agrees_with_ai: agreesWithAI,
        human_risk_level: humanRisk,
        human_sif_precursor: humanSIF,
        feedback_reason: feedbackReason,
      });
      setFeedbackList([fb, ...feedbackList]);
      setFeedbackReason('');
      setFeedbackSuccess(true);
    } catch (err: any) {
      alert(`Feedback submission failed: ${err.message}`);
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const triggerEscalationEmail = (
    type: 'HIGH_RISK' | 'ACTION_ASSIGNMENT' | 'OVERDUE_ACTION' | 'MANAGEMENT_ESCALATION'
  ) => {
    setNotificationType(type);
    setIsEmailModalOpen(true);
  };

  if (!report) return null;

  // Barrier badge color helper
  const getBarrierStatusBadge = (st: string) => {
    switch (st?.toUpperCase()) {
      case 'INTACT':
        return 'bg-emerald-50 text-emerald-800 border-emerald-300';
      case 'DEGRADED':
        return 'bg-amber-50 text-amber-800 border-amber-300';
      case 'FAILED':
        return 'bg-rose-50 text-rose-800 border-rose-300';
      default:
        return 'bg-[#EEF3F7] text-[#526575] border-[#D9E2EA]';
    }
  };

  // SIF Severity badge helper
  const getSIFSeverityBadge = (sev?: string) => {
    switch (sev?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-rose-100 text-rose-800 border-rose-300 animate-pulse';
      case 'HIGH':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'ELEVATED':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'WATCH':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-[#EEF3F7] text-[#526575] border-[#D9E2EA]';
    }
  };

  const primaryAction = actionsData.length > 0 ? actionsData[0] : null;
  const primaryHold = holdsData.length > 0 ? holdsData[0] : null;

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title={`Safety Intelligence Dossier: ${report.original_id || report.id}`}
        subtitle={`${report.refinery_unit || 'Process Plant'} • ${report.department || 'Operations'} • Ingested Record`}
        size="2xl"
      >
        <div className="space-y-5 text-[#172B3A]">
          {/* Top Bar Badges & Quick Action */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-[#EEF3F7] p-3.5 rounded-xl border border-[#D9E2EA] shadow-sm">
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className="font-mono text-xs font-bold text-[#1769AA] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                {report.original_id || report.id}
              </span>
              <RiskBadge level={report.risk_level} size="sm" />
              {sifEscData && (
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${getSIFSeverityBadge(
                    sifEscData.severity
                  )}`}
                >
                  SIF: {sifEscData.severity}
                </span>
              )}
              {bdiData && (
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-50 text-purple-800 border border-purple-200">
                  BDI: {bdiData.bdi_score.toFixed(1)} ({bdiData.classification})
                </span>
              )}
              {primaryHold && (
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-50 text-rose-800 border border-rose-200 flex items-center gap-1">
                  HOLD: {primaryHold.status}
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => triggerEscalationEmail('HIGH_RISK')}
                className="px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-mono text-xs font-semibold transition-all flex items-center gap-1.5 shadow-sm"
              >
                Escalate / Notify
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('action_sla')}
                className="px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-[#1769AA] border border-blue-200 font-mono text-xs font-semibold transition-all flex items-center gap-1.5 shadow-sm"
              >
                Action & SLA
              </button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1.5 border-b border-[#D9E2EA] pb-2 text-xs font-mono overflow-x-auto custom-scrollbar">
            <button
              onClick={() => setActiveTab('intelligence')}
              className={`px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                activeTab === 'intelligence'
                  ? 'bg-[#1769AA] text-white font-bold shadow-sm'
                  : 'text-[#526575] hover:text-[#172B3A] hover:bg-[#EEF3F7]'
              }`}
            >
              1. Source Data & Barriers
            </button>
            <button
              onClick={() => setActiveTab('sif_pathway')}
              className={`px-3 py-1.5 rounded-lg transition-all shrink-0 flex items-center gap-1 ${
                activeTab === 'sif_pathway'
                  ? 'bg-[#1769AA] text-white font-bold shadow-sm'
                  : 'text-[#526575] hover:text-[#172B3A] hover:bg-[#EEF3F7]'
              }`}
            >
              2. SIF 7-Stage Pathway
            </button>
            <button
              onClick={() => setActiveTab('recommendations')}
              className={`px-3 py-1.5 rounded-lg transition-all shrink-0 flex items-center gap-1 ${
                activeTab === 'recommendations'
                  ? 'bg-[#1769AA] text-white font-bold shadow-sm'
                  : 'text-[#526575] hover:text-[#172B3A] hover:bg-[#EEF3F7]'
              }`}
            >
              3. AI Recommendations
            </button>
            <button
              onClick={() => setActiveTab('action_sla')}
              className={`px-3 py-1.5 rounded-lg transition-all shrink-0 flex items-center gap-1 ${
                activeTab === 'action_sla'
                  ? 'bg-[#1769AA] text-white font-bold shadow-sm'
                  : 'text-[#526575] hover:text-[#172B3A] hover:bg-[#EEF3F7]'
              }`}
            >
              4. Action Control & SLA
            </button>
            <button
              onClick={() => setActiveTab('ask_ai')}
              className={`px-3 py-1.5 rounded-lg transition-all shrink-0 flex items-center gap-1 ${
                activeTab === 'ask_ai'
                  ? 'bg-[#1769AA] text-white font-bold shadow-sm'
                  : 'text-[#526575] hover:text-[#172B3A] hover:bg-[#EEF3F7]'
              }`}
            >
              5. Ask AI
            </button>
            <button
              onClick={() => setActiveTab('feedback')}
              className={`px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                activeTab === 'feedback'
                  ? 'bg-[#1769AA] text-white font-bold shadow-sm'
                  : 'text-[#526575] hover:text-[#172B3A] hover:bg-[#EEF3F7]'
              }`}
            >
              6. Human Review
            </button>
            <button
              onClick={() => setActiveTab('audit_trail')}
              className={`px-3 py-1.5 rounded-lg transition-all shrink-0 flex items-center gap-1 ${
                activeTab === 'audit_trail'
                  ? 'bg-[#1769AA] text-white font-bold shadow-sm'
                  : 'text-[#526575] hover:text-[#172B3A] hover:bg-[#EEF3F7]'
              }`}
            >
              7. Audit Trail
            </button>
          </div>


          {/* TAB 1: SOURCE DATA & SWISS CHEESE BARRIERS */}
          {activeTab === 'intelligence' && (
            <div className="space-y-5">
              {/* Section 1: Source Recorded Data */}
              <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-xl p-4 space-y-3 shadow-sm">
                <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-[#172B3A] uppercase tracking-wider">
                      Source Report Telemetry
                    </span>
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-blue-50 text-[#1769AA] border border-blue-200 font-semibold">
                      RECORDED DATA
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-[#1769AA]">
                    ID: {report.original_id || report.id}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                  <div>
                    <span className="text-[#718394] uppercase text-[10px] block">REPORT ID</span>
                    <span className="text-[#1769AA] font-bold">{report.original_id || report.id}</span>
                  </div>
                  <div>
                    <span className="text-[#718394] uppercase text-[10px] block">SUBMITTED BY</span>
                    <span className="text-[#172B3A] font-bold">{report.submitting_user || 'Supervisor'}</span>
                  </div>
                  <div>
                    <span className="text-[#718394] uppercase text-[10px] block">SUBMISSION TIME</span>
                    <span className="text-[#172B3A]">{report.created_at ? new Date(report.created_at).toLocaleString() : 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-[#718394] uppercase text-[10px] block">ANALYSIS STATUS</span>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span
                        className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded uppercase ${
                          report.analysis_status === 'COMPLETED' || (!report.analysis_status && analysis)
                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                            : report.analysis_status === 'FAILED'
                            ? 'bg-rose-100 text-rose-800 border border-rose-300'
                            : 'bg-amber-100 text-amber-800 border border-amber-300 animate-pulse'
                        }`}
                      >
                        {report.analysis_status === 'FAILED'
                          ? 'FAILED'
                          : report.analysis_status === 'IN_PROGRESS'
                          ? 'ANALYZING...'
                          : 'COMPLETED'}
                      </span>
                      {report.analysis_status === 'FAILED' && (
                        <button
                          type="button"
                          onClick={async () => {
                            try {
                              setLoading(true);
                              const res = await api.analyzeReport(report.id);
                              setAnalysis(res);
                              report.analysis_status = 'COMPLETED';
                              if (onActionUpdated) onActionUpdated();
                            } catch (e) {
                              console.error(e);
                            } finally {
                              setLoading(false);
                            }
                          }}
                          className="px-2 py-0.5 bg-amber-500 hover:bg-amber-400 text-white font-mono font-bold text-[10px] rounded transition-all shadow-sm"
                        >
                          Retry Analysis
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono pt-1">
                  <div>
                    <span className="text-[#718394] uppercase text-[10px] block">REFINERY UNIT</span>
                    <span className="text-[#172B3A] font-bold">{report.refinery_unit || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-[#718394] uppercase text-[10px] block">EQUIPMENT</span>
                    <span className="text-[#172B3A] font-bold">{report.equipment || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-[#718394] uppercase text-[10px] block">WORK TYPE</span>
                    <span className="text-[#172B3A]">{report.work_type || 'General'}</span>
                  </div>
                  <div>
                    <span className="text-[#718394] uppercase text-[10px] block">DEPARTMENT</span>
                    <span className="text-[#172B3A]">{report.department || 'Operations'}</span>
                  </div>
                </div>

                <div className="space-y-2 pt-1 font-sans text-xs">
                  <div>
                    <span className="text-[10px] font-mono uppercase text-[#526575] font-bold block mb-1">
                      Observed Problem / Exposure:
                    </span>
                    <div className="p-3 rounded-lg bg-white border border-[#D9E2EA] text-[#172B3A] leading-relaxed font-mono text-xs">
                      {report.description || 'No description recorded.'}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <span className="text-[10px] font-mono uppercase text-[#526575] font-bold block mb-1">
                        Immediate Cause:
                      </span>
                      <div className="p-2.5 rounded-lg bg-white border border-[#D9E2EA] text-[#172B3A] text-xs font-mono">
                        {report.immediate_cause || 'Not specified'}
                      </div>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase text-[#526575] font-bold block mb-1">
                        Potential Consequence:
                      </span>
                      <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs font-mono">
                        {report.potential_consequence || 'Personnel hazard'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Section 1.5: IOGP Life-Saving Rule & Recurrence Intelligence */}
              {analysis && (
                <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-xl p-4 space-y-3 shadow-sm">
                  <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-[#172B3A] uppercase tracking-wider">
                        IOGP Life-Saving Rule & Recurrence Intelligence
                      </span>
                      <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-blue-50 text-[#1769AA] border border-blue-200 font-semibold">
                        EXPLAINABLE AI
                      </span>
                    </div>
                    {analysis.human_overridden && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300 font-bold">
                         HUMAN OVERRIDDEN ({analysis.human_risk_level || 'Custom'})
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                    {/* IOGP Rule Card */}
                    <div className="p-3 rounded-lg bg-white border border-[#D9E2EA] space-y-1.5">
                      <span className="text-[#526575] uppercase text-[10px] block font-bold">
                        IOGP LIFE-SAVING RULE MATCH
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="px-2.5 py-1 rounded bg-amber-100 text-amber-900 border border-amber-300 font-bold text-xs">
                          {analysis.iogp_rule || 'No clear match'}
                        </span>
                        {analysis.iogp_confidence && (
                          <span className="text-[10px] text-[#718394]">
                            Confidence: {Math.round(analysis.iogp_confidence * 100)}%
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] font-sans text-[#526575] leading-relaxed pt-1">
                        {analysis.iogp_reasoning || 'Automated rule classification based on narrative keywords.'}
                      </p>
                      {analysis.secondary_iogp_rules && analysis.secondary_iogp_rules.length > 0 && (
                        <div className="text-[10px] text-[#718394] pt-1">
                          Secondary Rules: <span className="text-[#172B3A]">{analysis.secondary_iogp_rules.join(', ')}</span>
                        </div>
                      )}
                    </div>

                    {/* Recurrence Intelligence Card */}
                    <div className="p-3 rounded-lg bg-white border border-[#D9E2EA] space-y-1.5">
                      <span className="text-[#526575] uppercase text-[10px] block font-bold">
                        HISTORICAL RECURRENCE INTELLIGENCE
                      </span>
                      <div className="flex items-center gap-2">
                        <span className={`px-2.5 py-1 rounded font-bold text-xs border ${analysis.is_recurring ? 'bg-rose-100 text-rose-800 border-rose-300' : 'bg-emerald-100 text-emerald-800 border-emerald-300'}`}>
                          {analysis.is_recurring ? 'RECURRING ISSUE DETECTED' : 'FIRST-TIME / ISOLATED EVENT'}
                        </span>
                        <span className="text-[10px] text-[#718394]">
                          Score: {Math.round((analysis.recurrence_score || 0) * 100)}%
                        </span>
                      </div>
                      <div className="text-[11px] font-sans text-[#526575] space-y-1 pt-1">
                        {analysis.recurrence_details?.equipment_occurrences_in_dataset > 1 && (
                          <div>• Equipment repeated: <strong>{analysis.recurrence_details.equipment_occurrences_in_dataset} occurrences</strong> in dataset</div>
                        )}
                        {analysis.recurrence_details?.unit_occurrences_in_dataset > 1 && (
                          <div>• Unit repeat frequency: <strong>{analysis.recurrence_details.unit_occurrences_in_dataset} occurrences</strong> in unit</div>
                        )}
                        {analysis.recurrence_details?.recorded_previous_similar_reports > 0 && (
                          <div>• Prior reported events: <strong>{analysis.recurrence_details.recorded_previous_similar_reports} similar reports</strong></div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Section 2: Swiss Cheese Barrier Model & BDI */}
              <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-xl p-4 space-y-4 shadow-sm">
                <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-[#172B3A] uppercase tracking-wider">
                      Swiss Cheese Barrier Defense Layers (Phase 2 & 3)
                    </span>
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-purple-50 text-purple-800 border border-purple-200 font-semibold">
                      ANALYTICAL INDICATOR
                    </span>
                  </div>
                  {bdiData && (
                    <span className="text-[10px] font-mono font-bold text-purple-700">
                      BDI: {bdiData.bdi_score.toFixed(1)} / 100 • {bdiData.classification}
                    </span>
                  )}
                </div>

                {/* Swiss Cheese Layers Table */}
                {barrierData?.barriers && barrierData.barriers.length > 0 ? (
                  <div className="space-y-2">
                    <div className="grid grid-cols-12 gap-2 text-[10px] font-mono text-[#718394] uppercase border-b border-[#D9E2EA] pb-1">
                      <div className="col-span-4">Barrier Layer</div>
                      <div className="col-span-2">Status</div>
                      <div className="col-span-6">Observed Degradation Reasoning & Evidence</div>
                    </div>

                    {barrierData.barriers.map((bar, idx) => (
                      <div
                        key={idx}
                        className="grid grid-cols-12 gap-2 p-2.5 rounded-lg bg-white border border-[#D9E2EA] items-start text-xs font-mono"
                      >
                        <div className="col-span-4">
                          <span className="font-bold text-[#172B3A] block">{bar.barrier_name}</span>
                          <span className="text-[10px] text-[#718394]">{bar.barrier_type}</span>
                        </div>
                        <div className="col-span-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold border inline-block ${getBarrierStatusBadge(
                              bar.status
                            )}`}
                          >
                            {bar.status}
                          </span>
                        </div>
                        <div className="col-span-6 space-y-1">
                          <p className="text-[#526575] text-[11px] font-sans leading-relaxed">
                            {bar.reasoning || 'Defense layer verified.'}
                          </p>
                          {bar.evidence_phrases && bar.evidence_phrases.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {bar.evidence_phrases.map((phrase, pIdx) => (
                                <span
                                  key={pIdx}
                                  className="text-[9px] px-1.5 py-0.2 rounded bg-blue-50 text-[#1769AA] border border-blue-200"
                                >
                                  "{phrase}"
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-3 bg-white rounded-lg border border-[#D9E2EA] text-xs font-mono text-[#718394]">
                    Evaluating Swiss Cheese barrier layers for this observation...
                  </div>
                )}

                {/* Multi-Barrier Convergence Banner */}
                {barrierData?.multi_barrier_convergence && (
                  <div className="p-3 rounded-lg bg-rose-50 border border-rose-300 text-xs font-mono text-rose-800 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-base"></span>
                      <div>
                        <span className="font-bold uppercase tracking-wider block text-rose-900">
                          MULTI-BARRIER CONVERGENCE IDENTIFIED
                        </span>
                        <span className="text-[11px] text-rose-800 font-sans">
                          Multiple barrier layers (PPE, maintenance, or procedural compliance) appear simultaneously degraded.
                        </span>
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded bg-rose-600 text-white text-[10px] font-bold">
                      CONVERGED
                    </span>
                  </div>
                )}

                {/* Analytical Disclaimer */}
                <p className="text-[10px] font-mono text-[#718394] italic pt-1 border-t border-[#D9E2EA]">
                   Analytical indicator derived from observed safety data — not an official organizational risk score or accident probability.
                </p>
              </div>
            </div>
          )}

          {/* TAB 2: SIF PRECURSOR ESCALATION & 7-STAGE PATHWAY */}
          {activeTab === 'sif_pathway' && (
            <div className="space-y-5">
              <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-xl p-4 space-y-4 shadow-sm">
                <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-[#172B3A] uppercase tracking-wider">
                      SIF Precursor Escalation Analysis (Phase 4)
                    </span>
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-amber-100 text-amber-900 border border-amber-300 font-semibold">
                      AI ESCALATION ENGINE
                    </span>
                  </div>
                  {sifEscData && (
                    <span
                      className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-bold border ${getSIFSeverityBadge(
                        sifEscData.severity
                      )}`}
                    >
                      ESCALATION: {sifEscData.severity}
                    </span>
                  )}
                </div>

                {/* Why Escalated Narrative */}
                <div className="p-3.5 rounded-xl bg-white border border-[#D9E2EA] space-y-2">
                  <span className="text-[10px] font-mono uppercase text-[#526575] font-bold block">
                    Why Was This Report Escalated?
                  </span>
                  <p className="text-xs font-sans text-[#172B3A] leading-relaxed">
                    {sifEscData?.why_escalated ||
                      'The system detected convergence of unmitigated energy hazard, control barrier degradation, and potential high-consequence exposure pathway.'}
                  </p>
                  {sifEscData?.contributing_factors && sifEscData.contributing_factors.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      <span className="text-[10px] font-mono text-[#718394] uppercase">
                        Contributing Factors:
                      </span>
                      {sifEscData.contributing_factors.map((f, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-[#1769AA] font-mono text-[10px]"
                        >
                          {f}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* 7-Stage Precursor Scenario Pathway */}
                <div className="space-y-2">
                  <span className="text-[10px] font-mono uppercase text-[#526575] font-bold block">
                    7-Stage Precursor Escalation Scenario Pathway:
                  </span>

                  {sifEscData?.escalation_scenario && sifEscData.escalation_scenario.length > 0 ? (
                    <div className="space-y-2">
                      {sifEscData.escalation_scenario.map((st, idx) => (
                        <div
                          key={idx}
                          className={`p-3 rounded-lg border flex items-start gap-3 transition-all ${
                            st.is_active
                              ? 'bg-rose-50 border-rose-300 shadow-sm'
                              : 'bg-white border-[#D9E2EA]'
                          }`}
                        >
                          <div
                            className={`h-6 w-6 rounded-full flex items-center justify-center font-mono text-xs font-bold shrink-0 ${
                              st.is_active
                                ? 'bg-rose-600 text-white'
                                : 'bg-[#EEF3F7] text-[#526575]'
                            }`}
                          >
                            {st.stage_number}
                          </div>
                          <div className="space-y-1 flex-1">
                            <div className="flex items-center justify-between">
                              <h5 className="font-mono text-xs font-bold text-[#172B3A]">
                                {st.stage_name}
                              </h5>
                              {st.is_active && (
                                <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-rose-100 text-rose-800 border border-rose-300 font-bold">
                                  ACTIVE PATHWAY
                                </span>
                              )}
                            </div>
                            <p className="text-[11px] font-sans text-[#526575] leading-relaxed">
                              {st.description}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-3 bg-white rounded-lg border border-[#D9E2EA] text-xs font-mono text-[#718394]">
                      Generating structured 7-stage precursor scenario pathway...
                    </div>
                  )}
                </div>

                <p className="text-[10px] font-mono text-[#718394] italic pt-1 border-t border-[#D9E2EA]">
                   Potential precursor escalation — not a guaranteed incident prediction.
                </p>
              </div>
            </div>
          )}

          {/* TAB 3: AI RECOMMENDATIONS */}
          {activeTab === 'recommendations' && (
            <div className="space-y-4">
              <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-xl p-4 space-y-4 shadow-sm">
                <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-[#172B3A] uppercase tracking-wider">
                      Context-Aware AI Safety Recommendations
                    </span>
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-blue-50 text-[#1769AA] border border-blue-200 font-semibold">
                      AI RECOMMENDATION
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-[#718394]">
                    HUMAN-IN-THE-LOOP APPROVAL REQUIRED
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Immediate Containment */}
                  <div className="p-3.5 rounded-xl bg-white border border-blue-200 space-y-2 shadow-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-[#1769AA] text-sm"></span>
                      <h5 className="font-mono text-xs font-bold text-[#1769AA] uppercase">
                        Immediate Containment Action
                      </h5>
                    </div>
                    <p className="text-xs font-sans text-[#172B3A] leading-relaxed">
                      {sifEscData?.recommended_immediate_action ||
                        analysis?.immediate_action_recommendation ||
                        'Temporarily pause work, isolate energy sources, and verify barrier integrity prior to continuation.'}
                    </p>
                  </div>

                  {/* Preventive Action */}
                  <div className="p-3.5 rounded-xl bg-white border border-emerald-200 space-y-2 shadow-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-[#2E8B57] text-sm"></span>
                      <h5 className="font-mono text-xs font-bold text-[#2E8B57] uppercase">
                        Preventive & Remediation Action
                      </h5>
                    </div>
                    <p className="text-xs font-sans text-[#172B3A] leading-relaxed">
                      {sifEscData?.recommended_preventive_action ||
                        analysis?.preventive_action_recommendation ||
                        'Implement mandatory pre-task verification checklist, inspect equipment, and audit compliance.'}
                    </p>
                  </div>
                </div>

                {/* Recurrence Prevention & Reliability Controls */}
                <div className="p-3.5 rounded-xl bg-white border border-purple-200 space-y-2 shadow-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-purple-700 text-sm"></span>
                    <h5 className="font-mono text-xs font-bold text-purple-700 uppercase">
                      Systemic Recurrence Prevention & Engineering Controls
                    </h5>
                  </div>
                  <p className="text-xs font-sans text-[#172B3A] leading-relaxed">
                    {sifEscData?.what_remains_unresolved
                      ? `Unresolved factor: ${sifEscData.what_remains_unresolved}. Enforce preventative maintenance cycles and safety barrier verification.`
                      : 'Conduct unit-wide supervisor walk-through and verify corrective actions across similar equipment.'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: ACTION CONTROL & SLA */}
          {activeTab === 'action_sla' && (
            <div className="space-y-5">
              {/* Live SLA & Escalation Telemetry */}
              {primaryAction && (
                <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-xl p-4 space-y-3 shadow-sm">
                  <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-[#172B3A] uppercase tracking-wider">
                        Agentic Action Telemetry & Live SLA Tracker
                      </span>
                      <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-blue-50 text-[#1769AA] border border-blue-200 font-semibold">
                        ACTION ENGINE
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-[#718394]">
                      ID: {primaryAction.id.slice(0, 8)}...
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                    <div>
                      <span className="text-[#718394] uppercase text-[10px] block">ACTION STATUS</span>
                      <span className="text-[#1769AA] font-bold">{primaryAction.status}</span>
                    </div>
                    <div>
                      <span className="text-[#718394] uppercase text-[10px] block">RESPONSIBLE ROLE</span>
                      <span className="text-[#172B3A] font-bold">{primaryAction.assigned_role}</span>
                    </div>
                    <div>
                      <span className="text-[#718394] uppercase text-[10px] block">SLA STATE</span>
                      <span
                        className={`font-bold ${
                          primaryAction.sla_state === 'BREACHED'
                            ? 'text-rose-600'
                            : primaryAction.sla_state === 'APPROACHING_DEADLINE'
                            ? 'text-amber-600'
                            : 'text-emerald-600'
                        }`}
                      >
                        {primaryAction.sla_state || 'NORMAL'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[#718394] uppercase text-[10px] block">ESCALATION LEVEL</span>
                      <span className="text-[#172B3A] font-bold">
                        Level {primaryAction.escalation_level}
                      </span>
                    </div>
                  </div>

                  {/* Digital Safety Hold Box if exists */}
                  {primaryHold && (
                    <div className="p-3 rounded-lg bg-rose-50 border border-rose-300 text-xs font-mono space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-rose-800 font-bold flex items-center gap-1.5">
                          ACTIVE DIGITAL SAFETY HOLD
                        </span>
                        <span className="px-2 py-0.5 rounded bg-rose-600 text-white font-bold text-[10px]">
                          {primaryHold.status}
                        </span>
                      </div>
                      <p className="text-[11px] text-rose-900 font-sans">
                        Trigger: <strong>{primaryHold.trigger}</strong> • Requested by:{' '}
                        {primaryHold.requested_by}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Action Update Form */}
              <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-xl p-4 space-y-4 shadow-sm">
                <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
                  <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] flex items-center gap-2">
                    Update Safety Action Record & Governance
                  </h4>
                  <span className="text-[10px] font-mono text-[#1769AA]">AUDIT LOGGED</span>
                </div>

                {actionSuccess && (
                  <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-300 text-xs font-mono text-emerald-800">
                    Action record updated and audit log entry created!
                  </div>
                )}

                <form onSubmit={handleUpdateAction} className="space-y-3 text-xs font-mono">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                      <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">
                        Action Status
                      </label>
                      <select
                        value={actionStatus}
                        onChange={(e) => setActionStatus(e.target.value)}
                        className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                      >
                        <option value="Open">Open</option>
                        <option value="In Progress">In Progress</option>
                        <option value="Under Review">Under Review</option>
                        <option value="Overdue">Overdue</option>
                        <option value="Closed">Closed / Verified</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">
                        Assigned Person
                      </label>
                      <input
                        type="text"
                        value={assignedTo}
                        onChange={(e) => setAssignedTo(e.target.value)}
                        placeholder="e.g. Lead HSE Engineer"
                        className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                      />
                    </div>

                    <div>
                      <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">
                        Target Due Date
                      </label>
                      <input
                        type="date"
                        value={dueDate}
                        onChange={(e) => setDueDate(e.target.value)}
                        className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">
                      Action Comments / Remediation Justification
                    </label>
                    <textarea
                      value={comments}
                      onChange={(e) => setComments(e.target.value)}
                      placeholder="Document physical barrier installation, engineering checks, or field closure evidence..."
                      rows={2}
                      className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] font-sans focus:outline-none focus:border-[#1769AA]"
                    />
                  </div>

                  <div className="flex justify-end gap-3 pt-2">
                    <button
                      type="submit"
                      disabled={updatingAction}
                      className="px-5 py-2 rounded-xl bg-[#1769AA] hover:bg-[#123B5D] text-white font-mono text-xs font-bold transition-all shadow-sm disabled:opacity-50"
                    >
                      {updatingAction ? 'Saving Changes...' : 'Save & Log Action '}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* TAB 5: ASK AI ABOUT THIS REPORT */}
          {activeTab === 'ask_ai' && (
            <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-xl flex flex-col h-[460px] overflow-hidden shadow-sm">
              {/* Quick Query Bar */}
              <div className="p-2.5 bg-[#EEF3F7] border-b border-[#D9E2EA] flex items-center gap-1.5 overflow-x-auto custom-scrollbar text-[11px] font-mono">
                <span className="text-[#526575] text-[10px] uppercase font-bold shrink-0">
                  SUGGESTED:
                </span>
                {[
                  'Why was this report escalated?',
                  'Why is BDI high?',
                  'Which barriers are degraded?',
                  'What is the 7-stage precursor pathway?',
                  'What immediate containment is recommended?',
                ].map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendReportChat(q)}
                    className="px-2.5 py-1 rounded-lg bg-white hover:bg-blue-50 text-[#172B3A] hover:text-[#1769AA] border border-[#D9E2EA] hover:border-[#1769AA] shrink-0 text-[11px] transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>

              {/* Chat Thread */}
              <div className="flex-1 p-4 overflow-y-auto custom-scrollbar space-y-3">
                {chatMessages.map((m, idx) => (
                  <div
                    key={idx}
                    className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
                  >
                    <div
                      className={`max-w-2xl rounded-xl p-3.5 text-xs font-sans leading-relaxed ${
                        m.sender === 'user'
                          ? 'bg-[#1769AA] text-white shadow-sm rounded-br-none font-medium'
                          : 'bg-white border border-[#D9E2EA] text-[#172B3A] rounded-bl-none shadow-sm'
                      }`}
                    >
                      <div className="whitespace-pre-wrap font-sans text-xs space-y-2">
                        {m.text}
                      </div>

                      {m.suggestedActions && m.suggestedActions.length > 0 && (
                        <div className="mt-2.5 pt-2.5 border-t border-[#D9E2EA] flex flex-wrap gap-1.5">
                          {m.suggestedActions.map((act, i) => (
                            <button
                              key={i}
                              onClick={() => handleSendReportChat(act)}
                              className="px-2 py-0.5 rounded-full bg-blue-50 hover:bg-blue-100 text-[#1769AA] border border-blue-200 font-mono text-[10px]"
                            >
                              {act}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                    <span className="text-[9px] font-mono text-[#718394] mt-1 px-1">
                      {m.sender === 'user' ? 'YOU' : 'AI ASSISTANT'} • {m.timestamp}
                    </span>
                  </div>
                ))}
                {chatLoading && (
                  <div className="flex items-center gap-2 text-xs font-mono text-[#1769AA] p-2.5 bg-white rounded-lg border border-[#D9E2EA] w-fit animate-pulse shadow-sm">
                    <span className="h-2 w-2 rounded-full bg-[#1769AA] animate-ping" />
                    <span>Analyzing barrier convergence, BDI indicators, and escalation rules...</span>
                  </div>
                )}
              </div>

              {/* Chat Input */}
              <div className="p-3 border-t border-[#D9E2EA] bg-[#EEF3F7]">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendReportChat();
                  }}
                  className="flex items-center gap-2"
                >
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ask about barrier states, BDI drivers, SIF escalation reasons, or required containment..."
                    className="flex-1 bg-white border border-[#D9E2EA] focus:border-[#1769AA] rounded-xl px-3.5 py-2 text-xs font-sans text-[#172B3A] placeholder-[#718394] focus:outline-none"
                  />
                  <button
                    type="submit"
                    disabled={chatLoading || !chatInput.trim()}
                    className="px-5 py-2 rounded-xl bg-[#1769AA] hover:bg-[#123B5D] text-white font-mono text-xs font-bold transition-all disabled:opacity-40 shadow-sm"
                  >
                    Send 
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* TAB 6: EXPERT HUMAN REVIEW */}
          {activeTab === 'feedback' && (
            <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-xl p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-3">
                <div>
                  <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] flex items-center gap-2">
                    Safety Officer Expert Review & Feedback Loop
                  </h4>
                  <p className="text-[11px] font-sans text-[#526575]">
                    Log expert HSE assessment without overwriting original AI evaluations
                  </p>
                </div>
                <span className="text-[10px] font-mono text-[#1769AA]">AUDITABLE FEEDBACK</span>
              </div>

              {feedbackSuccess && (
                <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-300 text-xs font-mono text-emerald-800">
                  Expert safety feedback logged successfully!
                </div>
              )}

              <form onSubmit={handleSubmitFeedback} className="space-y-3 text-xs font-mono">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Reviewer Name / Title</label>
                    <input
                      type="text"
                      value={reviewerName}
                      onChange={(e) => setReviewerName(e.target.value)}
                      className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                      required
                    />
                  </div>

                  <div>
                    <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Agreement with AI</label>
                    <select
                      value={agreesWithAI ? 'yes' : 'no'}
                      onChange={(e) => setAgreesWithAI(e.target.value === 'yes')}
                      className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                    >
                      <option value="yes">Agree with AI Assessment</option>
                      <option value="no">Disagree / Propose Override</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Human Risk Assessment</label>
                    <select
                      value={humanRisk}
                      onChange={(e) => setHumanRisk(e.target.value)}
                      className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                    >
                      <option value="Low">Low Risk</option>
                      <option value="Medium">Medium Risk</option>
                      <option value="High">High Risk</option>
                      <option value="Critical">Critical Risk</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Expert Justification / Field Observations</label>
                  <textarea
                    value={feedbackReason}
                    onChange={(e) => setFeedbackReason(e.target.value)}
                    placeholder="Provide specific engineering or operational justification for this assessment..."
                    rows={2}
                    className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA] font-sans"
                    required
                  />
                </div>

                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={submittingFeedback || !feedbackReason.trim()}
                    className="px-4 py-2 rounded-lg bg-[#1769AA] hover:bg-[#123B5D] disabled:opacity-50 text-white font-mono text-xs font-bold transition-colors shadow-sm"
                  >
                    {submittingFeedback ? 'Submitting...' : 'Submit Expert Review'}
                  </button>
                </div>
              </form>

              {/* Historical Reviews List */}
              {feedbackList.length > 0 && (
                <div className="pt-3 border-t border-[#D9E2EA] space-y-2">
                  <span className="text-[10px] font-mono text-[#718394] uppercase block font-semibold">Previous Human Reviews ({feedbackList.length})</span>
                  {feedbackList.map((fb) => (
                    <div key={fb.id} className="p-3 rounded-lg bg-white border border-[#D9E2EA] text-xs font-mono space-y-1">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-[#1769AA] font-bold">{fb.reviewer_name}</span>
                        <span className="text-[#718394]">{new Date(fb.submitted_at).toLocaleString()}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${fb.agrees_with_ai ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-amber-50 text-amber-800 border border-amber-200'}`}>
                          {fb.agrees_with_ai ? 'AGREES WITH AI' : 'DISAGREES WITH AI'}
                        </span>
                        {fb.human_risk_level && (
                          <span className="text-[#526575]">Assessed Risk: <strong className="text-[#172B3A]">{fb.human_risk_level}</strong></span>
                        )}
                      </div>
                      <p className="text-[#526575] font-sans text-xs pt-1">"{fb.feedback_reason}"</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 7: IMMUTABLE AUDIT TRAIL */}
          {activeTab === 'audit_trail' && (
            <AuditTimelineView reportId={report.id} />
          )}
        </div>
      </Modal>


      {/* Email Preview Modal */}
      <EmailPreviewModal
        report={report}
        notificationType={notificationType}
        isOpen={isEmailModalOpen}
        onClose={() => setIsEmailModalOpen(false)}
      />
    </>
  );
};

export default ReportDetailModal;
