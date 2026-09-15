import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { SIFSummary, RecurringIssuesResponse, ActionStats } from '../../types/safety';
import { RiskBadge } from '../common/RiskBadge';

interface ManagementViewProps {
  datasetId?: string;
  onOpenReport?: (reportId: string) => void;
}

export const ManagementView: React.FC<ManagementViewProps> = ({ datasetId, onOpenReport }) => {
  const [sifSummary, setSifSummary] = useState<SIFSummary | null>(null);
  const [densityData, setDensityData] = useState<any | null>(null);
  const [multiFactorData, setMultiFactorData] = useState<any | null>(null);
  const [recurringData, setRecurringData] = useState<RecurringIssuesResponse | null>(null);
  const [actionStats, setActionStats] = useState<ActionStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([
      api.getSIFSummary(datasetId),
      api.getSIFDensity(datasetId),
      api.getMultiFactorAnalytics(datasetId),
      api.getRecurringIssues(datasetId),
      api.getActionStats(datasetId)
    ])
      .then(([sifRes, denRes, mfRes, recRes, actRes]) => {
        if (sifRes.status === 'fulfilled') setSifSummary(sifRes.value);
        if (denRes.status === 'fulfilled') setDensityData(denRes.value);
        if (mfRes.status === 'fulfilled') setMultiFactorData(mfRes.value);
        if (recRes.status === 'fulfilled') setRecurringData(recRes.value);
        if (actRes.status === 'fulfilled') setActionStats(actRes.value);
      })
      .finally(() => setLoading(false));
  }, [datasetId]);

  if (loading) {
    return (
      <div className="p-8 text-center text-xs font-mono text-[#1769AA] animate-pulse bg-white rounded-xl border border-[#D9E2EA] shadow-sm">
        Aggregating Executive Safety Intelligence & Multi-Barrier Analytics...
      </div>
    );
  }

  const unitRankings = densityData?.dimension_rankings?.['Refinery Unit'] || [];
  const activityRankings = densityData?.dimension_rankings?.['Activity / Work Type'] || [];
  const ruleRankings = densityData?.dimension_rankings?.['IOGP Life-Saving Rule'] || [];
  const unavailableDims = densityData?.unavailable_dimensions || [];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-[#D9E2EA] rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-mono font-bold text-[#172B3A] uppercase tracking-wider">
                Executive Safety Intelligence & Governance View
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200 font-bold">
                PLANT MANAGEMENT
              </span>
            </div>
            <p className="text-xs font-sans text-[#526575] mt-1">
              Executive answers to high-consequence precursor density, barrier erosion, recurring equipment hotspots, and overdue SLA remediation.
            </p>
          </div>

          <div className="flex items-center gap-4 bg-[#F4F7FA] p-3 rounded-lg border border-[#D9E2EA] text-xs font-mono">
            <div>
              <span className="text-[10px] text-[#718394] block uppercase font-bold">Overall Precursor Density</span>
              <span className="text-xl font-bold text-rose-700">
                {densityData?.sif_precursor_density_percentage || 0}%
              </span>
            </div>
            <div className="h-8 w-px bg-[#D9E2EA]" />
            <div>
              <span className="text-[10px] text-[#718394] block uppercase font-bold">Overdue Actions</span>
              <span className="text-xl font-bold text-[#E5A11A]">
                {actionStats?.overdue_count || 0}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 7 Key Executive Strategic Questions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Q1: Highest SIF Density Units */}
        <div className="bg-white border border-[#D9E2EA] rounded-xl p-4 space-y-3 shadow-sm">
          <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
            <h3 className="text-xs font-mono font-bold text-[#1769AA] uppercase flex items-center gap-2">
              1. Which units have the highest SIF precursor density?
            </h3>
            <span className="text-[10px] font-mono text-[#718394]">BY REFINERY UNIT</span>
          </div>

          {unitRankings.length > 0 ? (
            <div className="space-y-2">
              {unitRankings.slice(0, 4).map((u: any, idx: number) => (
                <div key={idx} className="p-2.5 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA] flex items-center justify-between text-xs font-mono">
                  <div>
                    <span className="font-bold text-[#172B3A] block">{u.name}</span>
                    <span className="text-[10px] text-[#526575]">{u.sif_precursor_count} SIF precursors / {u.total_reports} total reports</span>
                  </div>
                  <div className="text-right">
                    <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 font-bold text-xs">
                      {u.sif_density_percentage}% Density
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-3 bg-[#F4F7FA] rounded-lg text-xs font-mono text-[#718394]">
              {unavailableDims.includes('Refinery Unit') ? 'Not available in this dataset.' : 'Calculating process unit precursor density...'}
            </div>
          )}
        </div>

        {/* Q2: Most Frequent Life-Saving Rules */}
        <div className="bg-white border border-[#D9E2EA] rounded-xl p-4 space-y-3 shadow-sm">
          <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
            <h3 className="text-xs font-mono font-bold text-[#E5A11A] uppercase flex items-center gap-2">
              2. Which Life-Saving Rules appear most frequently?
            </h3>
            <span className="text-[10px] font-mono text-[#718394]">IOGP 9 RULES</span>
          </div>

          {ruleRankings.length > 0 ? (
            <div className="space-y-2">
              {ruleRankings.slice(0, 4).map((r: any, idx: number) => (
                <div key={idx} className="p-2.5 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA] flex items-center justify-between text-xs font-mono">
                  <div>
                    <span className="font-bold text-[#172B3A] block">{r.name}</span>
                    <span className="text-[10px] text-[#526575]">{r.total_reports} matched observations ({r.high_risk_count} High Risk)</span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 font-bold text-xs">
                    {r.sif_density_percentage}% SIF Rate
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-3 bg-[#F4F7FA] rounded-lg text-xs font-mono text-[#718394]">
              Evaluating IOGP Life-Saving Rules distribution...
            </div>
          )}
        </div>

        {/* Q3: High SIF Activities */}
        <div className="bg-white border border-[#D9E2EA] rounded-xl p-4 space-y-3 shadow-sm">
          <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
            <h3 className="text-xs font-mono font-bold text-purple-700 uppercase flex items-center gap-2">
              3. Which activities produce the most SIF potential?
            </h3>
            <span className="text-[10px] font-mono text-[#718394]">WORK TYPES</span>
          </div>

          {activityRankings.length > 0 ? (
            <div className="space-y-2">
              {activityRankings.slice(0, 4).map((act: any, idx: number) => (
                <div key={idx} className="p-2.5 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA] flex items-center justify-between text-xs font-mono">
                  <div>
                    <span className="font-bold text-[#172B3A] block">{act.name}</span>
                    <span className="text-[10px] text-[#526575]">{act.sif_precursor_count} SIF events in {act.total_reports} tasks</span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-purple-50 text-purple-800 border border-purple-200 font-bold text-xs">
                    {act.sif_density_percentage}% SIF
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-3 bg-[#F4F7FA] rounded-lg text-xs font-mono text-[#718394]">
              {unavailableDims.includes('Activity / Work Type') ? 'Not available in this dataset.' : 'Ranking high-exposure operational tasks...'}
            </div>
          )}
        </div>

        {/* Q4: Recurring Issues & Hotspot Equipment */}
        <div className="bg-white border border-[#D9E2EA] rounded-xl p-4 space-y-3 shadow-sm">
          <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
            <h3 className="text-xs font-mono font-bold text-[#2E8B57] uppercase flex items-center gap-2">
              4. Which issues are recurring across equipment?
            </h3>
            <span className="text-[10px] font-mono text-[#718394]">EQUIPMENT HOTSPOTS</span>
          </div>

          {recurringData?.by_equipment && recurringData.by_equipment.length > 0 ? (
            <div className="space-y-2">
              {recurringData.by_equipment.slice(0, 4).map((eq, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA] flex items-center justify-between text-xs font-mono">
                  <div>
                    <span className="font-bold text-[#1769AA] block">{eq.identifier}</span>
                    <span className="text-[10px] text-[#526575]">{eq.count} repeated observations • {eq.sif_precursor_count} SIF precursors</span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 font-bold text-xs">
                    RECURRING
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-3 bg-[#F4F7FA] rounded-lg text-xs font-mono text-[#718394]">
              {unavailableDims.includes('Equipment') ? 'Not available in this dataset.' : 'Discovering recurring equipment clusters...'}
            </div>
          )}
        </div>
      </div>

      {/* Compound Multi-Factor Failure Clusters */}
      <div className="bg-white border border-[#D9E2EA] rounded-xl p-4 space-y-3 shadow-sm">
        <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
          <h3 className="text-xs font-mono font-bold text-rose-700 uppercase flex items-center gap-2">
            Where are multiple risk factors occurring together? (Multi-Factor Swiss Cheese)
          </h3>
          <span className="text-[10px] font-mono text-[#718394]">COMPOUND BARRIER COLLAPSE</span>
        </div>

        {multiFactorData?.combinations && multiFactorData.combinations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {multiFactorData.combinations.slice(0, 3).map((comb: any, idx: number) => (
              <div key={idx} className="p-3 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA] space-y-2 text-xs font-mono">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-rose-700 text-xs truncate">{comb.combination_key}</span>
                  <span className="px-1.5 py-0.5 rounded bg-rose-50 text-rose-800 text-[10px] font-bold border border-rose-200">
                    {comb.danger_level}
                  </span>
                </div>
                <div className="text-[11px] text-[#526575] font-sans">
                  {comb.report_count} report(s) combining {comb.factor_count} simultaneous control failures.
                </div>
                <div className="text-[10px] text-[#718394] border-t border-[#D9E2EA] pt-1">
                  Top cause: <span className="text-[#172B3A] font-semibold">{comb.top_causes[0] || 'Multiple failures'}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-3 bg-[#F4F7FA] rounded-lg text-xs font-mono text-[#718394]">
            Analyzing multi-factor barrier failure alignments...
          </div>
        )}
      </div>
    </div>
  );
};
