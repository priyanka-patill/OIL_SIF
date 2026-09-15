import React, { useState, useEffect, useCallback } from 'react';
import { ActionItem, ActionStats, ActionHistoryItem, ReportCounts, SafetyReport } from '../../types/safety';
import { api } from '../../services/api';
import { RiskBadge } from '../common/RiskBadge';
import { Modal } from '../common/Modal';
import { EmailPreviewModal } from '../notifications/EmailPreviewModal';

interface ActionsViewProps {
  counts: ReportCounts | null;
  datasetId?: string;
  onOpenReport: (reportId: string) => void;
}

export const ActionsView: React.FC<ActionsViewProps> = ({ counts, datasetId, onOpenReport }) => {
  const [activeStatusTab, setActiveStatusTab] = useState<'ALL' | 'OVERDUE' | 'OPEN' | 'IN_PROGRESS' | 'CLOSED'>('ALL');
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [stats, setStats] = useState<ActionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Edit / Assign Action Modal
  const [editingAction, setEditingAction] = useState<ActionItem | null>(null);
  const [editStatus, setEditStatus] = useState('Open');
  const [editAssignedTo, setEditAssignedTo] = useState('');
  const [editAssignedDept, setEditAssignedDept] = useState('');
  const [editDueDate, setEditDueDate] = useState('');
  const [editComments, setEditComments] = useState('');
  const [editVerifiedBy, setEditVerifiedBy] = useState('');
  const [savingAction, setSavingAction] = useState(false);

  // Action Audit History Modal
  const [historyModalReportId, setHistoryModalReportId] = useState<string | null>(null);
  const [historyItems, setHistoryItems] = useState<ActionHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Escalation Email Modal
  const [escalatingReport, setEscalatingReport] = useState<SafetyReport | null>(null);
  const [isEscalating, setIsEscalating] = useState(false);

  // Fetch actions & stats
  const fetchActionData = useCallback(() => {
    setLoading(true);
    const statusParam =
      activeStatusTab === 'ALL'
        ? undefined
        : activeStatusTab === 'IN_PROGRESS'
        ? 'In Progress'
        : activeStatusTab === 'OPEN'
        ? 'Open'
        : activeStatusTab === 'CLOSED'
        ? 'Closed'
        : 'Overdue';

    Promise.all([
      api.getActions({
        dataset_id: datasetId,
        status: statusParam,
        search: search.trim() || undefined,
        page,
        page_size: 15,
      }),
      api.getActionStats(datasetId),
    ])
      .then(([actionsRes, statsRes]) => {
        setActions(actionsRes.items || []);
        setTotalPages(actionsRes.total_pages || 1);
        setStats(statsRes);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [datasetId, activeStatusTab, search, page]);

  useEffect(() => {
    fetchActionData();
  }, [fetchActionData]);

  const handleOpenEdit = (act: ActionItem) => {
    setEditingAction(act);
    setEditStatus(act.action_status);
    setEditAssignedTo(act.assigned_to || '');
    setEditAssignedDept(act.assigned_department || act.department || '');
    setEditDueDate(act.due_date ? act.due_date.split('T')[0] : '');
    setEditComments(act.action_comments || '');
    setEditVerifiedBy(act.closure_verified_by || '');
  };

  const handleSaveAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingAction) return;

    setSavingAction(true);
    try {
      await api.updateAction(editingAction.report_id, {
        action_status: editStatus,
        assigned_to: editAssignedTo || null,
        assigned_department: editAssignedDept || null,
        due_date: editDueDate ? new Date(editDueDate).toISOString() : null,
        action_comments: editComments || null,
        closure_verified_by: editStatus === 'Closed' ? (editVerifiedBy || 'Safety Officer') : null,
        actor_name: 'Safety Officer',
        actor_role: 'Safety Officer',
      });
      setEditingAction(null);
      fetchActionData();
    } catch (err: any) {
      alert(`Failed to save action: ${err.message}`);
    } finally {
      setSavingAction(false);
    }
  };

  const handleOpenHistory = async (reportId: string) => {
    setHistoryModalReportId(reportId);
    setLoadingHistory(true);
    try {
      const records = await api.getActionHistory(reportId);
      setHistoryItems(records || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleEscalateAction = async (act: ActionItem) => {
    try {
      const rep = await api.getReport(act.report_id);
      setEscalatingReport(rep);
      setIsEscalating(true);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6 text-[#172B3A]">
      {/* 1. Metric Overview Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <button
          onClick={() => { setActiveStatusTab('ALL'); setPage(1); }}
          className={`p-4 rounded-xl border text-left transition-all ${
            activeStatusTab === 'ALL'
              ? 'bg-blue-50 border-[#1769AA] shadow-sm ring-1 ring-[#1769AA]'
              : 'bg-white border-[#D9E2EA] hover:border-[#1769AA]'
          }`}
        >
          <span className="text-[10px] font-mono text-[#718394] font-bold uppercase block mb-1">TOTAL ACTIONS</span>
          <span className="text-2xl font-mono font-bold text-[#172B3A]">{stats?.total_actions || 0}</span>
          <span className="text-[10px] text-[#718394] block mt-1">Full tracker registry</span>
        </button>

        <button
          onClick={() => { setActiveStatusTab('OVERDUE'); setPage(1); }}
          className={`p-4 rounded-xl border text-left transition-all ${
            activeStatusTab === 'OVERDUE'
              ? 'bg-rose-100 border-rose-500 shadow-sm ring-1 ring-rose-500'
              : 'bg-rose-50 border-rose-200 hover:border-rose-400'
          }`}
        >
          <span className="text-[10px] font-mono text-rose-800 font-bold uppercase block mb-1">OVERDUE</span>
          <span className="text-2xl font-mono font-bold text-rose-700">{stats?.overdue_count || 0}</span>
          <span className="text-[10px] text-rose-700 block mt-1">Requires P1 escalation</span>
        </button>

        <button
          onClick={() => { setActiveStatusTab('OPEN'); setPage(1); }}
          className={`p-4 rounded-xl border text-left transition-all ${
            activeStatusTab === 'OPEN'
              ? 'bg-amber-100 border-amber-500 shadow-sm ring-1 ring-amber-500'
              : 'bg-amber-50 border-amber-200 hover:border-amber-400'
          }`}
        >
          <span className="text-[10px] font-mono text-amber-900 font-bold uppercase block mb-1">OPEN ITEMS</span>
          <span className="text-2xl font-mono font-bold text-amber-800">{stats?.open_count || 0}</span>
          <span className="text-[10px] text-amber-800 block mt-1">Pending implementation</span>
        </button>

        <button
          onClick={() => { setActiveStatusTab('IN_PROGRESS'); setPage(1); }}
          className={`p-4 rounded-xl border text-left transition-all ${
            activeStatusTab === 'IN_PROGRESS'
              ? 'bg-blue-100 border-blue-500 shadow-sm ring-1 ring-blue-500'
              : 'bg-blue-50 border-blue-200 hover:border-blue-400'
          }`}
        >
          <span className="text-[10px] font-mono text-[#1769AA] font-bold uppercase block mb-1">IN PROGRESS</span>
          <span className="text-2xl font-mono font-bold text-[#1769AA]">{stats?.in_progress_count || 0}</span>
          <span className="text-[10px] text-[#1769AA] block mt-1">Active barrier mitigation</span>
        </button>

        <button
          onClick={() => { setActiveStatusTab('CLOSED'); setPage(1); }}
          className={`p-4 rounded-xl border text-left transition-all ${
            activeStatusTab === 'CLOSED'
              ? 'bg-emerald-100 border-emerald-500 shadow-sm ring-1 ring-emerald-500'
              : 'bg-emerald-50 border-emerald-200 hover:border-emerald-400'
          }`}
        >
          <span className="text-[10px] font-mono text-emerald-800 font-bold uppercase block mb-1">CLOSED</span>
          <span className="text-2xl font-mono font-bold text-emerald-700">{stats?.closed_count || 0}</span>
          <span className="text-[10px] text-emerald-800 block mt-1">Verified resolved</span>
        </button>
      </div>

      {/* 2. Control Toolbar: Search & Tab Filter */}
      <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search action by Report ID, problem narrative, assignee..."
            className="w-full sm:w-80 bg-white border border-[#D9E2EA] focus:border-[#1769AA] rounded-lg px-3 py-2 text-xs font-sans text-[#172B3A] placeholder-[#718394] focus:outline-none shadow-sm"
          />
          {search && (
            <button
              onClick={() => { setSearch(''); setPage(1); }}
              className="text-xs font-mono text-[#526575] hover:text-[#1769AA]"
            >
              ✕
            </button>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-[#526575] text-[10px] uppercase font-semibold">STATUS FILTER:</span>
          <div className="flex bg-white p-1 rounded-lg border border-[#D9E2EA]">
            {(['ALL', 'OVERDUE', 'OPEN', 'IN_PROGRESS', 'CLOSED'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => { setActiveStatusTab(tab); setPage(1); }}
                className={`px-2.5 py-1 rounded-md transition-all text-[11px] ${
                  activeStatusTab === tab
                    ? 'bg-[#1769AA] text-white font-bold'
                    : 'text-[#526575] hover:text-[#172B3A]'
                }`}
              >
                {tab.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 3. Action Cards Grid / List */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-16 text-center text-xs font-mono text-[#1769AA] animate-pulse">
             Loading Action Items telemetry...
          </div>
        ) : actions.length === 0 ? (
          <div className="p-12 text-center text-xs font-mono text-[#718394] bg-white border border-[#D9E2EA] rounded-xl shadow-sm">
            No action items matching active filter criteria.
          </div>
        ) : (
          actions.map((act) => (
            <div
              key={act.report_id}
              className={`p-4 rounded-xl border transition-all shadow-sm ${
                act.is_overdue
                  ? 'bg-rose-50/60 border-rose-300 hover:border-rose-400'
                  : act.action_status.toLowerCase() === 'closed'
                  ? 'bg-[#F4F7FA] border-[#D9E2EA] hover:border-[#1769AA]'
                  : 'bg-white border-[#D9E2EA] hover:border-[#1769AA]'
              }`}
            >
              <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                {/* Left: Report & Problem Meta */}
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      onClick={() => onOpenReport(act.report_id)}
                      className="font-mono font-bold text-[#1769AA] hover:underline text-xs"
                    >
                      {act.original_id || act.report_id}
                    </button>
                    <span className="text-[#718394] text-xs font-mono">•</span>
                    <span className="text-xs font-mono text-[#172B3A] font-semibold">{act.refinery_unit || 'Process Unit'}</span>
                    <span className="text-[#718394] text-xs font-mono">•</span>
                    <span className="text-xs font-mono text-[#526575]">{act.department || 'Operations'}</span>
                    <RiskBadge level={act.risk_level} size="sm" />

                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                        act.is_overdue
                          ? 'bg-rose-100 text-rose-800 border-rose-300 animate-pulse'
                          : act.action_status.toLowerCase() === 'closed'
                          ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                          : act.action_status.toLowerCase() === 'in progress'
                          ? 'bg-blue-100 text-blue-800 border-blue-300'
                          : 'bg-amber-100 text-amber-800 border-amber-300'
                      }`}
                    >
                      {act.action_status.toUpperCase()}
                      {act.is_overdue && act.days_overdue ? ` (${act.days_overdue}d OVERDUE)` : ''}
                    </span>
                  </div>

                  {/* Corrective Action Statement */}
                  <div className="text-xs font-sans text-[#172B3A]">
                    <span className="text-[#526575] font-mono text-[10px] uppercase block font-semibold">CORRECTIVE ACTION:</span>
                    <p className="font-medium text-[#172B3A]">"{act.corrective_action || 'Review and verify control barriers'}"</p>
                  </div>

                  {/* Observed Problem Snippet */}
                  <div className="text-[11px] font-sans text-[#526575] truncate max-w-4xl">
                    Observation: "{act.problem}"
                  </div>

                  {/* Comments & Closure details if present */}
                  {act.action_comments && (
                    <div className="text-[11px] font-mono text-[#1769AA] bg-blue-50 p-2 rounded-lg border border-blue-200">
                       Note: "{act.action_comments}"
                    </div>
                  )}
                </div>

                {/* Middle: Assignment & Timeline Telemetry */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs font-mono bg-[#F4F7FA] p-3 rounded-xl border border-[#D9E2EA] shrink-0 min-w-[280px]">
                  <div>
                    <span className="text-[#718394] text-[10px] uppercase block font-semibold">ASSIGNED TO</span>
                    <span className="font-semibold text-[#172B3A] truncate block">
                      {act.assigned_to || <span className="text-[#718394] italic">Unassigned</span>}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#718394] text-[10px] uppercase block font-semibold">TARGET DUE DATE</span>
                    <span className={`font-semibold block ${act.is_overdue ? 'text-rose-600' : 'text-[#172B3A]'}`}>
                      {act.due_date ? new Date(act.due_date).toLocaleDateString() : <span className="text-[#718394] italic">No date</span>}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#718394] text-[10px] uppercase block font-semibold">AUDIT LOGS</span>
                    <button
                      type="button"
                      onClick={() => handleOpenHistory(act.report_id)}
                      className="text-[#1769AA] hover:underline font-bold"
                    >
                      {act.history_count} Change{act.history_count !== 1 ? 's' : ''} 
                    </button>
                  </div>
                </div>

                {/* Right: Actions */}
                <div className="flex flex-row lg:flex-col items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={() => handleOpenEdit(act)}
                    className="px-3.5 py-1.5 rounded-lg bg-[#1769AA] hover:bg-[#123B5D] text-white font-mono text-xs font-bold transition-all shadow-sm"
                  >
                    Edit / Assign 
                  </button>

                  <button
                    type="button"
                    onClick={() => handleEscalateAction(act)}
                    className="px-3.5 py-1.5 rounded-lg bg-[#EEF3F7] hover:bg-rose-50 text-[#526575] hover:text-rose-700 border border-[#D9E2EA] hover:border-rose-300 font-mono text-xs font-semibold transition-all"
                  >
                     Escalate
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2 border-t border-[#D9E2EA] text-xs font-mono">
          <span className="text-[#718394]">Page {page} of {totalPages}</span>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-3 py-1 rounded bg-white border border-[#D9E2EA] text-[#526575] disabled:opacity-30"
            >
              Previous
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="px-3 py-1 rounded bg-white border border-[#D9E2EA] text-[#526575] disabled:opacity-30"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* MODAL 1: Edit / Assign Action */}
      {editingAction && (
        <Modal
          isOpen={true}
          onClose={() => setEditingAction(null)}
          title={`Action Management: Report ${editingAction.original_id || editingAction.report_id}`}
          subtitle="Update status, assign responsibility, configure target due date, and log justification"
          size="lg"
        >
          <form onSubmit={handleSaveAction} className="space-y-4 text-xs font-mono text-[#172B3A]">
            <div className="bg-[#F4F7FA] p-3 rounded-lg border border-[#D9E2EA]">
              <span className="text-[#718394] text-[10px] uppercase block mb-1 font-semibold">CORRECTIVE ACTION REQUIREMENT:</span>
              <p className="text-[#172B3A] font-sans font-medium">"{editingAction.corrective_action || 'Review control barriers'}"</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Status Transition</label>
                <select
                  value={editStatus}
                  onChange={(e) => setEditStatus(e.target.value)}
                  className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                >
                  <option value="Open">Open</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Closed">Closed</option>
                  <option value="Overdue">Overdue</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Target Due Date</label>
                <input
                  type="date"
                  value={editDueDate}
                  onChange={(e) => setEditDueDate(e.target.value)}
                  className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                />
              </div>

              <div>
                <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Responsible Person</label>
                <input
                  type="text"
                  value={editAssignedTo}
                  onChange={(e) => setEditAssignedTo(e.target.value)}
                  placeholder="e.g. John Doe"
                  className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                />
              </div>

              <div>
                <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Responsible Department</label>
                <input
                  type="text"
                  value={editAssignedDept}
                  onChange={(e) => setEditAssignedDept(e.target.value)}
                  placeholder="e.g. Maintenance / Operations"
                  className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                />
              </div>
            </div>

            {editStatus === 'Closed' && (
              <div>
                <label className="text-[10px] text-emerald-800 uppercase block mb-1 font-semibold">Closure Verification Authority</label>
                <input
                  type="text"
                  value={editVerifiedBy}
                  onChange={(e) => setEditVerifiedBy(e.target.value)}
                  placeholder="e.g. Lead HSE Officer"
                  className="w-full bg-white border border-emerald-300 rounded-lg p-2 text-[#172B3A] focus:outline-none"
                />
              </div>
            )}

            <div>
              <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Comments / Audit Notes</label>
              <textarea
                value={editComments}
                onChange={(e) => setEditComments(e.target.value)}
                placeholder="Document barrier installation details, technician notes, or closure evidence..."
                rows={3}
                className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] font-sans focus:outline-none focus:border-[#1769AA]"
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-[#D9E2EA]">
              <button
                type="button"
                onClick={() => setEditingAction(null)}
                className="px-4 py-2 rounded-xl bg-[#EEF3F7] hover:bg-[#D9E2EA] text-[#526575] font-mono text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={savingAction}
                className="px-5 py-2 rounded-xl bg-[#1769AA] hover:bg-[#123B5D] text-white font-mono text-xs font-bold disabled:opacity-50 shadow-sm"
              >
                {savingAction ? 'Saving...' : 'Save & Log History '}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* MODAL 2: Action Audit History Viewer */}
      {historyModalReportId && (
        <Modal
          isOpen={true}
          onClose={() => setHistoryModalReportId(null)}
          title="Action Modification Audit Trail"
          subtitle={`Immutable history of assignment and status changes for Report ${historyModalReportId}`}
          size="lg"
        >
          <div className="space-y-4 text-xs font-mono text-[#172B3A] max-h-[440px] overflow-y-auto custom-scrollbar pr-1">
            {loadingHistory ? (
              <div className="p-8 text-center text-[#1769AA] animate-pulse">Loading audit history...</div>
            ) : historyItems.length === 0 ? (
              <div className="p-8 text-center text-[#718394]">No previous status modifications on record.</div>
            ) : (
              historyItems.map((h) => (
                <div key={h.id} className="p-3.5 rounded-xl bg-[#F4F7FA] border border-[#D9E2EA] space-y-2 shadow-sm">
                  <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2 text-[11px]">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[#1769AA]">{h.actor_name}</span>
                      <span className="px-1.5 py-0.2 rounded bg-white text-[#526575] text-[10px] border border-[#D9E2EA]">{h.actor_role}</span>
                    </div>
                    <span className="text-[#718394]">{new Date(h.timestamp).toLocaleString()}</span>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-[#718394] text-[10px] uppercase font-semibold">ACTION TYPE:</span>
                    <span className="px-2 py-0.5 rounded bg-blue-50 text-[#1769AA] border border-blue-200 font-bold text-[10px]">
                      {h.action_type}
                    </span>
                    {h.old_status && h.new_status && (
                      <span className="text-[#526575] text-[11px]">
                        Status: <strong className="text-[#718394]">{h.old_status}</strong>  <strong className="text-[#1769AA]">{h.new_status}</strong>
                      </span>
                    )}
                  </div>

                  {h.comments && (
                    <p className="text-[#172B3A] font-sans text-xs bg-white p-2 rounded-lg border border-[#D9E2EA]">
                      "{h.comments}"
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        </Modal>
      )}

      {/* MODAL 3: Escalation Email Preview */}
      <EmailPreviewModal
        report={escalatingReport}
        notificationType="MANAGEMENT_ESCALATION"
        isOpen={isEscalating}
        onClose={() => {
          setIsEscalating(false);
          setEscalatingReport(null);
        }}
        onSent={fetchActionData}
      />
    </div>
  );
};
