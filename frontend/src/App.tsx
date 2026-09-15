import React, { useState, useEffect, useCallback } from 'react';
import {
  HealthStatus,
  DatasetItem,
  SafetyReport,
  ReportCounts,
  SIFSummary,
  MetadataFieldOption,
  PaginatedResponse,
  UserRole
} from './types/safety';
import { api } from './services/api';

import { Sidebar, NavTab } from './components/layout/Sidebar';
import { TopBar } from './components/layout/TopBar';

import { KPICards } from './components/dashboard/KPICards';
import { RiskDistribution } from './components/dashboard/RiskDistribution';
import { ReportTrend } from './components/dashboard/ReportTrend';
import { RefineryUnitChart } from './components/dashboard/RefineryUnitChart';
import { CauseConsequence } from './components/dashboard/CauseConsequence';
import { PPEProblemChart } from './components/dashboard/PPEProblemChart';

import { ReportFilters } from './components/reports/ReportFilters';
import { ColumnSelector, ColumnDef } from './components/reports/ColumnSelector';
import { ReportTable } from './components/reports/ReportTable';
import { ReportDetailModal } from './components/reports/ReportDetailModal';
import { ReportGeneratorModal } from './components/reports/ReportGeneratorModal';
import { SubmitReportModal } from './components/reports/SubmitReportModal';

import { SIFView } from './components/sif/SIFView';
import { FactorsView } from './components/factors/FactorsView';
import { PredictabilityView } from './components/predictability/PredictabilityView';
import { ActionsView } from './components/actions/ActionsView';
import { AISafetyChat } from './components/chat/AISafetyChat';
import { AnalyticsView } from './components/analytics/AnalyticsView';
import { DatasetsView } from './components/datasets/DatasetsView';
import { SettingsView } from './components/settings/SettingsView';
import { EmptyState } from './components/common/EmptyState';
import { SafetyConvergenceIntelligence } from './components/dashboard/SafetyConvergenceIntelligence';
import { ImmediateSafetyPriorities } from './components/dashboard/ImmediateSafetyPriorities';
import { ControlRoomDashboard } from './components/dashboard/ControlRoomDashboard';
import { ManagementView } from './components/management/ManagementView';
import { DemoSimulationModal } from './components/demo/DemoSimulationModal';

export const App: React.FC = () => {
  // Navigation
  const [activeTab, setActiveTab] = useState<NavTab>('dashboard');
  const [dashboardSubTab, setDashboardSubTab] = useState<'control_room' | 'management'>('control_room');
  const [chatInitialQuery, setChatInitialQuery] = useState<string>('');

  // Demo / Simulation Mode State
  const [isDemoModalOpen, setIsDemoModalOpen] = useState<boolean>(false);
  const [isDemoModeActive, setIsDemoModeActive] = useState<boolean>(false);

  // Security & Role-Based Access Control
  const [activeRole, setActiveRole] = useState<UserRole>('Safety Officer');


  // Core Data State
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('');
  const [counts, setCounts] = useState<ReportCounts | null>(null);
  const [sifSummary, setSifSummary] = useState<SIFSummary | null>(null);
  const [filterFields, setFilterFields] = useState<MetadataFieldOption[]>([]);

  // Reports Table State
  const [reports, setReports] = useState<SafetyReport[]>([]);
  const [reportsTotal, setReportsTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(15);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [search, setSearch] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('report_date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});

  // Single Report Modal
  const [selectedReport, setSelectedReport] = useState<SafetyReport | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState<boolean>(false);

  // Submit Safety Report Modal (Part 1 Foundation)
  const [isSubmitReportOpen, setIsSubmitReportOpen] = useState<boolean>(false);

  // Report Generator Modal (Part 4)
  const [isReportGeneratorOpen, setIsReportGeneratorOpen] = useState<boolean>(false);

  // Column Customization
  const [columns, setColumns] = useState<ColumnDef[]>([
    { key: 'original_id', label: 'Report ID', visible: true, required: true },
    { key: 'report_date', label: 'Date', visible: true },
    { key: 'refinery_unit', label: 'Refinery Unit', visible: true },
    { key: 'equipment', label: 'Equipment ID', visible: true },
    { key: 'work_type', label: 'Work Type', visible: true },
    { key: 'department', label: 'Department', visible: true },
    { key: 'description', label: 'Description', visible: true },
    { key: 'risk_level', label: 'Risk Level', visible: true },
    { key: 'potential_consequence', label: 'Consequence', visible: true },
    { key: 'immediate_cause', label: 'Immediate Cause', visible: false },
    { key: 'corrective_action', label: 'Corrective Action', visible: true },
    { key: 'action_status', label: 'Action Status', visible: true },
  ]);

  const handleToggleColumn = (key: string) => {
    setColumns((prev) =>
      prev.map((c) => (c.key === key && !c.required ? { ...c, visible: !c.visible } : c))
    );
  };

  // Initial Load: Health, Datasets, Metadata, Counts, SIF Summary
  useEffect(() => {
    api.getHealth().then(setHealth).catch(console.error);

    api.getDatasets(1, 10)
      .then((res) => {
        setDatasets(res.items || []);
        if (res.items && res.items.length > 0 && !selectedDatasetId) {
          setSelectedDatasetId(res.items[0].id);
        }
      })
      .catch(console.error);

    api.getMetadataFields()
      .then((res) => setFilterFields(res.available_filters || []))
      .catch(console.error);

    api.getDemoStatus()
      .then((st) => setIsDemoModeActive(st.demo_mode_active))
      .catch(() => {});
  }, []);


  // Fetch Dataset-Specific Summaries
  const refreshSummaries = useCallback(() => {
    api.getReportCounts(selectedDatasetId).then(setCounts).catch(console.error);
    api.getSIFSummary(selectedDatasetId).then(setSifSummary).catch(console.error);
  }, [selectedDatasetId]);

  useEffect(() => {
    refreshSummaries();
  }, [refreshSummaries]);

  // Fetch Reports on Filter/Page/Sort Change
  const fetchReports = useCallback(() => {
    const params: Record<string, any> = {
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
      search: search.trim() || undefined,
      dataset_id: selectedDatasetId || undefined,
      ...activeFilters,
    };

    api.getReports(params)
      .then((res: PaginatedResponse<SafetyReport>) => {
        setReports(res.items || []);
        setReportsTotal(res.total || 0);
        setTotalPages(res.total_pages || 1);
      })
      .catch(console.error);
  }, [page, pageSize, sortBy, sortOrder, search, selectedDatasetId, activeFilters]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);



  // Filter Handler
  const handleFilterChange = (key: string, val: string) => {
    setActiveFilters((prev) => {
      const next = { ...prev };
      if (val === '') {
        delete next[key];
      } else {
        next[key] = val;
      }
      return next;
    });
    setPage(1);
  };

  const handleClearFilters = () => {
    setSearch('');
    setActiveFilters({});
    setPage(1);
  };

  // Quick navigation filter shortcuts from dashboard cards
  const handleQuickFilterRisk = (risk: string) => {
    handleFilterChange('risk_level', risk);
    setActiveTab('reports');
  };

  const handleQuickFilterStatus = (status: string) => {
    handleFilterChange('action_status', status);
    setActiveTab('reports');
  };

  const handleQuickFilterUnit = (unit: string) => {
    handleFilterChange('refinery_unit', unit);
    setActiveTab('reports');
  };

  const handleQuickFilterConsequence = (consequence: string) => {
    handleFilterChange('potential_consequence', consequence);
    setActiveTab('reports');
  };

  const handleOpenReportById = async (reportId: string) => {
    try {
      const rep = await api.getReport(reportId);
      setSelectedReport(rep);
      setIsDetailOpen(true);
    } catch (e) {
      console.error(e);
    }
  };

  const handleOpenReportDetail = (report: SafetyReport) => {
    setSelectedReport(report);
    setIsDetailOpen(true);
  };

  const hasDateField = filterFields.some((f) => f.field_name === 'report_date' || f.data_type === 'DATETIME');

  return (
    <div className="flex bg-[#F4F7FA] text-[#172B3A] min-h-screen font-sans antialiased selection:bg-[#1769AA] selection:text-white">
      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        highRiskCount={counts?.by_risk_level?.['High'] || counts?.by_risk_level?.['HIGH'] || 0}
        sifCount={sifSummary?.sif_precursors_detected || 0}
        overdueCount={counts?.by_action_status?.['Overdue'] || counts?.by_action_status?.['OVERDUE'] || 0}
        activeRole={activeRole}
        onOpenSubmitReport={() => setIsSubmitReportOpen(true)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-x-hidden">
        {/* Hackathon Simulation Mode Glowing Top Banner */}
        {isDemoModeActive && (
          <div className="bg-amber-50 border-b border-amber-200 px-6 py-2 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
              <span className="text-xs font-semibold text-amber-900"> Simulation Mode Active</span>
              <span className="text-xs text-[#526575] hidden sm:inline">· External notifications suppressed</span>
            </div>
            <button
              onClick={() => setIsDemoModalOpen(true)}
              className="px-3 py-1 bg-amber-100 hover:bg-amber-200 border border-amber-300 text-amber-900 text-xs font-semibold rounded-lg transition-colors shadow-sm"
            >
              Open Simulation Controller
            </button>
          </div>
        )}

        <TopBar
          title={
            activeTab === 'dashboard'
              ? 'Control Room Dashboard'
              : activeTab === 'reports'
              ? 'Safety Reports Explorer'
              : activeTab === 'sif'
              ? 'SIF Precursor Intelligence'
              : activeTab === 'predictability'
              ? 'SIF Risk Prediction & Preventive Intelligence'
              : activeTab === 'actions'
              ? 'Action Center & Governance Tracker'
              : activeTab === 'chat'
              ? 'OIL Safety Intelligence Assistant'
              : activeTab === 'analytics'
              ? 'Deep Operational Analytics'
              : activeTab === 'datasets'
              ? 'Central Dataset Registry & Schema'
              : 'Escalations, Audit Logs & Settings'
          }
          subtitle="OIL SIF Intelligence Platform • Supervisor Report Submission & Control Room"
          datasets={datasets}
          selectedDatasetId={selectedDatasetId}
          onSelectDataset={setSelectedDatasetId}
          systemStatus={health?.database || 'connected'}
          totalReports={counts?.total_reports || 0}
          activeRole={activeRole}
          onRoleChange={setActiveRole}
          onOpenReportGenerator={() => setIsReportGeneratorOpen(true)}
          onOpenSubmitReport={() => setIsSubmitReportOpen(true)}
        />

        <main className="p-8 space-y-8 flex-1 max-w-[1680px] w-full mx-auto">
          {/* TAB 1: DASHBOARD */}
          {activeTab === 'dashboard' && (
            <div className="space-y-8">
              {/* Dashboard View Sub-Tab Switcher */}
              <div className="flex items-center justify-between pb-1">
                <div className="flex items-center gap-1 bg-[#EEF3F7] border border-[#D9E2EA] rounded-xl p-1 shadow-inner">
                  <button
                    onClick={() => setDashboardSubTab('control_room')}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 ${
                      dashboardSubTab === 'control_room'
                        ? 'bg-white text-[#123B5D] shadow-sm border border-[#D9E2EA]'
                        : 'text-[#526575] hover:text-[#172B3A]'
                    }`}
                  >
                    Control Room
                  </button>
                  <button
                    onClick={() => setDashboardSubTab('management')}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 ${
                      dashboardSubTab === 'management'
                        ? 'bg-white text-[#123B5D] shadow-sm border border-[#D9E2EA]'
                        : 'text-[#526575] hover:text-[#172B3A]'
                    }`}
                  >
                    Executive View
                  </button>
                </div>
                <span className="text-xs text-[#718394] font-medium">
                  Live database telemetry
                </span>
              </div>


              {dashboardSubTab === 'control_room' ? (
                <>
                  {/* STEP 1: SAFETY OVERVIEW & ATTENTION METRICS */}
                  <KPICards
                    counts={counts}
                    sifSummary={sifSummary}
                    onFilterRisk={handleQuickFilterRisk}
                    onFilterStatus={handleQuickFilterStatus}
                    onFilterSIF={() => setActiveTab('sif')}
                  />

                  {/* STEP 2: IMMEDIATE SAFETY PRIORITIES (TOP 3 ACTIVE SAFETY ITEMS) */}
                  <ImmediateSafetyPriorities
                    reports={reports}
                    onViewReport={handleOpenReportById}
                    onViewAllReports={() => setActiveTab('reports')}
                  />

                  {/* STEP 3: PRIORITY SAFETY ALERTS, BARRIER HEALTH & GOVERNANCE */}
                  <SafetyConvergenceIntelligence
                    datasetId={selectedDatasetId}
                    onViewReport={handleOpenReportById}
                    onViewAction={(_actionId) => setActiveTab('actions')}
                    onOpenChatWithQuery={(q) => {
                      setChatInitialQuery(q);
                      setActiveTab('chat');
                    }}
                  />
                </>
              ) : (
                <ManagementView
                  datasetId={selectedDatasetId}
                  onOpenReport={handleOpenReportById}
                />
              )}
            </div>
          )}

          {/* TAB 2: REPORTS EXPLORER */}
          {activeTab === 'reports' && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <ReportFilters
                  search={search}
                  onSearchChange={(s) => {
                    setSearch(s);
                    setPage(1);
                  }}
                  filters={activeFilters}
                  onFilterChange={handleFilterChange}
                  onClearFilters={handleClearFilters}
                  availableFilterFields={filterFields}
                  onOpenSubmitReport={() => setIsSubmitReportOpen(true)}
                />
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setIsReportGeneratorOpen(true)}
                    className="px-3.5 py-2 rounded-xl bg-white border border-[#D9E2EA] hover:border-[#1769AA] text-[#1769AA] hover:bg-[#EEF3F7] text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm"
                  >
                    Export Report
                  </button>
                  <ColumnSelector columns={columns} onToggleColumn={handleToggleColumn} />
                </div>
              </div>

              {reports.length === 0 ? (
                <EmptyState
                  type="no_filter_matches"
                  onClearFilters={handleClearFilters}
                />
              ) : (
                <ReportTable
                  reports={reports}
                  total={reportsTotal}
                  page={page}
                  pageSize={pageSize}
                  totalPages={totalPages}
                  onPageChange={setPage}
                  sortBy={sortBy}
                  sortOrder={sortOrder}
                  onSortChange={(col) => {
                    if (sortBy === col) {
                      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                    } else {
                      setSortBy(col);
                      setSortOrder('desc');
                    }
                  }}
                  onSelectReport={handleOpenReportDetail}
                  columns={columns}
                />
              )}
            </div>
          )}

          {/* TAB 3: SIF PRECURSOR INTELLIGENCE */}
          {activeTab === 'sif' && (
            <SIFView
              sifSummary={sifSummary}
              datasetId={selectedDatasetId}
              onOpenReport={handleOpenReportById}
            />
          )}

          {/* TAB 3.5: FACTOR & COMBINATION INTELLIGENCE */}
          {activeTab === 'factors' && (
            <FactorsView
              onOpenReport={handleOpenReportById}
            />
          )}

          {/* TAB 4: PREVENTIVE & RECURRENCE INTELLIGENCE */}
          {activeTab === 'predictability' && (
            <PredictabilityView
              datasetId={selectedDatasetId}
              onOpenReport={handleOpenReportById}
            />
          )}

          {/* TAB 5: ACTION CENTER (Part 4) */}
          {activeTab === 'actions' && (
            <ActionsView
              counts={counts}
              datasetId={selectedDatasetId}
              onOpenReport={handleOpenReportById}
            />
          )}

          {/* TAB 6: AI SAFETY CHATBOT (Part 4) */}
          {activeTab === 'chat' && (
            <AISafetyChat
              onOpenReport={handleOpenReportById}
              datasetId={selectedDatasetId}
              initialQuery={chatInitialQuery}
              onClearInitialQuery={() => setChatInitialQuery('')}
            />
          )}

          {/* TAB 7: ANALYTICS */}
          {activeTab === 'analytics' && (
            <AnalyticsView
              counts={counts}
              onSelectFilter={(field, val) => {
                handleFilterChange(field, val);
                setActiveTab('reports');
              }}
            />
          )}

          {/* TAB 8: DATASETS & QUALITY */}
          {activeTab === 'datasets' && (
            <DatasetsView
              datasets={datasets}
              selectedDatasetId={selectedDatasetId}
            />
          )}

          {/* TAB 9: SETTINGS, ESCALATIONS & AUDIT LOGS (Part 4) */}
          {activeTab === 'settings' && (
            <SettingsView
              health={health}
              activeRole={activeRole}
              onRoleChange={setActiveRole}
              onOpenDemo={() => setIsDemoModalOpen(true)}
            />
          )}
        </main>
      </div>

      {/* Demo & Simulation Controller Modal (Phase 8) */}
      {isDemoModalOpen && (
        <DemoSimulationModal
          onClose={() => {
            setIsDemoModalOpen(false);
            api.getDemoStatus().then((st) => setIsDemoModeActive(st.demo_mode_active)).catch(() => {});
          }}
          onOpenReport={handleOpenReportById}
        />
      )}

      {/* Report Detail Modal with Part 4 Ask AI & Action Governance */}
      <ReportDetailModal
        report={selectedReport}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        onActionUpdated={() => {
          fetchReports();
          refreshSummaries();
        }}
      />

      {/* Report Generator Modal (Part 4) */}
      <ReportGeneratorModal
        isOpen={isReportGeneratorOpen}
        onClose={() => setIsReportGeneratorOpen(false)}
        datasets={datasets}
        selectedDatasetId={selectedDatasetId}
        availableFilterFields={filterFields}
      />

      {/* Submit Safety Report Modal (Part 1 Foundation) */}
      <SubmitReportModal
        isOpen={isSubmitReportOpen}
        onClose={() => setIsSubmitReportOpen(false)}
        onReportSubmitted={(newReport) => {
          fetchReports();
          refreshSummaries();
          setSelectedReport(newReport);
        }}
        activeRole={activeRole}
        selectedDatasetId={selectedDatasetId}
      />
    </div>
  );
};

export default App;
