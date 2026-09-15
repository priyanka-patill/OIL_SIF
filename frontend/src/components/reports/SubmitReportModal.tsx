import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { SafetyReport, SafetyReportCreate, UserRole } from '../../types/safety';
import { api } from '../../services/api';

interface SubmitReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onReportSubmitted: (report: SafetyReport) => void;
  activeRole?: UserRole;
  selectedDatasetId?: string;
}

export const SubmitReportModal: React.FC<SubmitReportModalProps> = ({
  isOpen,
  onClose,
  onReportSubmitted,
  activeRole = 'Supervisor',
  selectedDatasetId,
}) => {
  // Primary Mandatory Input
  const [description, setDescription] = useState('');

  // Structured HSE Fields
  const [reportType, setReportType] = useState('Unsafe Act');
  const [reportDate, setReportDate] = useState(() => new Date().toISOString().slice(0, 16));
  const [siteLocation, setSiteLocation] = useState('Main Complex');
  const [refineryUnit, setRefineryUnit] = useState('');
  const [locationArea, setLocationArea] = useState('');
  const [department, setDepartment] = useState('');
  const [workType, setWorkType] = useState('');
  const [equipmentId, setEquipmentId] = useState('');

  // Optional Context & Pre-cursor Factors
  const [ppeIssue, setPpeIssue] = useState(false);
  const [supervisorFactor, setSupervisorFactor] = useState(false);
  const [maintenanceFactor, setMaintenanceFactor] = useState(false);
  const [repeatedIssue, setRepeatedIssue] = useState(false);
  const [immediateCause, setImmediateCause] = useState('');
  const [potentialConsequence, setPotentialConsequence] = useState('');
  const [correctiveAction, setCorrectiveAction] = useState('');
  const [assignedTo, setAssignedTo] = useState('');
  const [dueDate, setDueDate] = useState('');

  // Submission & Validation States
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionStatus, setSubmissionStatus] = useState<'IDLE' | 'RECEIVED' | 'ANALYZING' | 'SUCCESS'>('IDLE');
  const [createdReport, setCreatedReport] = useState<SafetyReport | null>(null);

  const resetForm = () => {
    setDescription('');
    setReportType('Unsafe Act');
    setReportDate(new Date().toISOString().slice(0, 16));
    setSiteLocation('Main Complex');
    setRefineryUnit('');
    setLocationArea('');
    setDepartment('');
    setWorkType('');
    setEquipmentId('');
    setPpeIssue(false);
    setSupervisorFactor(false);
    setMaintenanceFactor(false);
    setRepeatedIssue(false);
    setImmediateCause('');
    setPotentialConsequence('');
    setCorrectiveAction('');
    setAssignedTo('');
    setDueDate('');
    setErrorMsg(null);
    setIsSubmitting(false);
    setSubmissionStatus('IDLE');
    setCreatedReport(null);
  };

  const validate = (): boolean => {
    setErrorMsg(null);
    const trimmed = description.trim();
    if (!trimmed) {
      setErrorMsg('Please describe what you observed, including the activity, hazard, exposure, or missing control.');
      return false;
    }

    if (trimmed.length < 8) {
      setErrorMsg('Please describe what you observed in detail.');
      return false;
    }

    const vagueTerms = ['unsafe', 'problem', 'issue', 'bad', 'danger', 'incident', 'hazard'];
    if (vagueTerms.includes(trimmed.toLowerCase()) || (trimmed.split(/\s+/).length === 1 && vagueTerms.includes(trimmed.toLowerCase()))) {
      setErrorMsg('Please describe what you observed, including the activity, hazard, exposure, or missing control.');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate() || isSubmitting) return;

    setIsSubmitting(true);
    setSubmissionStatus('RECEIVED');

    const reportData: SafetyReportCreate = {
      description: description.trim(),
      report_type: reportType,
      report_date: reportDate ? new Date(reportDate).toISOString() : undefined,
      location: locationArea ? `${siteLocation} - ${locationArea}` : siteLocation,
      refinery_unit: refineryUnit.trim() || undefined,
      equipment: equipmentId.trim() || undefined,
      work_type: workType.trim() || undefined,
      department: department.trim() || undefined,
      ppe_issue: ppeIssue,
      supervisor_factor: supervisorFactor,
      maintenance_factor: maintenanceFactor,
      repeated_issue: repeatedIssue,
      immediate_cause: immediateCause.trim() || undefined,
      potential_consequence: potentialConsequence.trim() || undefined,
      corrective_action: correctiveAction.trim() || undefined,
      assigned_to: assignedTo.trim() || undefined,
      due_date: dueDate ? new Date(dueDate).toISOString() : undefined,
      dataset_id: selectedDatasetId || undefined,
      submitting_user: `Supervisor (${activeRole})`,
      submitting_role: activeRole,
    };

    try {
      setSubmissionStatus('ANALYZING');
      const newReport = await api.createReport(reportData);
      setCreatedReport(newReport);
      setSubmissionStatus('SUCCESS');
      onReportSubmitted(newReport);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || 'Failed to submit safety report. Please try again.');
      setSubmissionStatus('IDLE');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="CONTROL ROOM • SUBMIT SAFETY OBSERVATION" size="xl">
      {submissionStatus === 'SUCCESS' && createdReport ? (
        <div className="p-6 space-y-6 text-center text-[#172B3A]">
          <div className="h-16 w-16 bg-emerald-100 border border-emerald-300 rounded-full flex items-center justify-center mx-auto text-emerald-700 text-3xl animate-bounce">
           
          </div>

          <div>
            <span className="px-3 py-1 bg-blue-50 border border-blue-200 text-[#1769AA] font-mono text-xs font-bold rounded-full uppercase tracking-wider">
              REPORT SAVED & REGISTERED
            </span>
            <h2 className="text-2xl font-mono font-bold text-[#172B3A] mt-3">
              Report ID: <span className="text-[#1769AA]">{createdReport.original_id || createdReport.id}</span>
            </h2>
            <p className="text-[#718394] text-xs font-mono mt-1">
              Recorded at {new Date(createdReport.created_at).toLocaleString()} • Submitted by {createdReport.submitting_user}
            </p>
          </div>

          <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-xl p-4 max-w-xl mx-auto text-left space-y-3 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-[#526575] font-semibold">AI ANALYSIS STATUS:</span>
              <span
                className={`px-2.5 py-1 text-xs font-mono font-bold rounded-md uppercase ${
                  createdReport.analysis_status === 'COMPLETED'
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                    : createdReport.analysis_status === 'FAILED'
                    ? 'bg-rose-100 text-rose-800 border border-rose-300'
                    : 'bg-amber-100 text-amber-800 border border-amber-300 animate-pulse'
                }`}
              >
                {createdReport.analysis_status === 'COMPLETED'
                  ? 'ANALYSIS COMPLETE'
                  : createdReport.analysis_status === 'FAILED'
                  ? 'ANALYSIS FAILED (REPORT STORED SAFELY)'
                  : 'ANALYSIS IN PROGRESS...'}
              </span>
            </div>
            <p className="text-xs font-sans text-[#172B3A] line-clamp-3 bg-white p-3 rounded-lg border border-[#D9E2EA] italic">
              "{createdReport.description}"
            </p>
          </div>

          <div className="flex items-center justify-center gap-3 pt-2">
            <button
              type="button"
              onClick={() => {
                resetForm();
              }}
              className="px-4 py-2.5 rounded-xl bg-[#EEF3F7] hover:bg-[#D9E2EA] text-[#526575] text-xs font-mono font-bold transition-all"
            >
              Submit Another Report
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 rounded-xl bg-[#1769AA] hover:bg-[#123B5D] text-white text-xs font-mono font-bold shadow-sm transition-all"
            >
              Done & Return to Control Room
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="p-6 space-y-6 text-[#172B3A]">
          {/* Header Principle Banner */}
          <div className="bg-gradient-to-r from-blue-50 to-[#EEF3F7] border border-blue-200 rounded-xl p-4 flex items-start gap-3 shadow-sm">
            <span className="text-xl"></span>
            <div>
              <div className="text-xs font-mono font-bold text-[#1769AA] uppercase tracking-wider">
                SUPERVISOR DIRECT OBSERVATION ENTRY
              </div>
              <p className="text-xs font-sans text-[#526575] mt-0.5 leading-relaxed">
                Simply describe what you observed in clear natural language. The AI Safety Intelligence engine will automatically identify hazards, potential SIF precursor exposures, barrier failures, and recommended preventive actions.
              </p>
            </div>
          </div>

          {errorMsg && (
            <div className="bg-rose-50 border border-rose-300 text-rose-900 p-3.5 rounded-xl text-xs font-mono flex items-start gap-2 animate-shake">
              <span className="text-base"></span>
              <div>
                <div className="font-bold uppercase">Validation Error</div>
                <div>{errorMsg}</div>
              </div>
            </div>
          )}

          {/* SECTION 1: PRIMARY MANDATORY FIELD */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-mono font-bold text-[#172B3A] uppercase tracking-wide flex items-center gap-2">
                <span>Describe What You Observed</span>
                <span className="px-2 py-0.5 text-[10px] font-mono font-extrabold bg-rose-100 text-rose-800 border border-rose-300 rounded">
                  REQUIRED
                </span>
              </label>
              <span className="text-[11px] font-mono text-[#718394]">Natural language observation</span>
            </div>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              placeholder="e.g. During maintenance work on CDU-1, a worker was working close to energized equipment. Proper isolation was not verified and barricading was missing."
              className="w-full bg-white border border-[#D9E2EA] focus:border-[#1769AA] rounded-xl p-3.5 text-xs text-[#172B3A] placeholder:text-[#718394] focus:outline-none focus:ring-1 focus:ring-[#1769AA] transition-all font-sans leading-relaxed shadow-sm"
              required
            />
          </div>

          {/* SECTION 2: REPORT TYPE & LOCATION METADATA */}
          <div className="space-y-3 border-t border-[#D9E2EA] pt-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-[#1769AA] uppercase tracking-wider">
                1. Observation Metadata & Location
              </span>
              <span className="px-2 py-0.5 text-[10px] font-mono bg-[#EEF3F7] text-[#526575] border border-[#D9E2EA] rounded">
                OPTIONAL
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-[11px] font-mono text-[#526575] mb-1 font-semibold">REPORT TYPE</label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="w-full bg-white border border-[#D9E2EA] focus:border-[#1769AA] rounded-lg p-2 text-xs text-[#172B3A] focus:outline-none shadow-sm"
                >
                  <option value="Unsafe Act">Unsafe Act</option>
                  <option value="Unsafe Condition">Unsafe Condition</option>
                  <option value="Near Miss">Near Miss</option>
                  <option value="Incident">Incident</option>
                  <option value="Safety Observation">Safety Observation</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-[#526575] mb-1 font-semibold">DATE & TIME</label>
                <input
                  type="datetime-local"
                  value={reportDate}
                  onChange={(e) => setReportDate(e.target.value)}
                  className="w-full bg-white border border-[#D9E2EA] focus:border-[#1769AA] rounded-lg p-2 text-xs text-[#172B3A] focus:outline-none shadow-sm"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-[#526575] mb-1 font-semibold">REFINERY / UNIT</label>
                <input
                  type="text"
                  value={refineryUnit}
                  onChange={(e) => setRefineryUnit(e.target.value)}
                  placeholder="e.g. CDU-1, FCCU, SRU"
                  className="w-full bg-white border border-[#D9E2EA] focus:border-[#1769AA] rounded-lg p-2 text-xs text-[#172B3A] placeholder:text-[#718394] focus:outline-none shadow-sm"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-[#526575] mb-1 font-semibold">LOCATION / AREA</label>
                <input
                  type="text"
                  value={locationArea}
                  onChange={(e) => setLocationArea(e.target.value)}
                  placeholder="e.g. Pump Bay 4, Deck B"
                  className="w-full bg-white border border-[#D9E2EA] focus:border-[#1769AA] rounded-lg p-2 text-xs text-[#172B3A] placeholder:text-[#718394] focus:outline-none shadow-sm"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
              <div>
                <label className="block text-[11px] font-mono text-[#526575] mb-1 font-semibold">DEPARTMENT</label>
                <input
                  type="text"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  placeholder="e.g. Maintenance, Operations"
                  className="w-full bg-white border border-[#D9E2EA] focus:border-[#1769AA] rounded-lg p-2 text-xs text-[#172B3A] placeholder:text-[#718394] focus:outline-none shadow-sm"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-[#526575] mb-1 font-semibold">WORK TYPE / ACTIVITY</label>
                <input
                  type="text"
                  value={workType}
                  onChange={(e) => setWorkType(e.target.value)}
                  placeholder="e.g. Hot Work, Electrical Repair"
                  className="w-full bg-white border border-[#D9E2EA] focus:border-[#1769AA] rounded-lg p-2 text-xs text-[#172B3A] placeholder:text-[#718394] focus:outline-none shadow-sm"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-[#526575] mb-1 font-semibold">EQUIPMENT / ASSET ID</label>
                <input
                  type="text"
                  value={equipmentId}
                  onChange={(e) => setEquipmentId(e.target.value)}
                  placeholder="e.g. P-102B, V-301"
                  className="w-full bg-white border border-[#D9E2EA] focus:border-[#1769AA] rounded-lg p-2 text-xs text-[#172B3A] placeholder:text-[#718394] focus:outline-none shadow-sm"
                />
              </div>
            </div>
          </div>

          {/* SECTION 3: PRE-CURSOR FACTORS & OPTIONAL CONTEXT */}
          <div className="space-y-3 border-t border-[#D9E2EA] pt-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-[#1769AA] uppercase tracking-wider">
                2. Immediate Factors & Field Observations
              </span>
              <span className="px-2 py-0.5 text-[10px] font-mono bg-[#EEF3F7] text-[#526575] border border-[#D9E2EA] rounded">
                OPTIONAL
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-[#F4F7FA] p-3 rounded-xl border border-[#D9E2EA] font-mono shadow-sm">
              <label className="flex items-center gap-2 cursor-pointer select-none text-xs text-[#172B3A]">
                <input
                  type="checkbox"
                  checked={ppeIssue}
                  onChange={(e) => setPpeIssue(e.target.checked)}
                  className="rounded border-[#D9E2EA] bg-white text-[#1769AA] focus:ring-[#1769AA]"
                />
                <span>PPE Defect / Missing</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer select-none text-xs text-[#172B3A]">
                <input
                  type="checkbox"
                  checked={supervisorFactor}
                  onChange={(e) => setSupervisorFactor(e.target.checked)}
                  className="rounded border-[#D9E2EA] bg-white text-[#1769AA] focus:ring-[#1769AA]"
                />
                <span>Supervisor Factor</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer select-none text-xs text-[#172B3A]">
                <input
                  type="checkbox"
                  checked={maintenanceFactor}
                  onChange={(e) => setMaintenanceFactor(e.target.checked)}
                  className="rounded border-[#D9E2EA] bg-white text-[#1769AA] focus:ring-[#1769AA]"
                />
                <span>Maintenance Factor</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer select-none text-xs text-[#172B3A]">
                <input
                  type="checkbox"
                  checked={repeatedIssue}
                  onChange={(e) => setRepeatedIssue(e.target.checked)}
                  className="rounded border-[#D9E2EA] bg-white text-[#1769AA] focus:ring-[#1769AA]"
                />
                <span>Repeated Occurrence</span>
              </label>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] font-mono text-[#526575] mb-1 font-semibold">IMMEDIATE CAUSE</label>
                <input
                  type="text"
                  value={immediateCause}
                  onChange={(e) => setImmediateCause(e.target.value)}
                  placeholder="e.g. Isolation valve worn out, LOTO bypass"
                  className="w-full bg-white border border-[#D9E2EA] focus:border-[#1769AA] rounded-lg p-2 text-xs text-[#172B3A] placeholder:text-[#718394] focus:outline-none shadow-sm"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-[#526575] mb-1 font-semibold">POTENTIAL CONSEQUENCE</label>
                <input
                  type="text"
                  value={potentialConsequence}
                  onChange={(e) => setPotentialConsequence(e.target.value)}
                  placeholder="e.g. Hydrocarbon release, severe electrical shock"
                  className="w-full bg-white border border-[#D9E2EA] focus:border-[#1769AA] rounded-lg p-2 text-xs text-[#172B3A] placeholder:text-[#718394] focus:outline-none shadow-sm"
                />
              </div>
            </div>
          </div>

          {/* SECTION 4: CORRECTIVE ACTION & ASSIGNMENT */}
          <div className="space-y-3 border-t border-[#D9E2EA] pt-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-[#1769AA] uppercase tracking-wider">
                3. Immediate Corrective Action & Owner
              </span>
              <span className="px-2 py-0.5 text-[10px] font-mono bg-[#EEF3F7] text-[#526575] border border-[#D9E2EA] rounded">
                OPTIONAL
              </span>
            </div>

            <div>
              <label className="block text-[11px] font-mono text-[#526575] mb-1 font-semibold">CORRECTIVE ACTION TAKEN / PLANNED</label>
              <textarea
                value={correctiveAction}
                onChange={(e) => setCorrectiveAction(e.target.value)}
                rows={2}
                placeholder="e.g. Work stopped immediately. Barricading installed and LOTO verified before work resumed."
                className="w-full bg-white border border-[#D9E2EA] focus:border-[#1769AA] rounded-lg p-2 text-xs text-[#172B3A] placeholder:text-[#718394] focus:outline-none shadow-sm"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] font-mono text-[#526575] mb-1 font-semibold">ACTION OWNER / ASSIGNED TO</label>
                <input
                  type="text"
                  value={assignedTo}
                  onChange={(e) => setAssignedTo(e.target.value)}
                  placeholder="e.g. J. Doe (Maintenance Engineer)"
                  className="w-full bg-white border border-[#D9E2EA] focus:border-[#1769AA] rounded-lg p-2 text-xs text-[#172B3A] placeholder:text-[#718394] focus:outline-none shadow-sm"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-[#526575] mb-1 font-semibold">DUE DATE</label>
                <input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full bg-white border border-[#D9E2EA] focus:border-[#1769AA] rounded-lg p-2 text-xs text-[#172B3A] focus:outline-none shadow-sm"
                />
              </div>
            </div>
          </div>

          {/* AI AUTOMATION NOTICE */}
          <div className="bg-[#EEF3F7] border border-[#D9E2EA] p-3 rounded-xl flex items-center justify-between text-xs font-mono text-[#526575]">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 bg-blue-50 text-[#1769AA] border border-blue-200 rounded text-[10px] font-bold">
                AI-GENERATED
              </span>
              <span>Hazard, Exposure, SIF Precursor, Risk Level & Life-Saving Rules synthesized automatically</span>
            </div>
          </div>

          {/* FOOTER ACTIONS */}
          <div className="flex items-center justify-between border-t border-[#D9E2EA] pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-[#EEF3F7] hover:bg-[#D9E2EA] text-[#526575] hover:text-[#172B3A] text-xs font-mono transition-all"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2.5 rounded-xl bg-[#1769AA] hover:bg-[#123B5D] disabled:opacity-50 text-white font-mono text-xs font-bold transition-all shadow-sm flex items-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <span className="h-3 w-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Submitting & Triggering AI...</span>
                </>
              ) : (
                <>
                  <span> SUBMIT SAFETY REPORT</span>
                </>
              )}
            </button>
          </div>
        </form>
      )}
    </Modal>
  );
};
