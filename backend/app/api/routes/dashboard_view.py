from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Frontend Dashboard"])

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OIL SIF Intelligence Platform • Control Room</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            slate: {
              950: '#060B13',
              900: '#0B111E',
              850: '#0F172A',
              800: '#131E31',
              700: '#1E293B',
              600: '#334155'
            }
          }
        }
      }
    }
  </script>
  <!-- React 18 and Babel for standalone runtime execution -->
  <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <style>
    body {
      background-color: #0B111E;
      color: #F1F5F9;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.6); }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(51, 65, 85, 0.8); border-radius: 4px; }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(100, 116, 139, 1); }
  </style>
</head>
<body class="bg-[#0B111E] text-slate-100 min-h-screen selection:bg-cyan-500 selection:text-black">
  <div id="root"></div>

  <script type="text/babel">
    const { useState, useEffect, useCallback, useMemo, useRef } = React;

    // --- API CLIENT ---
    const api = {
      async get(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      },
      async post(url, data) {
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      },
      async patch(url, data) {
        const res = await fetch(url, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      },
      async put(url, data) {
        const res = await fetch(url, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      },
      async delete(url) {
        const res = await fetch(url, { method: 'DELETE' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return true;
      }
    };

    // --- BADGES & COMMON ---
    function RiskBadge({ level, size = 'md' }) {
      const norm = (level || 'UNKNOWN').toUpperCase();
      let color = 'bg-slate-800 text-slate-400 border-slate-700';
      let dot = 'bg-slate-400';
      if (norm === 'CRITICAL' || norm === 'HIGH') {
        color = 'bg-red-500/15 text-red-400 border-red-500/40 shadow-sm shadow-red-950/40';
        dot = 'bg-red-400 animate-pulse';
      } else if (norm === 'MEDIUM') {
        color = 'bg-amber-500/15 text-amber-400 border-amber-500/40';
        dot = 'bg-amber-400';
      } else if (norm === 'LOW') {
        color = 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40';
        dot = 'bg-emerald-400';
      }
      const s = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : size === 'lg' ? 'px-3.5 py-1.5 text-xs font-bold' : 'px-2.5 py-1 text-xs font-semibold';
      return (
        <span className={`inline-flex items-center gap-1.5 rounded border uppercase font-mono tracking-wider ${s} ${color}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${dot}`}></span>
          {norm}
        </span>
      );
    }

    function SIFBadge({ status, size = 'md' }) {
      const norm = (status || 'NO').toUpperCase();
      let color = 'bg-slate-800/80 text-slate-400 border-slate-700';
      let label = 'NON-SIF';
      if (norm === 'YES' || norm === 'TRUE') {
        color = 'bg-rose-500/20 text-rose-300 border-rose-500/50 shadow-sm shadow-rose-950/50';
        label = 'SIF PRECURSOR';
      } else if (norm === 'UNCERTAIN') {
        color = 'bg-amber-500/20 text-amber-300 border-amber-500/50';
        label = 'SIF UNCERTAIN';
      }
      const s = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : size === 'lg' ? 'px-3.5 py-1.5 text-xs font-bold' : 'px-2.5 py-1 text-xs font-semibold';
      return (
        <span className={`inline-flex items-center gap-1.5 rounded border uppercase font-mono tracking-wider ${s} ${color}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${norm === 'YES' ? 'bg-rose-400 animate-ping' : norm === 'UNCERTAIN' ? 'bg-amber-400' : 'bg-slate-500'}`}></span>
          {label}
        </span>
      );
    }

    function DangerBadge({ level }) {
      const l = (level || 'LOW').toUpperCase();
      let color = 'bg-emerald-950 text-emerald-300 border-emerald-500/40';
      if (l === 'CRITICAL') color = 'bg-red-950 text-red-300 border-red-500/50 animate-pulse';
      else if (l === 'HIGH') color = 'bg-rose-950 text-rose-300 border-rose-500/40';
      else if (l === 'MODERATE') color = 'bg-amber-950 text-amber-300 border-amber-500/40';

      return (
        <span className={`px-2 py-0.5 rounded border text-[10px] font-mono font-bold uppercase ${color}`}>
          {l} DANGER
        </span>
      );
    }

    // --- MODAL WRAPPER ---
    function Modal({ isOpen, onClose, title, subtitle, size = 'lg', children }) {
      if (!isOpen) return null;
      const sizeClasses = size === '2xl' ? 'max-w-4xl' : size === 'xl' ? 'max-w-3xl' : 'max-w-2xl';
      return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className={`w-full ${sizeClasses} bg-[#101726] border border-slate-800 rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden`}>
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/70">
              <div>
                <h3 className="text-sm font-mono font-bold text-slate-100 uppercase tracking-wide">{title}</h3>
                {subtitle && <p className="text-xs font-sans text-slate-400 mt-0.5">{subtitle}</p>}
              </div>
              <button onClick={onClose} className="text-slate-400 hover:text-slate-100 p-1.5 rounded-lg hover:bg-slate-800 font-mono text-sm">✕</button>
            </div>
            <div className="p-6 overflow-y-auto custom-scrollbar flex-1">{children}</div>
          </div>
        </div>
      );
    }

    // --- MAIN DASHBOARD APP ---
    function App() {
      const [tab, setTab] = useState('dashboard');
      const [activeRole, setActiveRole] = useState('Safety Officer');
      const [health, setHealth] = useState(null);
      const [datasets, setDatasets] = useState([]);
      const [selectedDatasetId, setSelectedDatasetId] = useState('');
      const [counts, setCounts] = useState(null);
      const [sifSummary, setSifSummary] = useState(null);
      const [filterFields, setFilterFields] = useState([]);

      // Factor Intelligence State
      const [factorCombinations, setFactorCombinations] = useState(null);
      const [factorSummary, setFactorSummary] = useState(null);
      const [hipoData, setHipoData] = useState(null);

      // Dataset Comparison State
      const [compA, setCompA] = useState('');
      const [compB, setCompB] = useState('');
      const [comparisonResult, setComparisonResult] = useState(null);
      const [compLoading, setCompLoading] = useState(false);

      // Reports State
      const [reports, setReports] = useState([]);
      const [reportsTotal, setReportsTotal] = useState(0);
      const [page, setPage] = useState(1);
      const [search, setSearch] = useState('');
      const [sortBy, setSortBy] = useState('report_date');
      const [sortOrder, setSortOrder] = useState('desc');
      const [activeFilters, setActiveFilters] = useState({});

      // Detail Modal
      const [selectedReport, setSelectedReport] = useState(null);
      const [reportDetailAnalysis, setReportDetailAnalysis] = useState(null);
      const [isDetailOpen, setIsDetailOpen] = useState(false);
      const [detailTab, setDetailTab] = useState('intelligence');
      const [detailChatMessages, setDetailChatMessages] = useState([]);
      const [detailChatInput, setDetailChatInput] = useState('');
      const [detailChatLoading, setDetailChatLoading] = useState(false);

      // Report Generator Modal
      const [isReportGenOpen, setIsReportGenOpen] = useState(false);
      const [genFormat, setGenFormat] = useState('PDF');
      const [genRisk, setGenRisk] = useState('');
      const [genUnit, setGenUnit] = useState('');
      const [genDept, setGenDept] = useState('');
      const [genPreview, setGenPreview] = useState(null);

      // Action Center State
      const [actionTab, setActionTab] = useState('ALL');
      const [actionItems, setActionItems] = useState([]);
      const [actionStats, setActionStats] = useState(null);
      const [actionSearch, setActionSearch] = useState('');
      const [editingAction, setEditingAction] = useState(null);
      const [editStatus, setEditStatus] = useState('Open');
      const [editAssignedTo, setEditAssignedTo] = useState('');
      const [editAssignedDept, setEditAssignedDept] = useState('');
      const [editDueDate, setEditDueDate] = useState('');
      const [editComments, setEditComments] = useState('');
      const [historyReportId, setHistoryReportId] = useState(null);
      const [historyList, setHistoryList] = useState([]);

      // Email Preview & Escalation Modal
      const [emailPreviewReport, setEmailPreviewReport] = useState(null);
      const [emailPreviewData, setEmailPreviewData] = useState(null);
      const [isEmailModalOpen, setIsEmailModalOpen] = useState(false);
      const [emailSentToast, setEmailSentToast] = useState(null);

      // AI Safety Chat State
      const [chatMessages, setChatMessages] = useState([
        {
          sender: 'ai',
          text: "### OIL Safety Intelligence Assistant\\n\\nDirectly connected to the **OIL Safety Intelligence Database** (1,025 verified refinery safety records across 13 datasets).\\n\\nAll questions are answered using exact database queries with strict **zero-fabrication** guarantees. Select any preset or type your custom inquiry below:",
          suggestedActions: [
            "Which combination of safety factors is most dangerous?",
            "Show high-potential near-miss reports.",
            "Compare single-factor vs multi-factor datasets.",
            "How many reports involve supervisor negligence?",
            "How many reports involve maintenance delay?",
            "How many reports involve repeated issues?",
            "Show reports where only PPE is violated.",
            "Summarize the current safety situation."
          ],
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
      const [chatInput, setChatInput] = useState('');
      const [chatLoading, setChatLoading] = useState(false);
      const chatEndRef = useRef(null);

      // Settings State
      const [notifConfigs, setNotifConfigs] = useState([]);
      const [emailLogs, setEmailLogs] = useState([]);
      const [auditLogs, setAuditLogs] = useState([]);
      const [settingsTab, setSettingsTab] = useState('system');
      const [newTier, setNewTier] = useState('SAFETY_HSE');
      const [newRole, setNewRole] = useState('');
      const [newDept, setNewDept] = useState('All');
      const [newEmail, setNewEmail] = useState('');

      // --- INITIAL LOAD ---
      useEffect(() => {
        api.get('/api/health').then(setHealth).catch(console.error);
        api.get('/api/datasets?page=1&page_size=20').then(res => {
          setDatasets(res.items || []);
          if (res.items && res.items.length > 0 && !selectedDatasetId) {
            setSelectedDatasetId(res.items[0].id);
          }
          if (res.items && res.items.length >= 2) {
            const single = res.items.find(d => d.dataset_type === 'single_factor' && !d.is_summary_dataset);
            const multi = res.items.find(d => d.dataset_type === 'multi_factor' || d.dataset_type === 'high_potential');
            setCompA(single ? single.id : res.items[0].id);
            setCompB(multi ? multi.id : res.items[1].id);
          }
        }).catch(console.error);
        api.get('/api/metadata/fields').then(res => setFilterFields(res.available_filters || [])).catch(console.error);

        // Load factor intelligence
        api.get('/api/factors/combinations').then(setFactorCombinations).catch(console.error);
        api.get('/api/factors/summary').then(setFactorSummary).catch(console.error);
        api.get('/api/factors/high-potential').then(setHipoData).catch(console.error);
      }, []);

      // Refresh Counts & Summaries
      const refreshMetrics = useCallback(() => {
        const q = selectedDatasetId ? `?dataset_id=${encodeURIComponent(selectedDatasetId)}` : '';
        api.get(`/api/reports/count${q}`).then(setCounts).catch(console.error);
        api.get(`/api/sif/summary${q}`).then(setSifSummary).catch(console.error);
        api.get(`/api/actions/stats${q}`).then(setActionStats).catch(console.error);
      }, [selectedDatasetId]);

      useEffect(() => {
        refreshMetrics();
      }, [refreshMetrics]);

      // Trigger Comparison
      useEffect(() => {
        if (compA && compB && compA !== compB) {
          setCompLoading(true);
          api.get(`/api/datasets/compare?dataset_a=${encodeURIComponent(compA)}&dataset_b=${encodeURIComponent(compB)}`)
            .then(setComparisonResult)
            .catch(console.error)
            .finally(() => setCompLoading(false));
        }
      }, [compA, compB]);

      // Fetch Reports
      const fetchReports = useCallback(() => {
        const params = new URLSearchParams({
          page,
          page_size: 15,
          sort_by: sortBy,
          sort_order: sortOrder,
          ...(search ? { search } : {}),
          ...(selectedDatasetId ? { dataset_id: selectedDatasetId } : {}),
          ...activeFilters
        });
        api.get(`/api/reports?${params.toString()}`).then(res => {
          setReports(res.items || []);
          setReportsTotal(res.total || 0);
        }).catch(console.error);
      }, [page, sortBy, sortOrder, search, selectedDatasetId, activeFilters]);

      useEffect(() => {
        fetchReports();
      }, [fetchReports]);

      // Fetch Action Items
      const fetchActions = useCallback(() => {
        const statusMap = {
          'OVERDUE': 'Overdue',
          'OPEN': 'Open',
          'IN_PROGRESS': 'In Progress',
          'CLOSED': 'Closed'
        };
        const params = new URLSearchParams({
          page: 1,
          page_size: 50,
          ...(selectedDatasetId ? { dataset_id: selectedDatasetId } : {}),
          ...(statusMap[actionTab] ? { status: statusMap[actionTab] } : {}),
          ...(actionSearch ? { search: actionSearch } : {})
        });
        api.get(`/api/actions?${params.toString()}`).then(res => {
          setActionItems(res.items || []);
        }).catch(console.error);
      }, [selectedDatasetId, actionTab, actionSearch]);

      useEffect(() => {
        if (tab === 'actions') fetchActions();
      }, [tab, fetchActions]);

      // Fetch Settings data
      useEffect(() => {
        if (tab === 'settings') {
          api.get('/api/notifications/config').then(setNotifConfigs).catch(console.error);
          api.get('/api/notifications/logs?page_size=25').then(res => setEmailLogs(res.items || [])).catch(console.error);
          api.get('/api/audit-logs?page_size=25').then(res => setAuditLogs(res.items || [])).catch(console.error);
        }
      }, [tab]);

      // Report Generator Preview
      useEffect(() => {
        if (isReportGenOpen) {
          const params = new URLSearchParams({
            ...(selectedDatasetId ? { dataset_id: selectedDatasetId } : {}),
            ...(genRisk ? { risk_level: genRisk } : {}),
            ...(genUnit ? { refinery_unit: genUnit } : {}),
            ...(genDept ? { department: genDept } : {})
          });
          api.get(`/api/reports/export/preview?${params.toString()}`).then(setGenPreview).catch(console.error);
        }
      }, [isReportGenOpen, selectedDatasetId, genRisk, genUnit, genDept]);

      // Chat send
      const handleSendChat = async (queryText) => {
        const text = queryText || chatInput;
        if (!text.trim() || chatLoading) return;

        const userMsg = { sender: 'user', text, timestamp: new Date().toLocaleTimeString() };
        setChatMessages(prev => [...prev, userMsg]);
        setChatInput('');
        setChatLoading(true);

        try {
          const res = await api.post('/api/chat', { message: text, dataset_id: selectedDatasetId || undefined });
          setChatMessages(prev => [
            ...prev,
            {
              sender: 'ai',
              text: res.reply,
              suggestedActions: res.suggested_actions,
              relevantReports: res.relevant_reports,
              timestamp: new Date().toLocaleTimeString()
            }
          ]);
        } catch (err) {
          setChatMessages(prev => [...prev, { sender: 'ai', text: ` Error: ${err.message}`, timestamp: new Date().toLocaleTimeString() }]);
        } finally {
          setChatLoading(false);
          chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
      };

      // Open single report detail modal
      const handleOpenReport = async (reportId) => {
        try {
          const rep = await api.get(`/api/reports/${reportId}`);
          setSelectedReport(rep);
          setDetailTab('intelligence');
          setDetailChatMessages([
            {
              sender: 'ai',
              text: `### OIL Safety Context: Report ${rep.original_id || rep.id}\\n\\nAsk me specific questions regarding this observation, hazard vectors, immediate actions, recurrence, or potential escalation consequences.`,
              suggestedActions: [
                'Why is this report important?',
                'What is the potential safety consequence?',
                'What immediate action is recommended?',
                'Is this issue recurring?',
                'What could happen if this remains unresolved?'
              ],
              timestamp: new Date().toLocaleTimeString()
            }
          ]);
          setIsDetailOpen(true);
          const an = await api.get(`/api/reports/${reportId}/analysis`);
          setReportDetailAnalysis(an);
        } catch (e) {
          console.error(e);
        }
      };

      // Report Specific Chat send
      const handleSendReportChat = async (queryText) => {
        const text = queryText || detailChatInput;
        if (!text.trim() || !selectedReport || detailChatLoading) return;

        const userMsg = { sender: 'user', text, timestamp: new Date().toLocaleTimeString() };
        setDetailChatMessages(prev => [...prev, userMsg]);
        setDetailChatInput('');
        setDetailChatLoading(true);

        try {
          const res = await api.post('/api/chat', { message: text, report_id: selectedReport.id });
          setDetailChatMessages(prev => [
            ...prev,
            {
              sender: 'ai',
              text: res.reply,
              suggestedActions: res.suggested_actions,
              timestamp: new Date().toLocaleTimeString()
            }
          ]);
        } catch (err) {
          setDetailChatMessages(prev => [...prev, { sender: 'ai', text: ` Error: ${err.message}`, timestamp: new Date().toLocaleTimeString() }]);
        } finally {
          setDetailChatLoading(false);
        }
      };

      // Open Email Preview Modal
      const handleTriggerEmailPreview = async (reportId, notifType = 'HIGH_RISK') => {
        try {
          const rep = await api.get(`/api/reports/${reportId}`);
          setEmailPreviewReport(rep);
          const preview = await api.post('/api/notifications/preview', { report_id: reportId, notification_type: notifType });
          setEmailPreviewData(preview);
          setIsEmailModalOpen(true);
        } catch (e) {
          alert(`Failed to generate email preview: ${e.message}`);
        }
      };

      // Dispatch Email
      const handleSendEmail = async () => {
        if (!emailPreviewData || !emailPreviewReport) return;
        try {
          const emails = emailPreviewData.recipients.map(r => r.email_address);
          await api.post('/api/notifications/send', {
            report_id: emailPreviewReport.id,
            notification_type: emailPreviewData.notification_type,
            recipient_emails: emails.length > 0 ? emails : ['safety.lead@refinery.oil.internal'],
            subject_override: emailPreviewData.subject
          });
          setEmailSentToast(`Dispatched to ${emails.join(', ') || 'Safety Lead'}`);
          setTimeout(() => {
            setEmailSentToast(null);
            setIsEmailModalOpen(false);
          }, 2000);
        } catch (e) {
          alert(`Failed to send email: ${e.message}`);
        }
      };

      // Update Action
      const handleSaveActionUpdate = async (e) => {
        e.preventDefault();
        if (!editingAction) return;
        try {
          await api.put(`/api/actions/${editingAction.report_id}`, {
            action_status: editStatus,
            assigned_to: editAssignedTo || null,
            assigned_department: editAssignedDept || null,
            due_date: editDueDate || null,
            comments: editComments || null,
            updated_by: `${activeRole} User`
          });
          setEditingAction(null);
          fetchActions();
          refreshMetrics();
        } catch (err) {
          alert(`Failed to update action: ${err.message}`);
        }
      };

      // Action History Logs
      const handleOpenHistory = async (reportId) => {
        try {
          const h = await api.get(`/api/actions/${reportId}/history`);
          setHistoryList(h || []);
          setHistoryReportId(reportId);
        } catch (e) {
          alert(e.message);
        }
      };

      // Add Notification Config
      const handleAddConfig = async (e) => {
        e.preventDefault();
        if (!newRole.trim() || !newEmail.trim()) return;
        try {
          await api.post('/api/notifications/config', {
            tier: newTier,
            role_name: newRole.trim(),
            department: newDept.trim() || 'All',
            email_address: newEmail.trim(),
            notify_on_high_risk: true,
            notify_on_overdue: true,
            notify_on_assignment: true,
            is_active: true
          });
          setNewRole('');
          setNewEmail('');
          const cfgs = await api.get('/api/notifications/config');
          setNotifConfigs(cfgs);
        } catch (err) {
          alert(`Failed: ${err.message}`);
        }
      };

      // Total reports in entire DB
      const dbTotalReports = useMemo(() => {
        return datasets.reduce((sum, d) => sum + (d.is_summary_dataset ? 0 : d.row_count), 0);
      }, [datasets]);

      return (
        <div className="flex min-h-screen">
          {/* SIDEBAR */}
          <aside className="w-64 bg-[#0B111E] border-r border-slate-800 flex flex-col shrink-0 h-screen sticky top-0 select-none">
            <div className="p-4 border-b border-slate-800 flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-white shadow-lg shadow-cyan-950/50">
                OIL
              </div>
              <div>
                <div className="text-xs font-mono font-bold tracking-wider text-slate-100 uppercase">SIF Intelligence</div>
                <div className="text-[10px] font-mono text-cyan-400 tracking-widest uppercase">Platform v2.0 • Enterprise</div>
              </div>
            </div>

            {/* Role indicator */}
            <div className="px-4 pt-3 pb-1">
              <div className="bg-slate-950/80 border border-slate-800 rounded-lg px-2.5 py-1.5 flex items-center justify-between text-xs font-mono">
                <span className="text-slate-500 text-[10px] uppercase">ACTIVE ROLE:</span>
                <span className="text-cyan-300 font-bold text-[11px]">{activeRole}</span>
              </div>
            </div>

            <nav className="flex-1 px-3 py-3 space-y-1 overflow-y-auto custom-scrollbar text-xs font-medium">
              {[
                { id: 'dashboard', label: 'Dashboard', icon: '' },
                { id: 'reports', label: 'Safety Reports', icon: '' },
                { id: 'factors', label: 'Factor Intelligence', icon: '' },
                { id: 'hipo', label: 'HiPo Precursors', icon: '', badge: hipoData?.total_high_potential_records ? `${hipoData.total_high_potential_records}` : undefined, badgeColor: 'bg-rose-500/20 text-rose-300 border-rose-500/40' },
                { id: 'comparison', label: 'Dataset Comparison', icon: '' },
                { id: 'actions', label: 'Action Center', icon: '', badge: actionStats?.overdue_count ? `${actionStats.overdue_count} Overdue` : undefined, badgeColor: 'bg-red-500/20 text-red-300 border-red-500/40' },
                { id: 'chat', label: 'AI Safety Chat', icon: '' },
                { id: 'settings', label: 'Escalations & Settings', icon: '' }
              ].map(item => (
                <button
                  key={item.id}
                  onClick={() => setTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition-all ${
                    tab === item.id
                      ? 'bg-slate-800/90 text-cyan-300 border border-cyan-500/40 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <span>{item.icon}</span>
                    <span className="truncate">{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className={`px-1.5 py-0.5 text-[10px] font-mono font-bold rounded border ${item.badgeColor || 'bg-slate-800 text-slate-300 border-slate-700'}`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              ))}
            </nav>

            <div className="p-4 border-t border-slate-800 bg-slate-950/40 text-[11px] font-mono text-slate-500">
              <div className="flex items-center justify-between">
                <span>DATABASE</span>
                <span className="text-emerald-400 font-semibold">{dbTotalReports || 1025} RECORDS</span>
              </div>
            </div>
          </aside>

          {/* MAIN CONTENT */}
          <div className="flex-1 flex flex-col min-w-0">
            {/* TOP BAR */}
            <header className="h-16 bg-[#0B111E]/90 backdrop-blur border-b border-slate-800 px-6 flex items-center justify-between sticky top-0 z-30">
              <div>
                <h1 className="text-base font-mono font-bold text-slate-100 uppercase tracking-wide flex items-center gap-2">
                  {tab === 'dashboard' ? 'Control Room Dashboard' : 
                   tab === 'reports' ? 'Safety Reports Explorer' : 
                   tab === 'factors' ? 'Safety Factor & Combination Matrix' :
                   tab === 'hipo' ? 'High-Potential Near Miss Precursors' :
                   tab === 'comparison' ? 'Side-by-Side Dataset Comparison' :
                   tab === 'actions' ? 'Action Center & Governance Tracker' : 
                   tab === 'chat' ? 'OIL Safety Intelligence Assistant' : 'Platform Settings & Escalations'}
                </h1>
                <p className="text-xs font-sans text-slate-400">OIL SIF Intelligence Platform • 1,025 Verified Reports Across 13 Datasets</p>
              </div>

              <div className="flex items-center gap-3">
                {/* Generate Report Action */}
                <button
                  onClick={() => setIsReportGenOpen(true)}
                  className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-mono text-xs font-bold transition-all shadow-md shadow-cyan-950/40 flex items-center gap-1.5"
                >
                  Generate Report
                </button>

                {/* Role Switcher */}
                <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs font-mono">
                  <span className="text-slate-500 text-[10px] uppercase">ROLE:</span>
                  <select
                    value={activeRole}
                    onChange={(e) => setActiveRole(e.target.value)}
                    className="bg-transparent text-cyan-300 font-bold focus:outline-none cursor-pointer"
                  >
                    <option value="Safety Officer" className="bg-slate-900 text-slate-200">Safety Officer</option>
                    <option value="Management" className="bg-slate-900 text-slate-200">Management</option>
                    <option value="Administrator" className="bg-slate-900 text-slate-200">Administrator</option>
                  </select>
                </div>

                {/* Dataset Selector */}
                {datasets.length > 0 && (
                  <div className="hidden lg:flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs font-mono text-slate-300">
                    <span className="text-slate-500 text-[10px] uppercase">Scope:</span>
                    <select
                      value={selectedDatasetId}
                      onChange={(e) => setSelectedDatasetId(e.target.value)}
                      className="bg-transparent text-cyan-300 font-semibold focus:outline-none cursor-pointer max-w-[220px] truncate"
                    >
                      {datasets.map(d => (
                        <option key={d.id} value={d.id} className="bg-slate-900 text-slate-200">
                          {d.sheet_name || d.dataset_name} ({d.row_count})
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
            </header>

            <main className="p-6 space-y-6 flex-1 max-w-[1600px] w-full mx-auto">
              {/* TAB: DASHBOARD */}
              {tab === 'dashboard' && (
                <div className="space-y-6">
                  {/* KPI Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-900 to-[#131E31] border border-slate-800">
                      <span className="text-[10px] font-mono text-slate-400 font-bold uppercase block mb-1">DATASET REPORTS</span>
                      <span className="text-3xl font-mono font-bold text-cyan-400">{counts?.total_reports || 0}</span>
                      <span className="text-[11px] text-slate-400 block mt-1">Scope: {datasets.find(d => d.id === selectedDatasetId)?.dataset_name || 'Selected'}</span>
                    </div>

                    <div className="p-5 rounded-2xl bg-gradient-to-br from-red-950/30 to-[#131E31] border border-red-500/30">
                      <span className="text-[10px] font-mono text-red-400 font-bold uppercase block mb-1">HIGH-RISK OBSERVATIONS</span>
                      <span className="text-3xl font-mono font-bold text-red-400">{counts?.by_risk_level?.['High'] || counts?.by_risk_level?.['HIGH'] || 0}</span>
                      <span className="text-[11px] text-slate-400 block mt-1">Critical Process Safety Hazards</span>
                    </div>

                    <div className="p-5 rounded-2xl bg-gradient-to-br from-rose-950/30 to-[#131E31] border border-rose-500/30">
                      <span className="text-[10px] font-mono text-rose-400 font-bold uppercase block mb-1">SIF PRECURSORS</span>
                      <span className="text-3xl font-mono font-bold text-rose-300">{sifSummary?.sif_precursors_detected || 0}</span>
                      <span className="text-[11px] text-slate-400 block mt-1">{sifSummary?.sif_precursor_rate_percentage || 0}% Precursor Rate</span>
                    </div>

                    <div className="p-5 rounded-2xl bg-gradient-to-br from-amber-950/30 to-[#131E31] border border-amber-500/30">
                      <span className="text-[10px] font-mono text-amber-400 font-bold uppercase block mb-1">ACTION ITEMS OVERDUE</span>
                      <span className="text-3xl font-mono font-bold text-amber-400">{actionStats?.overdue_count || 0}</span>
                      <span className="text-[11px] text-slate-400 block mt-1">Requires HSE Escalation</span>
                    </div>
                  </div>

                  {/* Factor Compounding Escalation Preview Banner */}
                  {factorCombinations && (
                    <div className="bg-[#131E31]/80 border border-slate-800 rounded-2xl p-5 space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
                            Safety Factor Compounding Matrix (1-Factor to 4-Factor)
                          </h3>
                          <p className="text-xs font-sans text-slate-400">
                            Empirical non-linear escalation across 950 operational workbook reports.
                          </p>
                        </div>
                        <button onClick={() => setTab('factors')} className="px-3 py-1 rounded bg-slate-900 border border-slate-700 text-cyan-400 text-xs font-mono font-bold hover:border-cyan-500">
                          Full Factor Matrix 
                        </button>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                        {factorCombinations.by_factor_count.map(tier => (
                          <div key={tier.factor_count} className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
                            <div className="flex items-center justify-between text-xs font-mono">
                              <span className="text-slate-400 font-bold">{tier.factor_label}</span>
                              <DangerBadge level={tier.danger_level} />
                            </div>
                            <div className="text-xl font-mono font-bold text-slate-100">{tier.total_reports} Reports</div>
                            <div className="flex justify-between text-[11px] font-mono text-slate-400">
                              <span>High Risk: <strong className={tier.high_risk_percentage > 50 ? 'text-red-400' : 'text-slate-300'}>{tier.high_risk_percentage}%</strong></span>
                              <span>Score: <strong className="text-cyan-300">{tier.danger_score}/100</strong></span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Operational breakdown with Dynamic Visual Rule */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Unit distribution */}
                    <div className="bg-[#131E31]/80 border border-slate-800 rounded-2xl p-5 space-y-4">
                      <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">Refinery Unit Distribution</h3>
                      {counts?.by_refinery_unit && Object.keys(counts.by_refinery_unit).length > 1 ? (
                        <div className="space-y-2 text-xs font-mono">
                          {Object.entries(counts.by_refinery_unit).slice(0, 6).map(([unit, cnt]) => (
                            <div key={unit} className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800">
                              <span className="text-slate-300">{unit}</span>
                              <span className="text-cyan-400 font-bold">{cnt} reports</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs font-mono text-slate-400">
                          {counts?.by_refinery_unit && Object.keys(counts.by_refinery_unit).length === 1 ? (
                            <span>All reports in this dataset are assigned to <strong className="text-cyan-300">{Object.keys(counts.by_refinery_unit)[0]}</strong> (single-unit focus).</span>
                          ) : (
                            <span>No refinery unit field recorded in current dataset scope.</span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Action Telemetry */}
                    <div className="bg-[#131E31]/80 border border-slate-800 rounded-2xl p-5 space-y-4">
                      <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">Action Status Telemetry</h3>
                      <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                        <div className="p-3 rounded-lg bg-amber-950/20 border border-amber-500/30">
                          <span className="text-slate-400 text-[10px] uppercase block">OPEN ACTIONS</span>
                          <span className="text-xl font-bold text-amber-400">{actionStats?.open_count || 0}</span>
                        </div>
                        <div className="p-3 rounded-lg bg-blue-950/20 border border-blue-500/30">
                          <span className="text-slate-400 text-[10px] uppercase block">IN PROGRESS</span>
                          <span className="text-xl font-bold text-blue-400">{actionStats?.in_progress_count || 0}</span>
                        </div>
                        <div className="p-3 rounded-lg bg-red-950/20 border border-red-500/30">
                          <span className="text-slate-400 text-[10px] uppercase block">OVERDUE</span>
                          <span className="text-xl font-bold text-red-400">{actionStats?.overdue_count || 0}</span>
                        </div>
                        <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/30">
                          <span className="text-slate-400 text-[10px] uppercase block">CLOSED</span>
                          <span className="text-xl font-bold text-emerald-400">{actionStats?.closed_count || 0}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB: FACTOR INTELLIGENCE (NEW) */}
              {tab === 'factors' && factorCombinations && (
                <div className="space-y-6">
                  {/* Overview */}
                  <div className="bg-[#131E31]/90 border border-slate-800 rounded-2xl p-6">
                    <h2 className="text-base font-mono font-bold text-slate-100 uppercase tracking-wider mb-1 flex items-center gap-2">
                      Multi-Factor Safety Matrix & Compound Danger Escalation
                    </h2>
                    <p className="text-xs font-sans text-slate-300">
                      Empirical breakdown of 950 refinery safety reports grouped into 1-factor, 2-factor, 3-factor, and 4-factor combination tiers.
                    </p>
                  </div>

                  {/* Compounding Tiers */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {factorCombinations.by_factor_count.map(tier => (
                      <div key={tier.factor_count} className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 font-bold">{tier.factor_label}</span>
                            <DangerBadge level={tier.danger_level} />
                          </div>
                          <div className="text-2xl font-mono font-bold text-slate-100 mb-1">{tier.total_reports} Reports</div>
                          <div className="text-xs font-sans text-slate-400 mb-4">{tier.datasets_count} Workbook Sheets</div>
                        </div>

                        <div className="space-y-2 pt-3 border-t border-slate-800 text-xs font-mono">
                          <div className="flex justify-between">
                            <span className="text-slate-500">High-Risk Rate:</span>
                            <strong className={tier.high_risk_percentage > 50 ? 'text-red-400 font-bold' : 'text-slate-200'}>
                              {tier.high_risk_percentage}% ({tier.high_risk_reports})
                            </strong>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">SIF Precursors:</span>
                            <strong className="text-rose-400 font-bold">{tier.sif_precursor_count}</strong>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Danger Score:</span>
                            <strong className="text-cyan-300 font-bold">{tier.danger_score}/100</strong>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Danger Rankings */}
                  <div className="bg-[#131E31]/90 border border-slate-800 rounded-2xl p-6 space-y-4">
                    <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
                      Compound Danger Rankings Across Combination Tiers
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs font-mono">
                        <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                          <tr>
                            <th className="p-3">Rank</th>
                            <th className="p-3">Combination Tier</th>
                            <th className="p-3">Active Factors</th>
                            <th className="p-3 text-center">Reports</th>
                            <th className="p-3 text-center">High Risk %</th>
                            <th className="p-3 text-center">SIF Precursors</th>
                            <th className="p-3 text-center">Score</th>
                            <th className="p-3 text-right">Danger Assessment</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {factorCombinations.danger_rankings.map(r => (
                            <tr key={r.combination_tier} className="hover:bg-slate-800/40">
                              <td className="p-3 font-bold text-cyan-400">#{r.rank}</td>
                              <td className="p-3 font-bold text-slate-200">{r.combination_tier}</td>
                              <td className="p-3">
                                <div className="flex flex-wrap gap-1">
                                  {r.factors.map((f, i) => (
                                    <span key={i} className="px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-300 text-[10px]">{f}</span>
                                  ))}
                                </div>
                              </td>
                              <td className="p-3 text-center font-bold">{r.report_count}</td>
                              <td className="p-3 text-center"><span className={r.high_risk_pct > 50 ? 'text-red-400 font-bold' : 'text-slate-300'}>{r.high_risk_pct}%</span></td>
                              <td className="p-3 text-center text-rose-300 font-bold">{r.sif_precursors}</td>
                              <td className="p-3 text-center text-cyan-300 font-bold">{r.danger_score}/100</td>
                              <td className="p-3 text-right"><DangerBadge level={r.danger_level} /></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB: HIGH-POTENTIAL INCIDENTS (NEW) */}
              {tab === 'hipo' && hipoData && (
                <div className="space-y-6">
                  <div className="bg-gradient-to-r from-red-950/40 via-slate-900 to-slate-900 border border-red-500/30 rounded-2xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="h-2.5 w-2.5 rounded-full bg-red-500 animate-ping"></span>
                        <h2 className="text-base font-mono font-bold text-red-300 uppercase tracking-wider">
                          Dedicated High-Potential (HiPo) Incident Telemetry
                        </h2>
                      </div>
                      <p className="text-xs font-sans text-slate-300 max-w-2xl">
                        Analysis of 100 operational near-miss events where multiple defense barriers were simultaneously compromised.
                      </p>
                    </div>

                    <div className="flex items-center gap-4 text-center">
                      <div className="bg-slate-950/80 px-4 py-2.5 rounded-xl border border-slate-800">
                        <span className="text-[10px] font-mono text-slate-500 uppercase block">RECORDED HIGH RISK</span>
                        <span className="text-2xl font-mono font-extrabold text-red-400">{hipoData.high_risk_percentage}%</span>
                      </div>
                      <div className="bg-slate-950/80 px-4 py-2.5 rounded-xl border border-slate-800">
                        <span className="text-[10px] font-mono text-slate-500 uppercase block">SIF PRECURSOR RATE</span>
                        <span className="text-2xl font-mono font-extrabold text-rose-300">{hipoData.sif_precursor_rate_percentage}%</span>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-[#131E31]/80 border border-slate-800 rounded-2xl p-5 space-y-4">
                      <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">Top High-Potential Root Causes</h4>
                      <div className="space-y-2 text-xs font-mono">
                        {Object.entries(hipoData.top_causes || {}).slice(0, 6).map(([c, cnt]) => (
                          <div key={c} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                            <span className="text-slate-300 truncate max-w-[80%]">{c}</span>
                            <span className="text-red-400 font-bold">{cnt}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="bg-[#131E31]/80 border border-slate-800 rounded-2xl p-5 space-y-4">
                      <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">Top High-Potential Consequences</h4>
                      <div className="space-y-2 text-xs font-mono">
                        {Object.entries(hipoData.top_consequences || {}).slice(0, 6).map(([c, cnt]) => (
                          <div key={c} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                            <span className="text-slate-300 truncate max-w-[80%]">{c}</span>
                            <span className="text-rose-400 font-bold">{cnt}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-[#131E31]/80 border border-slate-800 rounded-2xl p-5 space-y-3">
                      <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-300"> Multi-Barrier Failure Insights</h4>
                      <ul className="space-y-2 text-xs font-sans text-slate-300">
                        {hipoData.barrier_failure_insights.map((insight, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="text-cyan-400 font-bold">•</span>
                            <span>{insight}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="bg-[#131E31]/80 border border-slate-800 rounded-2xl p-5 space-y-3">
                      <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-300"> Proactive Engineering Imperatives</h4>
                      <ul className="space-y-2 text-xs font-sans text-slate-300">
                        {hipoData.preventive_imperatives.map((imp, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="text-emerald-400 font-bold"></span>
                            <span>{imp}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB: DATASET COMPARISON (NEW) */}
              {tab === 'comparison' && (
                <div className="space-y-6">
                  <div className="bg-[#131E31]/90 border border-slate-800 rounded-2xl p-6">
                    <h2 className="text-base font-mono font-bold text-slate-100 uppercase tracking-wider mb-1 flex items-center gap-2">
                      Side-by-Side Dataset Comparative Intelligence
                    </h2>
                    <p className="text-xs font-sans text-slate-400">
                      Compare risk distributions, factor counts, root causes, and barrier failure modes between any two refinery datasets.
                    </p>
                  </div>

                  {/* Dataset Selectors */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-slate-900 border border-cyan-500/40 rounded-xl space-y-2">
                      <label className="text-[10px] font-mono text-cyan-400 uppercase font-bold block">Dataset A (Baseline)</label>
                      <select
                        value={compA}
                        onChange={(e) => setCompA(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs font-mono text-slate-200"
                      >
                        {datasets.map(d => (
                          <option key={d.id} value={d.id}>{d.sheet_name || d.dataset_name} ({d.row_count} rows)</option>
                        ))}
                      </select>
                    </div>

                    <div className="p-4 bg-slate-900 border border-purple-500/40 rounded-xl space-y-2">
                      <label className="text-[10px] font-mono text-purple-400 uppercase font-bold block">Dataset B (Comparison)</label>
                      <select
                        value={compB}
                        onChange={(e) => setCompB(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs font-mono text-slate-200"
                      >
                        {datasets.map(d => (
                          <option key={d.id} value={d.id}>{d.sheet_name || d.dataset_name} ({d.row_count} rows)</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Comparison Results */}
                  {comparisonResult && (
                    <div className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Dataset A Card */}
                        <div className="p-5 rounded-2xl bg-[#131E31]/80 border border-cyan-500/30 space-y-4">
                          <div className="flex justify-between items-center">
                            <h3 className="text-sm font-mono font-bold text-cyan-300">{comparisonResult.dataset_a.name}</h3>
                            <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 text-[10px] font-mono font-bold">{comparisonResult.dataset_a.type}</span>
                          </div>
                          <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
                            <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800">
                              <span className="text-slate-500 text-[10px] block">REPORTS</span>
                              <strong className="text-lg text-slate-100">{comparisonResult.dataset_a.total_reports}</strong>
                            </div>
                            <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800">
                              <span className="text-slate-500 text-[10px] block">HIGH RISK</span>
                              <strong className="text-lg text-red-400">{comparisonResult.dataset_a.high_risk_percentage}%</strong>
                            </div>
                            <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800">
                              <span className="text-slate-500 text-[10px] block">SIF PRECURSORS</span>
                              <strong className="text-lg text-rose-300">{comparisonResult.dataset_a.sif_precursors}</strong>
                            </div>
                          </div>
                        </div>

                        {/* Dataset B Card */}
                        <div className="p-5 rounded-2xl bg-[#131E31]/80 border border-purple-500/30 space-y-4">
                          <div className="flex justify-between items-center">
                            <h3 className="text-sm font-mono font-bold text-purple-300">{comparisonResult.dataset_b.name}</h3>
                            <span className="px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800 text-[10px] font-mono font-bold">{comparisonResult.dataset_b.type}</span>
                          </div>
                          <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
                            <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800">
                              <span className="text-slate-500 text-[10px] block">REPORTS</span>
                              <strong className="text-lg text-slate-100">{comparisonResult.dataset_b.total_reports}</strong>
                            </div>
                            <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800">
                              <span className="text-slate-500 text-[10px] block">HIGH RISK</span>
                              <strong className="text-lg text-red-400">{comparisonResult.dataset_b.high_risk_percentage}%</strong>
                            </div>
                            <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800">
                              <span className="text-slate-500 text-[10px] block">SIF PRECURSORS</span>
                              <strong className="text-lg text-rose-300">{comparisonResult.dataset_b.sif_precursors}</strong>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* AI Comparative Insights */}
                      <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl space-y-3">
                        <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">AI SIF Comparative Insights</h4>
                        <ul className="space-y-2 text-xs font-sans text-slate-300">
                          {comparisonResult.comparative_insights.map((ins, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <span className="text-cyan-400 font-bold">•</span>
                              <span>{ins}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* TAB: REPORTS EXPLORER */}
              {tab === 'reports' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between gap-3">
                    <input
                      type="text"
                      value={search}
                      onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                      placeholder="Search reports by keyword, cause, description..."
                      className="w-80 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 text-xs font-sans text-slate-100 focus:outline-none focus:border-cyan-500"
                    />
                    <button
                      onClick={() => setIsReportGenOpen(true)}
                      className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-cyan-400 font-mono text-xs font-bold hover:border-cyan-500"
                    >
                      Export Report 
                    </button>
                  </div>

                  <div className="bg-[#131E31]/90 border border-slate-800 rounded-2xl overflow-hidden">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                        <tr>
                          <th className="p-3.5">Report ID</th>
                          <th className="p-3.5">Unit</th>
                          <th className="p-3.5">Department</th>
                          <th className="p-3.5">Description</th>
                          <th className="p-3.5">Risk</th>
                          <th className="p-3.5">Status</th>
                          <th className="p-3.5 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {reports.map(r => (
                          <tr key={r.id} className="hover:bg-slate-800/40 transition-colors">
                            <td className="p-3.5 font-bold text-cyan-400">{r.original_id || r.id}</td>
                            <td className="p-3.5 text-slate-200">{r.refinery_unit || '—'}</td>
                            <td className="p-3.5 text-slate-300">{r.department || '—'}</td>
                            <td className="p-3.5 text-slate-300 font-sans truncate max-w-xs">{r.description}</td>
                            <td className="p-3.5"><RiskBadge level={r.risk_level} size="sm" /></td>
                            <td className="p-3.5 font-bold text-amber-400">{r.action_status || 'Open'}</td>
                            <td className="p-3.5 text-right space-x-2">
                              <button
                                onClick={() => handleOpenReport(r.id)}
                                className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-cyan-300 border border-slate-700"
                              >
                                View 
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* TAB: ACTION CENTER (PART 4) */}
              {tab === 'actions' && (
                <div className="space-y-6">
                  {/* Status Filter Tabs */}
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                    {[
                      { id: 'ALL', label: 'ALL ACTIONS', count: actionStats?.total_actions || 0, color: 'text-slate-100' },
                      { id: 'OVERDUE', label: 'OVERDUE', count: actionStats?.overdue_count || 0, color: 'text-red-400' },
                      { id: 'OPEN', label: 'OPEN', count: actionStats?.open_count || 0, color: 'text-amber-400' },
                      { id: 'IN_PROGRESS', label: 'IN PROGRESS', count: actionStats?.in_progress_count || 0, color: 'text-blue-400' },
                      { id: 'CLOSED', label: 'CLOSED', count: actionStats?.closed_count || 0, color: 'text-emerald-400' }
                    ].map(st => (
                      <button
                        key={st.id}
                        onClick={() => setActionTab(st.id)}
                        className={`p-4 rounded-xl border text-left transition-all ${
                          actionTab === st.id
                            ? 'bg-slate-800 border-cyan-500 ring-1 ring-cyan-500 shadow-md'
                            : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block mb-1">{st.label}</span>
                        <span className={`text-2xl font-mono font-bold ${st.color}`}>{st.count}</span>
                      </button>
                    ))}
                  </div>

                  {/* Actions List */}
                  <div className="space-y-3">
                    {actionItems.map(act => (
                      <div
                        key={act.report_id}
                        className={`p-4 rounded-xl border transition-all ${
                          act.is_overdue
                            ? 'bg-slate-900/90 border-red-500/40 shadow-sm shadow-red-950/40'
                            : 'bg-slate-900/80 border-slate-800 hover:border-cyan-500/40'
                        }`}
                      >
                        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                          <div className="space-y-1.5 flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-mono font-bold text-cyan-400 text-xs">{act.original_id || act.report_id}</span>
                              <span className="text-slate-500 text-xs font-mono">• {act.refinery_unit} • {act.department}</span>
                              <RiskBadge level={act.risk_level} size="sm" />
                              <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                                act.is_overdue ? 'bg-red-950 text-red-300 border-red-800 animate-pulse' : 'bg-slate-800 text-slate-300 border-slate-700'
                              }`}>
                                {act.action_status.toUpperCase()}
                              </span>
                            </div>
                            <p className="text-xs font-sans text-slate-100 font-medium">Corrective Action: "{act.corrective_action}"</p>
                            <p className="text-[11px] font-sans text-slate-400 truncate">Observation: "{act.problem}"</p>
                          </div>

                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs font-mono bg-slate-950 p-3 rounded-xl border border-slate-800 shrink-0 min-w-[280px]">
                            <div>
                              <span className="text-slate-500 text-[10px] block">ASSIGNED TO</span>
                              <span className="font-semibold text-slate-200">{act.assigned_to || 'Unassigned'}</span>
                            </div>
                            <div>
                              <span className="text-slate-500 text-[10px] block">DUE DATE</span>
                              <span className={act.is_overdue ? 'text-red-400 font-bold' : 'text-slate-200'}>
                                {act.due_date ? new Date(act.due_date).toLocaleDateString() : 'No date'}
                              </span>
                            </div>
                            <div>
                              <span className="text-slate-500 text-[10px] block">AUDIT</span>
                              <button onClick={() => handleOpenHistory(act.report_id)} className="text-cyan-400 underline font-bold">
                                {act.history_count} Logs 
                              </button>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            <button
                              onClick={() => {
                                setEditingAction(act);
                                setEditStatus(act.action_status);
                                setEditAssignedTo(act.assigned_to || '');
                                setEditAssignedDept(act.assigned_department || act.department || '');
                                setEditDueDate(act.due_date ? act.due_date.split('T')[0] : '');
                                setEditComments(act.action_comments || '');
                              }}
                              className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-bold"
                            >
                              Edit 
                            </button>
                            <button
                              onClick={() => handleTriggerEmailPreview(act.report_id, 'MANAGEMENT_ESCALATION')}
                              className="px-3 py-1.5 rounded-lg bg-red-950 hover:bg-red-900 text-red-300 border border-red-800 font-mono text-xs font-bold"
                            >
                               Escalate
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB: AI SAFETY CHATBOT */}
              {tab === 'chat' && (
                <div className="bg-[#131E31]/90 border border-slate-800 rounded-2xl flex flex-col h-[740px] overflow-hidden shadow-xl">
                  <div className="p-4 border-b border-slate-800 bg-slate-950/80 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-white shadow-md">
                        
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h2 className="text-xs font-mono font-bold text-slate-100 uppercase tracking-wider">
                            OIL Safety Intelligence Assistant
                          </h2>
                          <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-bold">
                            GROUNDED IN DATABASE
                          </span>
                        </div>
                        <p className="text-[11px] font-sans text-cyan-400">Strict zero-fabrication query engine over 1,025 database records</p>
                      </div>
                    </div>
                  </div>

                  {/* Preset Buttons */}
                  <div className="p-2.5 bg-slate-950/90 border-b border-slate-800 flex items-center gap-1.5 overflow-x-auto custom-scrollbar text-[11px] font-mono">
                    {[
                      "Which combination of safety factors is most dangerous?",
                      "Show high-potential near-miss reports.",
                      "Compare single-factor vs multi-factor datasets.",
                      "How many reports involve supervisor negligence?",
                      "How many reports involve maintenance delay?",
                      "How many reports involve repeated issues?",
                      "Show reports where only PPE is violated.",
                      "Summarize the current safety situation.",
                      "How many high-risk reports?",
                      "What are the most common immediate causes?"
                    ].map((q, i) => (
                      <button
                        key={i}
                        onClick={() => handleSendChat(q)}
                        className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 border border-slate-800 shrink-0 transition-all"
                      >
                        {q}
                      </button>
                    ))}
                  </div>

                  {/* Message Stream */}
                  <div className="flex-1 p-5 overflow-y-auto custom-scrollbar space-y-4">
                    {chatMessages.map((m, idx) => (
                      <div key={idx} className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}>
                        <div className={`max-w-3xl rounded-xl p-4 text-xs font-sans leading-relaxed ${
                          m.sender === 'user' ? 'bg-cyan-600 text-white rounded-br-none' : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-none'
                        }`}>
                          <div className="whitespace-pre-wrap font-sans text-xs space-y-1.5">{m.text}</div>
                          {m.relevantReports && m.relevantReports.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-slate-800 flex flex-wrap gap-2">
                              <span className="text-[10px] font-mono text-slate-500 uppercase block w-full">Inspect Reports:</span>
                              {m.relevantReports.map(r => (
                                <button
                                  key={r.id}
                                  onClick={() => handleOpenReport(r.id)}
                                  className="px-2 py-1 rounded bg-slate-950 hover:bg-slate-800 text-cyan-300 border border-cyan-500/40 font-mono text-[11px] font-bold"
                                >
                                  Report {r.original_id || r.id} 
                                </button>
                              ))}
                            </div>
                          )}
                          {m.suggestedActions && m.suggestedActions.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-slate-800 flex flex-wrap gap-1.5">
                              {m.suggestedActions.map((act, i) => (
                                <button
                                  key={i}
                                  onClick={() => handleSendChat(act)}
                                  className="px-2.5 py-1 rounded-full bg-slate-950 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 border border-slate-800 font-mono text-[10px]"
                                >
                                  {act}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                        <span className="text-[9px] font-mono text-slate-500 mt-1">{m.timestamp}</span>
                      </div>
                    ))}
                    {chatLoading && (
                      <div className="text-xs font-mono text-cyan-400 p-2 animate-pulse">
                         Consulting OIL safety database records...
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </div>

                  {/* Input Form */}
                  <div className="p-4 border-t border-slate-800 bg-slate-950/80">
                    <form onSubmit={(e) => { e.preventDefault(); handleSendChat(); }} className="flex items-center gap-2">
                      <input
                        type="text"
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        placeholder="Ask questions about safety reports, SIF precursors, refinery units..."
                        className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                      />
                      <button type="submit" disabled={chatLoading || !chatInput.trim()} className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-bold">
                        Send 
                      </button>
                    </form>
                  </div>
                </div>
              )}

              {/* TAB: SETTINGS & ESCALATION CONFIG */}
              {tab === 'settings' && (
                <div className="space-y-6">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-xs font-mono">
                    <button
                      onClick={() => setSettingsTab('system')}
                      className={`px-3 py-1.5 rounded-lg ${settingsTab === 'system' ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400 hover:bg-slate-900'}`}
                    >
                      System Telemetry
                    </button>
                    <button
                      onClick={() => setSettingsTab('escalations')}
                      className={`px-3 py-1.5 rounded-lg ${settingsTab === 'escalations' ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400 hover:bg-slate-900'}`}
                    >
                      Escalation Matrix ({notifConfigs.length})
                    </button>
                    <button
                      onClick={() => setSettingsTab('email_logs')}
                      className={`px-3 py-1.5 rounded-lg ${settingsTab === 'email_logs' ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400 hover:bg-slate-900'}`}
                    >
                      Email Logs ({emailLogs.length})
                    </button>
                    <button
                      onClick={() => setSettingsTab('audit')}
                      className={`px-3 py-1.5 rounded-lg ${settingsTab === 'audit' ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400 hover:bg-slate-900'}`}
                    >
                      Audit Trail ({auditLogs.length})
                    </button>
                  </div>

                  {settingsTab === 'system' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs font-mono">
                      <div className="bg-[#131E31]/80 border border-slate-800 rounded-xl p-5 space-y-2">
                        <h4 className="text-cyan-400 font-bold uppercase mb-2">Platform Environment</h4>
                        <div>SERVICE: <strong className="text-slate-100">{health?.service || 'OIL SIF Platform'}</strong></div>
                        <div>VERSION: <strong className="text-slate-100">{health?.version || '2.0.0'}</strong></div>
                        <div>DATABASE: <strong className="text-emerald-400">{health?.database || 'CONNECTED'}</strong></div>
                        <div>DATASETS LOADED: <strong className="text-cyan-300">{datasets.length}</strong></div>
                        <div>TOTAL SAFETY REPORTS: <strong className="text-emerald-400">{dbTotalReports}</strong></div>
                      </div>
                      <div className="bg-[#131E31]/80 border border-slate-800 rounded-xl p-5 space-y-2">
                        <h4 className="text-cyan-400 font-bold uppercase mb-2">Role Permissions</h4>
                        <div>ACTIVE ROLE: <strong className="text-cyan-300">{activeRole}</strong></div>
                        <div>ESCALATIONS: <strong className="text-slate-200">3-Tier Notification Matrix Enabled</strong></div>
                        <div>AUDIT LOGS: <strong className="text-emerald-400">Active Logging</strong></div>
                      </div>
                    </div>
                  )}

                  {settingsTab === 'escalations' && (
                    <div className="space-y-4">
                      {activeRole === 'Administrator' && (
                        <form onSubmit={handleAddConfig} className="bg-[#131E31]/80 border border-slate-800 rounded-xl p-4 grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs font-mono">
                          <div>
                            <label className="text-[10px] text-slate-400 uppercase block mb-1">Tier</label>
                            <select value={newTier} onChange={(e) => setNewTier(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200">
                              <option value="SAFETY_HSE">Safety / HSE</option>
                              <option value="DEPT_HEAD">Department Head</option>
                              <option value="MANAGEMENT">Management</option>
                            </select>
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 uppercase block mb-1">Role Title</label>
                            <input type="text" value={newRole} onChange={(e) => setNewRole(e.target.value)} placeholder="Lead HSE Engineer" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200" required />
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 uppercase block mb-1">Department</label>
                            <input type="text" value={newDept} onChange={(e) => setNewDept(e.target.value)} placeholder="Operations / All" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200" />
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 uppercase block mb-1">Email</label>
                            <div className="flex gap-2">
                              <input type="email" value={newEmail} onChange={(e) => setNewEmail(e.target.value)} placeholder="lead@oil.internal" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200" required />
                              <button type="submit" className="px-3 py-2 bg-cyan-600 text-white rounded-lg font-bold">Add</button>
                            </div>
                          </div>
                        </form>
                      )}

                      <div className="space-y-2">
                        {notifConfigs.map(cfg => (
                          <div key={cfg.id} className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between text-xs font-mono">
                            <div>
                              <span className="px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800 font-bold mr-2 text-[10px]">{cfg.tier}</span>
                              <strong className="text-slate-100">{cfg.role_name}</strong>
                              <span className="text-slate-400 ml-2">({cfg.email_address})</span>
                            </div>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${cfg.is_active ? 'bg-emerald-950 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}>
                              {cfg.is_active ? 'ACTIVE' : 'MUTED'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {settingsTab === 'email_logs' && (
                    <div className="space-y-3">
                      {emailLogs.map(l => (
                        <div key={l.id} className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono space-y-1">
                          <div className="flex justify-between text-[11px]">
                            <span className="text-cyan-400 font-bold">{l.recipient_email}</span>
                            <span className="text-slate-500">{new Date(l.sent_at).toLocaleString()}</span>
                          </div>
                          <div className="text-slate-200">{l.subject}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {settingsTab === 'audit' && (
                    <div className="space-y-2">
                      {auditLogs.map(a => (
                        <div key={a.id} className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono flex justify-between">
                          <div>
                            <span className="px-2 py-0.5 rounded bg-slate-800 text-cyan-300 font-bold mr-2 text-[10px]">{a.action_type}</span>
                            <span className="text-slate-300">{a.entity_type} ({a.entity_id || 'Global'})</span>
                          </div>
                          <span className="text-slate-500">{new Date(a.timestamp).toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </main>
          </div>

          {/* REPORT DETAIL MODAL WITH PART 4 ASK AI */}
          {selectedReport && (
            <Modal
              isOpen={isDetailOpen}
              onClose={() => setIsDetailOpen(false)}
              title={`Safety Report: ${selectedReport.original_id || selectedReport.id}`}
              subtitle={`${selectedReport.refinery_unit || 'Process Unit'} • ${selectedReport.department || 'Operations'}`}
              size="2xl"
            >
              <div className="space-y-4 text-xs font-mono text-slate-200">
                <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                  <button
                    onClick={() => setDetailTab('intelligence')}
                    className={`px-3 py-1.5 rounded-lg ${detailTab === 'intelligence' ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400'}`}
                  >
                    Intelligence & Facts
                  </button>
                  <button
                    onClick={() => setDetailTab('ask_ai')}
                    className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 ${detailTab === 'ask_ai' ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400'}`}
                  >
                    ASK AI ABOUT THIS REPORT
                  </button>
                  <button
                    onClick={() => handleTriggerEmailPreview(selectedReport.id, 'HIGH_RISK')}
                    className="ml-auto px-3 py-1.5 rounded-lg bg-red-950 text-red-300 border border-red-800 font-bold"
                  >
                     Escalate / Notify
                  </button>
                </div>

                {detailTab === 'intelligence' && (
                  <div className="space-y-4">
                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 font-sans">
                      "{selectedReport.description}"
                    </div>
                    {reportDetailAnalysis && (
                      <div className="grid grid-cols-2 gap-3">
                        <div className="p-3 rounded-lg bg-red-950/30 border border-red-500/30">
                          <strong className="text-red-300 block mb-1"> Immediate Action</strong>
                          <p className="font-sans">{reportDetailAnalysis.immediate_action_recommendation}</p>
                        </div>
                        <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-500/30">
                          <strong className="text-emerald-300 block mb-1"> Preventive Strategy</strong>
                          <p className="font-sans">{reportDetailAnalysis.preventive_action_recommendation}</p>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {detailTab === 'ask_ai' && (
                  <div className="space-y-3">
                    <div className="flex flex-wrap gap-1.5">
                      {[
                        'Why is this report important?',
                        'What is the potential safety consequence?',
                        'What immediate action is recommended?',
                        'Is this issue recurring?',
                        'What could happen if this remains unresolved?'
                      ].map((prompt, i) => (
                        <button
                          key={i}
                          onClick={() => handleSendReportChat(prompt)}
                          className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 text-[11px]"
                        >
                          {prompt}
                        </button>
                      ))}
                    </div>

                    <div className="h-[280px] overflow-y-auto custom-scrollbar p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                      {detailChatMessages.map((msg, i) => (
                        <div key={i} className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                          <div className={`p-3 rounded-xl max-w-lg text-xs font-sans ${msg.sender === 'user' ? 'bg-cyan-600 text-white' : 'bg-slate-900 border border-slate-800 text-slate-200'}`}>
                            {msg.text}
                          </div>
                        </div>
                      ))}
                      {detailChatLoading && <div className="text-cyan-400 animate-pulse"> Reasoning over report context...</div>}
                    </div>

                    <form onSubmit={(e) => { e.preventDefault(); handleSendReportChat(); }} className="flex gap-2">
                      <input
                        type="text"
                        value={detailChatInput}
                        onChange={(e) => setDetailChatInput(e.target.value)}
                        placeholder="Ask anything about this report..."
                        className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100"
                      />
                      <button type="submit" className="px-4 py-2 bg-cyan-600 text-white rounded-lg font-bold">Ask</button>
                    </form>
                  </div>
                )}
              </div>
            </Modal>
          )}

          {/* REPORT GENERATOR MODAL */}
          <Modal
            isOpen={isReportGenOpen}
            onClose={() => setIsReportGenOpen(false)}
            title="Generate Safety Intelligence Report"
            subtitle="Export executive reports with dynamic schema-aware filtering"
            size="xl"
          >
            <div className="space-y-4 text-xs font-mono text-slate-200">
              <div className="grid grid-cols-3 gap-3">
                {['PDF', 'EXCEL', 'CSV'].map(fmt => (
                  <button
                    key={fmt}
                    onClick={() => setGenFormat(fmt)}
                    className={`p-3 rounded-xl border text-center font-bold ${genFormat === fmt ? 'bg-cyan-950 border-cyan-500 text-cyan-300' : 'bg-slate-900 border-slate-800 text-slate-400'}`}
                  >
                    {fmt === 'PDF' ? ' Executive PDF' : fmt === 'EXCEL' ? ' Excel Workbook' : ' Raw CSV'}
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-3 gap-3 bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div>
                  <label className="text-[10px] text-slate-400 uppercase block mb-1">Risk Level</label>
                  <select value={genRisk} onChange={(e) => setGenRisk(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded p-1.5 text-slate-200">
                    <option value="">All</option>
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 uppercase block mb-1">Refinery Unit</label>
                  <input type="text" value={genUnit} onChange={(e) => setGenUnit(e.target.value)} placeholder="e.g. Hydrogen Unit" className="w-full bg-slate-900 border border-slate-800 rounded p-1.5 text-slate-200" />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 uppercase block mb-1">Department</label>
                  <input type="text" value={genDept} onChange={(e) => setGenDept(e.target.value)} placeholder="e.g. Maintenance" className="w-full bg-slate-900 border border-slate-800 rounded p-1.5 text-slate-200" />
                </div>
              </div>

              {genPreview && (
                <div className="bg-slate-900 p-3 rounded-xl border border-slate-800 flex justify-between">
                  <span>Matching Records: <strong className="text-cyan-400">{genPreview.total_matching_reports}</strong></span>
                  <span>High-Risk: <strong className="text-red-400">{genPreview.by_risk_level?.['High'] || 0}</strong></span>
                  <span>SIF Precursors: <strong className="text-rose-400">{genPreview.sif_precursor_count}</strong></span>
                </div>
              )}

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button onClick={() => setIsReportGenOpen(false)} className="px-4 py-2 bg-slate-800 rounded-lg text-slate-300">Cancel</button>
                <a
                  href={`/api/reports/export/${genFormat.toLowerCase()}?${new URLSearchParams({
                    ...(selectedDatasetId ? { dataset_id: selectedDatasetId } : {}),
                    ...(genRisk ? { risk_level: genRisk } : {}),
                    ...(genUnit ? { refinery_unit: genUnit } : {}),
                    ...(genDept ? { department: genDept } : {})
                  }).toString()}`}
                  download
                  className="px-5 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-lg font-bold shadow-md"
                >
                  Download {genFormat} Report 
                </a>
              </div>
            </div>
          </Modal>

          {/* EMAIL PREVIEW & ESCALATION MODAL */}
          {emailPreviewData && (
            <Modal
              isOpen={isEmailModalOpen}
              onClose={() => setIsEmailModalOpen(false)}
              title="Management Escalation • Mandatory Email Preview"
              subtitle={`Review notification for Report ${emailPreviewReport?.original_id || emailPreviewReport?.id} before sending`}
              size="2xl"
            >
              <div className="space-y-4 text-xs font-mono text-slate-200">
                {emailSentToast && (
                  <div className="p-3 bg-emerald-950 border border-emerald-500 rounded-lg text-emerald-300 font-bold">
                    {emailSentToast}
                  </div>
                )}
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                  <div>SUBJECT: <strong className="text-slate-100">{emailPreviewData.subject}</strong></div>
                  <div>RECIPIENTS: <strong className="text-cyan-400">{emailPreviewData.recipients.map(r => `${r.role_name} (${r.email_address})`).join(', ')}</strong></div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[360px] overflow-y-auto custom-scrollbar">
                  <div className="p-4 rounded-xl bg-slate-900 border border-blue-500/30 space-y-2">
                    <h5 className="font-bold text-blue-400 uppercase text-[11px]"> 1. Recorded Information (Facts)</h5>
                    <div>Unit: <strong>{emailPreviewData.recorded_information.refinery_unit}</strong></div>
                    <div>Department: <strong>{emailPreviewData.recorded_information.department}</strong></div>
                    <div>Risk: <RiskBadge level={emailPreviewData.recorded_information.recorded_risk_level} size="sm" /></div>
                    <p className="italic font-sans text-slate-300">"{emailPreviewData.recorded_information.observed_problem}"</p>
                  </div>

                  <div className="p-4 rounded-xl bg-purple-950/30 border border-purple-500/40 space-y-2">
                    <h5 className="font-bold text-purple-400 uppercase text-[11px]"> 2. AI SIF Recommendations</h5>
                    <div>AI Risk: <strong>{emailPreviewData.ai_recommendations.ai_risk_level}</strong></div>
                    <div>SIF Status: <strong>{emailPreviewData.ai_recommendations.sif_precursor}</strong></div>
                    <div className="p-2 bg-red-950/40 border border-red-500/40 rounded text-red-200 font-sans">
                       {emailPreviewData.ai_recommendations.immediate_action_recommendation}
                    </div>
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                  <button onClick={() => setIsEmailModalOpen(false)} className="px-4 py-2 bg-slate-800 rounded-lg text-slate-300">Cancel</button>
                  <button onClick={handleSendEmail} className="px-5 py-2 bg-gradient-to-r from-red-600 to-rose-600 text-white rounded-lg font-bold shadow-md">
                    Confirm & Dispatch Email 
                  </button>
                </div>
              </div>
            </Modal>
          )}

          {/* EDIT ACTION MODAL */}
          {editingAction && (
            <Modal
              isOpen={true}
              onClose={() => setEditingAction(null)}
              title={`Action Governance: Report ${editingAction.original_id || editingAction.report_id}`}
              subtitle="Update status, assignee, target due date, and comments"
              size="lg"
            >
              <form onSubmit={handleSaveActionUpdate} className="space-y-4 text-xs font-mono text-slate-200">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[10px] text-slate-400 uppercase block mb-1">Status</label>
                    <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded p-2 text-slate-200">
                      <option value="Open">Open</option>
                      <option value="In Progress">In Progress</option>
                      <option value="Closed">Closed</option>
                      <option value="Overdue">Overdue</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400 uppercase block mb-1">Due Date</label>
                    <input type="date" value={editDueDate} onChange={(e) => setEditDueDate(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded p-2 text-slate-200" />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400 uppercase block mb-1">Assignee</label>
                    <input type="text" value={editAssignedTo} onChange={(e) => setEditAssignedTo(e.target.value)} placeholder="e.g. John Doe" className="w-full bg-slate-900 border border-slate-800 rounded p-2 text-slate-200" />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400 uppercase block mb-1">Department</label>
                    <input type="text" value={editAssignedDept} onChange={(e) => setEditAssignedDept(e.target.value)} placeholder="e.g. Maintenance" className="w-full bg-slate-900 border border-slate-800 rounded p-2 text-slate-200" />
                  </div>
                </div>

                <div>
                  <label className="text-[10px] text-slate-400 uppercase block mb-1">Comments</label>
                  <textarea value={editComments} onChange={(e) => setEditComments(e.target.value)} placeholder="Action notes..." rows={3} className="w-full bg-slate-900 border border-slate-800 rounded p-2 text-slate-200 font-sans" />
                </div>

                <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                  <button type="button" onClick={() => setEditingAction(null)} className="px-4 py-2 bg-slate-800 rounded-lg text-slate-300">Cancel</button>
                  <button type="submit" className="px-5 py-2 bg-cyan-600 text-white rounded-lg font-bold">Save & Log </button>
                </div>
              </form>
            </Modal>
          )}

          {/* ACTION AUDIT HISTORY MODAL */}
          {historyReportId && (
            <Modal
              isOpen={true}
              onClose={() => setHistoryReportId(null)}
              title="Action Audit History Trail"
              subtitle={`Modifications recorded for Report ${historyReportId}`}
              size="lg"
            >
              <div className="space-y-3 text-xs font-mono text-slate-200 max-h-[380px] overflow-y-auto custom-scrollbar">
                {historyList.map(h => (
                  <div key={h.id} className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                    <div className="flex justify-between text-[11px]">
                      <span className="font-bold text-cyan-400">{h.actor_name} ({h.actor_role})</span>
                      <span className="text-slate-500">{new Date(h.timestamp).toLocaleString()}</span>
                    </div>
                    <div>Status: <strong className="text-slate-400">{h.old_status}</strong>  <strong className="text-cyan-300">{h.new_status}</strong></div>
                    {h.comments && <p className="font-sans text-slate-300 italic">"{h.comments}"</p>}
                  </div>
                ))}
              </div>
            </Modal>
          )}
        </div>
      );
    }

    ReactDOM.createRoot(document.getElementById('root')).render(<App />);
  </script>
</body>
</html>
"""

@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
def get_control_room_dashboard():
    return DASHBOARD_HTML
