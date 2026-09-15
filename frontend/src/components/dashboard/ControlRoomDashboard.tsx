import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { SIFSummary, ReportCounts, RecurringIssuesResponse, BDISummaryResponse } from '../../types/safety';
import { InfoTooltip } from '../common/InfoTooltip';

interface ControlRoomDashboardProps {
  datasetId?: string;
  counts: ReportCounts | null;
  sifSummary: SIFSummary | null;
  onFilterSelect?: (field: string, value: string) => void;
}

export const ControlRoomDashboard: React.FC<ControlRoomDashboardProps> = ({
  datasetId,
  counts,
  sifSummary,
}) => {
  const [densityData, setDensityData] = useState<any | null>(null);
  const [recurringData, setRecurringData] = useState<RecurringIssuesResponse | null>(null);
  const [bdiSummary, setBdiSummary] = useState<BDISummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [showTechnicalAnalytics, setShowTechnicalAnalytics] = useState<boolean>(false);

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([
      api.getSIFDensity(datasetId),
      api.getMultiFactorAnalytics(datasetId),
      api.getRecurringIssues(datasetId),
      api.getBDISummary(datasetId)
    ])
      .then(([denRes, _mfRes, recRes, bdiRes]) => {
        if (denRes.status === 'fulfilled') setDensityData(denRes.value);
        if (recRes.status === 'fulfilled') setRecurringData(recRes.value);
        if (bdiRes.status === 'fulfilled') setBdiSummary(bdiRes.value);
      })
      .finally(() => setLoading(false));
  }, [datasetId]);

  if (!counts) return null;

  const total = counts.total_reports || 0;
  const unavailableDims: string[] = densityData?.unavailable_dimensions || [];

  // Data helpers
  const units = densityData?.dimension_rankings?.['Refinery Unit'] || [];
  const activities = densityData?.dimension_rankings?.['Activity / Work Type'] || [];
  const iogpRules = densityData?.dimension_rankings?.['IOGP Life-Saving Rule'] || [];
  const locations = densityData?.dimension_rankings?.['Location / Site'] || [];

  // Action closure counts
  const openActions = counts.by_action_status?.['Open'] || 0;
  const inProgressActions = counts.by_action_status?.['In Progress'] || 0;
  const overdueActions = counts.by_action_status?.['Overdue'] || 0;
  const closedActions = counts.by_action_status?.['Closed'] || 0;
  const totalActions = openActions + inProgressActions + overdueActions + closedActions || 1;

  return (
    <div className="space-y-8">
      {/* WHAT IS HAPPENING & PRIORITY ANALYTICS */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
          <div>
            <h2 className="text-sm font-bold text-[#172B3A] flex items-center gap-2">
              What Is Happening Across Operational Areas?
            </h2>
            <p className="text-xs text-[#526575] font-medium">
              Key safety indicators, precursor rates, and high-risk process units.
            </p>
          </div>
        </div>

        {/* Top 3 High-Level Question Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">

          {/* CARD 1: SIF Precursor Rate & Density */}
          <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-3 shadow-sm flex flex-col justify-between">
            <div className="flex items-center justify-between pb-2 border-b border-[#D9E2EA]">
              <div className="flex items-center gap-1">
                <h3 className="text-xs font-bold text-[#172B3A] uppercase tracking-wider">
                  SIF Precursor Rate
                </h3>
                <InfoTooltip
                  title="SIF Precursor Density"
                  text="Percentage of total safety reports that contain potential serious injury or fatality precursor conditions."
                />
              </div>
              <span className="text-[10px] font-extrabold text-[#D64545] bg-[#D64545]/15 px-2 py-0.5 rounded-lg border border-[#D64545]/30">
                PRECURSORS
              </span>
            </div>

            <div className="p-4 bg-[#EEF3F7] rounded-xl border border-[#D9E2EA] text-center space-y-1 my-auto shadow-xs">
              <span className="text-[11px] text-[#526575] uppercase font-bold tracking-wider block">
                Precursor Density (%)
              </span>
              <span className="text-4xl font-black text-[#D64545] tracking-tight block tabular-nums">
                {densityData?.sif_precursor_density_percentage || 0}%
              </span>
              <span className="text-xs text-[#526575] font-semibold block pt-1">
                {densityData?.sif_precursor_count || 0} SIF precursors identified out of {total} total reports
              </span>
            </div>
          </div>

          {/* CARD 2: Process Unit Breakdown */}
          <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-3 shadow-sm">
            <div className="flex items-center justify-between pb-2 border-b border-[#D9E2EA]">
              <div className="flex items-center gap-1">
                <h3 className="text-xs font-bold text-[#172B3A] uppercase tracking-wider">
                  Highest Risk Process Units
                </h3>
                <InfoTooltip
                  title="Unit Ranking"
                  text="Process units ranked by concentration of precursor safety conditions."
                />
              </div>
              <span className="text-[10px] font-bold text-[#1769AA] bg-[#EEF3F7] px-2 py-0.5 rounded-lg border border-[#D9E2EA]">
                UNIT RANKING
              </span>
            </div>

            {units.length > 0 ? (
              <div className="space-y-2 text-xs">
                {units.slice(0, 3).map((u: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between p-2.5 rounded-xl bg-[#EEF3F7] border border-[#D9E2EA] shadow-xs">
                    <span className="text-[#172B3A] font-bold truncate"> {u.name}</span>
                    <span className="font-extrabold text-[#D64545] text-xs">{u.sif_density_percentage}% ({u.sif_precursor_count}/{u.total_reports})</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 bg-[#EEF3F7] rounded-xl text-xs text-[#718394] font-medium border border-[#D9E2EA]">
                {unavailableDims.includes('Refinery Unit') ? 'Not available in active dataset.' : 'Calculating process unit metrics...'}
              </div>
            )}
          </div>

          {/* CARD 3: Action Remediation & SLA Closure */}
          <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-3 shadow-sm">
            <div className="flex items-center justify-between pb-2 border-b border-[#D9E2EA]">
              <div className="flex items-center gap-1">
                <h3 className="text-xs font-bold text-[#172B3A] uppercase tracking-wider">
                  Action Remediation Status
                </h3>
                <InfoTooltip
                  title="Action Remediation"
                  text="Overview of corrective safety action resolution and overdue remediation items."
                />
              </div>
              <span className="text-[10px] font-bold text-[#2E8B57] bg-[#EEF3F7] px-2 py-0.5 rounded-lg border border-[#D9E2EA]">
                ACTIONS
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#EEF3F7] border border-[#D9E2EA] shadow-xs">
                <span className="text-[#2E8B57] font-bold">Closed & Verified</span>
                <span className="font-extrabold text-[#2E8B57]">{closedActions} ({((closedActions / totalActions) * 100).toFixed(1)}%)</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#EEF3F7] border border-[#D9E2EA] shadow-xs">
                <span className="text-[#B87A00] font-bold">Overdue Remediation</span>
                <span className="font-extrabold text-[#D64545]">{overdueActions}</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#EEF3F7] border border-[#D9E2EA] shadow-xs">
                <span className="text-[#172B3A] font-bold">Open & Pending</span>
                <span className="font-extrabold text-[#172B3A]">{openActions + inProgressActions}</span>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* PROGRESSIVE DISCLOSURE FOR DEEP TECHNICAL ANALYTICS */}
      <div className="border-t border-[#D9E2EA] pt-4">
        <button
          type="button"
          onClick={() => setShowTechnicalAnalytics(!showTechnicalAnalytics)}
          className="w-full flex items-center justify-between p-4 bg-white border border-[#D9E2EA] rounded-2xl text-xs font-bold text-[#172B3A] hover:bg-[#EEF3F7] transition-colors shadow-sm"
        >
          <div className="flex items-center gap-2">
            <span>{showTechnicalAnalytics ? 'Hide Secondary Analytical Charts ▲' : 'Show Secondary Analytical Charts (IOGP Rules, Hotspots, Activities, Locations) ▼'}</span>
          </div>
          <span className="text-[11px] text-[#718394] font-semibold">Click to toggle detailed breakdown charts</span>
        </button>

        {showTechnicalAnalytics && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-in fade-in duration-200">
            {/* CHART 4: IOGP Life-Saving Rule Distribution */}
            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-3 shadow-sm">
              <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
                <h3 className="text-xs font-bold text-[#172B3A] uppercase">
                   IOGP Life-Saving Rules
                </h3>
                <span className="text-[10px] text-[#B87A00] font-bold">9 RULES</span>
              </div>
              {iogpRules.length > 0 ? (
                <div className="space-y-2 text-xs">
                  {iogpRules.slice(0, 4).map((r: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-[#EEF3F7] rounded-lg border border-[#D9E2EA]">
                      <span className="text-[#172B3A] font-semibold truncate">{r.name}</span>
                      <span className="font-bold text-[#B87A00] text-xs">{r.total_reports} matched</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-3 bg-[#EEF3F7] rounded-lg text-xs text-[#718394]">Evaluating IOGP rule matches...</div>
              )}
            </div>

            {/* CHART 5: Recurring Precursors */}
            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-3 shadow-sm">
              <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
                <h3 className="text-xs font-bold text-[#172B3A] uppercase">
                   Recurring Precursor Hotspots
                </h3>
                <span className="text-[10px] text-[#2E8B57] font-bold">EQUIPMENT</span>
              </div>
              {recurringData?.by_equipment && recurringData.by_equipment.length > 0 ? (
                <div className="space-y-2 text-xs">
                  {recurringData.by_equipment.slice(0, 4).map((eq, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-[#EEF3F7] rounded-lg border border-[#D9E2EA]">
                      <span className="text-[#1769AA] font-bold truncate">{eq.identifier}</span>
                      <span className="text-[#526575] text-xs font-semibold">{eq.count} repeats ({eq.sif_precursor_count} SIF)</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-3 bg-[#EEF3F7] rounded-lg text-xs text-[#718394]">Discovering recurring hotspots...</div>
              )}
            </div>

            {/* CHART 6: Barrier Failure Breakdown */}
            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-3 shadow-sm">
              <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
                <h3 className="text-xs font-bold text-[#172B3A] uppercase">
                   Barrier Degradation Categories
                </h3>
                <span className="text-[10px] text-purple-700 font-bold">BARRIER TYPE</span>
              </div>
              <div className="space-y-2 text-xs">
                {Object.entries(sifSummary?.by_ppe_issue_type || {}).map(([bType, bCnt]) => (
                  <div key={bType} className="flex items-center justify-between p-2 bg-[#EEF3F7] rounded-lg border border-[#D9E2EA]">
                    <span className="text-[#172B3A] font-semibold">{bType.replace('_', ' ')}</span>
                    <span className="font-bold text-purple-700">{bCnt}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* CHART 7: High-Risk Activities */}
            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-3 shadow-sm">
              <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
                <h3 className="text-xs font-bold text-[#172B3A] uppercase">
                   Operational Work Types
                </h3>
                <span className="text-[10px] text-[#1769AA] font-bold">ACTIVITIES</span>
              </div>
              {activities.length > 0 ? (
                <div className="space-y-2 text-xs">
                  {activities.slice(0, 4).map((act: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-[#EEF3F7] rounded-lg border border-[#D9E2EA]">
                      <span className="text-[#172B3A] font-semibold truncate">{act.name}</span>
                      <span className="font-bold text-[#1769AA] text-xs">{act.sif_density_percentage}% SIF</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-3 bg-[#EEF3F7] rounded-lg text-xs text-[#718394]">Calculating activity risk...</div>
              )}
            </div>

            {/* CHART 8: High-Risk Physical Locations */}
            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-3 shadow-sm">
              <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
                <h3 className="text-xs font-bold text-[#172B3A] uppercase">
                   Site Physical Locations
                </h3>
                <span className="text-[10px] text-[#526575] font-bold">LOCATIONS</span>
              </div>
              {locations.length > 0 ? (
                <div className="space-y-2 text-xs">
                  {locations.slice(0, 4).map((loc: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-[#EEF3F7] rounded-lg border border-[#D9E2EA]">
                      <span className="text-[#172B3A] font-semibold truncate">{loc.name}</span>
                      <span className="font-bold text-[#526575] text-xs">{loc.total_reports} reports</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-3 bg-[#EEF3F7] rounded-lg text-xs text-[#718394]">Evaluating site locations...</div>
              )}
            </div>

            {/* CHART 9: Technical BDI Banding */}
            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-3 shadow-sm">
              <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
                <h3 className="text-xs font-bold text-[#172B3A] uppercase">
                   BDI Banding Details
                </h3>
                <span className="text-[10px] text-purple-700 font-bold">TECHNICAL INDEX</span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-center text-xs">
                <div className="p-2.5 bg-[#EEF3F7] rounded-xl border border-[#D9E2EA]">
                  <span className="text-[10px] text-[#526575] uppercase block font-bold">Average BDI</span>
                  <span className="text-lg font-black text-purple-700">{bdiSummary?.average_bdi || 0} / 100</span>
                </div>
                <div className="p-2.5 bg-[#EEF3F7] rounded-xl border border-[#D9E2EA]">
                  <span className="text-[10px] text-[#526575] uppercase block font-bold">Severe (&gt;80)</span>
                  <span className="text-lg font-black text-[#D64545]">{bdiSummary?.severe_bdi_count ?? (bdiSummary as any)?.severe_count ?? 0}</span>
                </div>
              </div>
            </div>

          </div>
        )}
      </div>
    </div>
  );
};
