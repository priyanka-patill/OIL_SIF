import React, { useState, useEffect } from 'react';
import { Modal } from '../common/Modal';
import { api } from '../../services/api';
import { EmailPreviewData, SafetyReport } from '../../types/safety';

interface EmailPreviewModalProps {
  report: SafetyReport | null;
  notificationType?: 'HIGH_RISK' | 'ACTION_ASSIGNMENT' | 'OVERDUE_ACTION' | 'MANAGEMENT_ESCALATION';
  isOpen: boolean;
  onClose: () => void;
  onSent?: () => void;
}

export const EmailPreviewModal: React.FC<EmailPreviewModalProps> = ({
  report,
  notificationType = 'HIGH_RISK',
  isOpen,
  onClose,
  onSent,
}) => {
  const [preview, setPreview] = useState<EmailPreviewData | null>(null);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [activeTab, setActiveTab] = useState<'formatted' | 'html' | 'text'>('formatted');
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!report || !isOpen) return;

    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    api.previewEmail({
      report_id: report.id,
      notification_type: notificationType,
    })
      .then((data) => setPreview(data))
      .catch((err) => setErrorMsg(err.message))
      .finally(() => setLoading(false));
  }, [report, notificationType, isOpen]);

  const handleSend = async () => {
    if (!preview || !report) return;

    setSending(true);
    setErrorMsg(null);

    try {
      const recipientEmails = preview.recipients.map((r) => r.email_address);
      const res = await api.sendNotificationEmail({
        report_id: report.id,
        notification_type: preview.notification_type,
        recipient_emails: recipientEmails.length > 0 ? recipientEmails : ['safety.lead@refinery.oil.internal'],
        subject: preview.subject,
        body_html: preview.rendered_html,
        triggered_by: 'Safety Officer',
        escalation_tier: preview.recipients[0]?.tier || 'SAFETY_HSE',
      });

      setSuccessMsg(`${res.message}`);
      setTimeout(() => {
        onSent?.();
        onClose();
      }, 1500);
    } catch (err: any) {
      setErrorMsg(`Failed to send email: ${err.message}`);
    } finally {
      setSending(false);
    }
  };

  if (!isOpen || !report) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Management Escalation • Mandatory Email Preview"
      subtitle={`Review governance notification for Report ${report.original_id || report.id} before dispatch`}
      size="2xl"
    >
      <div className="space-y-5 text-[#172B3A]">
        {/* Status alerts */}
        {successMsg && (
          <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs font-mono text-emerald-800 flex items-center gap-2">
            <span>{successMsg}</span>
          </div>
        )}
        {errorMsg && (
          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs font-mono text-rose-800 flex items-center gap-2">
            <span>{errorMsg}</span>
          </div>
        )}

        {loading ? (
          <div className="p-12 text-center text-xs font-mono text-[#1769AA] animate-pulse">
             Generating strict facts & AI separated email preview...
          </div>
        ) : preview ? (
          <>
            {/* Header info */}
            <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-xl p-4 space-y-3 text-xs font-mono">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#D9E2EA] pb-2.5">
                <div className="flex items-center gap-2">
                  <span className="text-[#718394] uppercase text-[10px] font-bold">NOTIFICATION TYPE:</span>
                  <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200 font-bold">
                    {preview.notification_type}
                  </span>
                </div>
                <span className="text-[#526575] text-[11px]">
                  Requires human verification before broadcast
                </span>
              </div>

              <div>
                <span className="text-[#718394] uppercase text-[10px] block mb-1 font-bold">EMAIL SUBJECT:</span>
                <div className="font-bold text-[#172B3A] bg-white p-2 rounded-lg border border-[#D9E2EA]">
                  {preview.subject}
                </div>
              </div>

              <div>
                <span className="text-[#718394] uppercase text-[10px] block mb-1 font-bold">CONFIGURED RECIPIENTS:</span>
                <div className="flex flex-wrap gap-2">
                  {preview.recipients.map((rec, i) => (
                    <div
                      key={i}
                      className="px-2.5 py-1 rounded-lg bg-white border border-[#D9E2EA] flex items-center gap-2 text-[11px] shadow-sm"
                    >
                      <span className="px-1.5 py-0.5 rounded bg-blue-50 text-blue-800 text-[9px] font-bold border border-blue-200">
                        {rec.tier}
                      </span>
                      <span className="text-[#172B3A] font-medium">{rec.role_name}</span>
                      <span className="text-[#1769AA] font-mono">({rec.email_address})</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* View tabs */}
            <div className="flex items-center gap-2 border-b border-[#D9E2EA] pb-2 text-xs font-mono">
              <button
                onClick={() => setActiveTab('formatted')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'formatted'
                    ? 'bg-[#1769AA] text-white font-bold shadow-sm'
                    : 'text-[#526575] hover:text-[#172B3A] hover:bg-[#EEF3F7]'
                }`}
              >
                Structured Preview (Separated)
              </button>
              <button
                onClick={() => setActiveTab('html')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'html'
                    ? 'bg-[#1769AA] text-white font-bold shadow-sm'
                    : 'text-[#526575] hover:text-[#172B3A] hover:bg-[#EEF3F7]'
                }`}
              >
                Rendered HTML Output
              </button>
              <button
                onClick={() => setActiveTab('text')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'text'
                    ? 'bg-[#1769AA] text-white font-bold shadow-sm'
                    : 'text-[#526575] hover:text-[#172B3A] hover:bg-[#EEF3F7]'
                }`}
              >
                Plain Text Message
              </button>
            </div>

            {/* Tab content */}
            {activeTab === 'formatted' && (
              <div className="space-y-4 max-h-[380px] overflow-y-auto custom-scrollbar pr-1">
                {/* 1. Recorded Information */}
                <div className="bg-white border border-blue-200 rounded-xl p-4 space-y-3 shadow-sm">
                  <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
                    <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-[#1769AA] flex items-center gap-2">
                      1. Recorded Field Information (Source of Truth)
                    </h4>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200 font-bold">
                      FACTUAL RECORD
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
                    <div className="bg-[#F4F7FA] p-2.5 rounded-lg border border-[#D9E2EA]">
                      <span className="text-[#718394] text-[10px] block font-bold">REPORT ID</span>
                      <span className="font-bold text-[#1769AA]">{preview.recorded_information.original_id}</span>
                    </div>
                    <div className="bg-[#F4F7FA] p-2.5 rounded-lg border border-[#D9E2EA]">
                      <span className="text-[#718394] text-[10px] block font-bold">REFINERY UNIT</span>
                      <span className="font-semibold text-[#172B3A]">{preview.recorded_information.refinery_unit}</span>
                    </div>
                    <div className="bg-[#F4F7FA] p-2.5 rounded-lg border border-[#D9E2EA]">
                      <span className="text-[#718394] text-[10px] block font-bold">DEPARTMENT</span>
                      <span className="text-[#172B3A]">{preview.recorded_information.department}</span>
                    </div>
                    <div className="bg-[#F4F7FA] p-2.5 rounded-lg border border-[#D9E2EA]">
                      <span className="text-[#718394] text-[10px] block font-bold">RECORDED RISK</span>
                      <span className="font-bold text-rose-700">{preview.recorded_information.recorded_risk_level}</span>
                    </div>
                  </div>

                  <div className="bg-[#F4F7FA] p-3 rounded-lg border border-[#D9E2EA] text-xs">
                    <span className="text-[#718394] font-mono text-[10px] block mb-1 font-bold">OBSERVED PROBLEM:</span>
                    <p className="font-sans text-[#172B3A] italic">"{preview.recorded_information.observed_problem}"</p>
                  </div>

                  <div className="bg-[#F4F7FA] p-3 rounded-lg border border-[#D9E2EA] text-xs">
                    <span className="text-[#718394] font-mono text-[10px] block mb-1 font-bold">CORRECTIVE ACTION & GOVERNANCE:</span>
                    <p className="font-sans text-[#172B3A] font-medium">Action: <strong>{preview.recorded_information.corrective_action}</strong></p>
                    <p className="font-mono text-[#526575] text-[11px] mt-1">
                      Status: <strong className="text-[#E5A11A]">{preview.recorded_information.action_status}</strong> • Assigned: <strong>{preview.recorded_information.assigned_to}</strong> • Due: <strong>{preview.recorded_information.due_date}</strong>
                    </p>
                  </div>
                </div>

                {/* 2. AI-Generated Recommendations */}
                <div className="bg-white border border-purple-200 rounded-xl p-4 space-y-3 shadow-sm">
                  <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
                    <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-purple-700 flex items-center gap-2">
                      2. AI SIF Risk Assessment & Preventive Recommendations
                    </h4>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-50 text-purple-800 border border-purple-200 font-bold">
                      AI INFERENCE
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    <div className="bg-purple-50/60 p-2.5 rounded-lg border border-purple-200">
                      <span className="text-purple-800 text-[10px] block font-bold">AI EVALUATED RISK</span>
                      <span className="font-bold text-purple-900">
                        {preview.ai_recommendations.ai_risk_level} ({(preview.ai_recommendations.confidence_score * 100).toFixed(0)}% Confidence)
                      </span>
                    </div>
                    <div className="bg-purple-50/60 p-2.5 rounded-lg border border-purple-200">
                      <span className="text-purple-800 text-[10px] block font-bold">SIF PRECURSOR FLAG</span>
                      <span className="font-bold text-rose-800">
                        {preview.ai_recommendations.sif_precursor} ({preview.ai_recommendations.sif_category})
                      </span>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-rose-50/60 border border-rose-200 text-xs font-sans">
                    <span className="text-rose-900 font-mono text-[10px] font-bold block mb-1"> RECOMMENDED IMMEDIATE ACTION</span>
                    <p className="text-rose-950">{preview.ai_recommendations.immediate_action_recommendation}</p>
                  </div>

                  <div className="p-3 rounded-lg bg-emerald-50/60 border border-emerald-200 text-xs font-sans">
                    <span className="text-emerald-900 font-mono text-[10px] font-bold block mb-1"> RECOMMENDED PREVENTIVE STRATEGY</span>
                    <p className="text-emerald-950">{preview.ai_recommendations.preventive_action_recommendation}</p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'html' && (
              <div className="bg-[#F4F7FA] p-4 rounded-xl border border-[#D9E2EA] max-h-[380px] overflow-y-auto">
                <iframe
                  title="Email Preview"
                  srcDoc={preview.rendered_html}
                  className="w-full h-[340px] bg-white rounded-lg border border-[#D9E2EA]"
                />
              </div>
            )}

            {activeTab === 'text' && (
              <pre className="bg-[#F4F7FA] p-4 rounded-xl border border-[#D9E2EA] text-xs font-mono text-[#172B3A] max-h-[380px] overflow-y-auto whitespace-pre-wrap">
                {preview.rendered_plain_text}
              </pre>
            )}

            {/* Action buttons */}
            <div className="flex items-center justify-between pt-3 border-t border-[#D9E2EA]">
              <span className="text-[11px] font-mono text-[#526575]">
                Action will be logged in the immutable platform EmailLog.
              </span>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 rounded-xl bg-[#EEF3F7] hover:bg-slate-200 text-[#172B3A] font-mono text-xs font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSend}
                  disabled={sending}
                  className="px-5 py-2 rounded-xl bg-[#D64545] hover:bg-red-700 text-white font-mono text-xs font-bold transition-all shadow-sm disabled:opacity-50 flex items-center gap-2"
                >
                  {sending ? 'Sending Notification...' : 'Confirm & Dispatch Email '}
                </button>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </Modal>
  );
};
