import React, { useState } from 'react';
import { api } from '../../services/api';

interface HumanFeedbackModalProps {
  reportId: string;
  analysisId?: string;
  actionId?: string;
  onClose: () => void;
  onFeedbackSubmitted?: () => void;
}

export const HumanFeedbackModal: React.FC<HumanFeedbackModalProps> = ({
  reportId,
  analysisId,
  actionId,
  onClose,
  onFeedbackSubmitted,
}) => {
  const [rating, setRating] = useState<'CORRECT' | 'PARTIALLY_CORRECT' | 'INCORRECT' | 'NOT_USEFUL'>('CORRECT');
  const [category, setCategory] = useState<string>('SIF_PRECURSOR');
  const [reviewerName, setReviewerName] = useState<string>('Safety Officer');
  const [reviewerRole, setReviewerRole] = useState<string>('Lead Safety Engineer');
  const [humanRiskLevel, setHumanRiskLevel] = useState<string>('');
  const [humanSifStatus, setHumanSifStatus] = useState<string>('');
  const [comments, setComments] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.submitHumanFeedback({
        report_id: reportId,
        analysis_id: analysisId,
        action_id: actionId,
        reviewer_name: reviewerName.trim() || 'Safety Officer',
        reviewer_role: reviewerRole.trim() || 'Safety Officer',
        rating,
        feedback_category: category,
        human_risk_level: humanRiskLevel || undefined,
        human_sif_status: humanSifStatus || undefined,
        comments: comments.trim() || undefined,
        is_simulated: false,
      });
      setSuccess(true);
      setTimeout(() => {
        if (onFeedbackSubmitted) onFeedbackSubmitted();
        onClose();
      }, 1200);
    } catch (err: any) {
      alert(`Failed to submit human feedback: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white border border-[#D9E2EA] rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-5">
        <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-3">
          <div className="flex items-center gap-2">
            <span className="text-xl"></span>
            <h3 className="text-sm font-mono font-bold text-[#172B3A] uppercase tracking-wider">
              Expert Human Review & Calibration
            </h3>
          </div>
          <button onClick={onClose} className="text-[#718394] hover:text-[#172B3A] text-lg font-bold">
            &times;
          </button>
        </div>

        {success ? (
          <div className="p-6 text-center space-y-2 font-mono">
            <div className="text-3xl"></div>
            <div className="text-[#2E8B57] font-bold text-sm">Feedback Recorded Successfully!</div>
            <p className="text-[#526575] text-xs font-sans">
              Logged to immutable audit trail and calibration registry.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 text-xs font-mono">
            <div className="bg-[#F4F7FA] p-3 rounded-xl border border-[#D9E2EA] text-[11px] text-[#526575]">
              Report Reference: <strong className="text-[#1769AA]">{reportId}</strong>
              {actionId && <span> • Action: <strong className="text-indigo-700">{actionId}</strong></span>}
            </div>

            {/* Rating Selection */}
            <div>
              <label className="text-[11px] text-[#718394] uppercase font-bold block mb-2">
                1. AI Assessment Accuracy Rating
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {[
                  { key: 'CORRECT', label: 'Correct', color: 'hover:bg-emerald-50 hover:text-emerald-800 border-emerald-200' },
                  { key: 'PARTIALLY_CORRECT', label: 'Partial', color: 'hover:bg-amber-50 hover:text-amber-800 border-amber-200' },
                  { key: 'INCORRECT', label: 'Incorrect', color: 'hover:bg-rose-50 hover:text-rose-800 border-rose-200' },
                  { key: 'NOT_USEFUL', label: 'Not Useful', color: 'hover:bg-[#EEF3F7] hover:text-[#172B3A] border-[#D9E2EA]' },
                ].map((item) => (
                  <button
                    key={item.key}
                    type="button"
                    onClick={() => setRating(item.key as any)}
                    className={`py-2 px-3 rounded-lg border font-bold text-center transition-all ${
                      rating === item.key
                        ? 'bg-[#1769AA] text-white border-[#1769AA] shadow-sm scale-102'
                        : `bg-[#F4F7FA] text-[#172B3A] ${item.color}`
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Category */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-[#718394] uppercase block mb-1 font-bold">Feedback Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-[#F4F7FA] border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                >
                  <option value="SIF_PRECURSOR">SIF Precursor Escalation</option>
                  <option value="BDI_SCORING">BDI Degradation Score</option>
                  <option value="BARRIER_CLASSIFICATION">Swiss Cheese Barrier Layers</option>
                  <option value="ACTION_RECOMMENDATION">Action Recommendation</option>
                  <option value="CORRELATION">Multi-Factor Correlation</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] text-[#718394] uppercase block mb-1 font-bold">Human SIF Assessment</label>
                <select
                  value={humanSifStatus}
                  onChange={(e) => setHumanSifStatus(e.target.value)}
                  className="w-full bg-[#F4F7FA] border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                >
                  <option value="">-- No Correction --</option>
                  <option value="YES">SIF Precursor: YES</option>
                  <option value="NO">SIF Precursor: NO</option>
                  <option value="UNCERTAIN">SIF Precursor: UNCERTAIN</option>
                </select>
              </div>
            </div>

            {/* Reviewer Details */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-[#718394] uppercase block mb-1 font-bold">Reviewer Name</label>
                <input
                  type="text"
                  value={reviewerName}
                  onChange={(e) => setReviewerName(e.target.value)}
                  className="w-full bg-[#F4F7FA] border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                  required
                />
              </div>

              <div>
                <label className="text-[11px] text-[#718394] uppercase block mb-1 font-bold">Reviewer Role</label>
                <input
                  type="text"
                  value={reviewerRole}
                  onChange={(e) => setReviewerRole(e.target.value)}
                  className="w-full bg-[#F4F7FA] border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                  required
                />
              </div>
            </div>

            {/* Comments */}
            <div>
              <label className="text-[11px] text-[#718394] uppercase block mb-1 font-bold">
                Expert Notes & Operational Comments (Optional)
              </label>
              <textarea
                rows={3}
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                placeholder="Provide notes on why the AI evaluation was correct or why specific barriers should be re-weighted..."
                className="w-full bg-[#F4F7FA] border border-[#D9E2EA] rounded-lg p-2.5 text-[#172B3A] placeholder-[#718394] font-sans text-xs focus:outline-none focus:border-[#1769AA]"
              />
            </div>

            {/* Buttons */}
            <div className="flex justify-end gap-3 pt-2 border-t border-[#D9E2EA]">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-[#EEF3F7] hover:bg-slate-200 text-[#172B3A] rounded-lg transition-colors font-bold"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-5 py-2 bg-[#1769AA] hover:bg-[#123B5D] text-white rounded-lg font-bold transition-all shadow-sm disabled:opacity-50"
              >
                {submitting ? 'Submitting...' : 'Submit Expert Review'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
