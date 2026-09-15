import React, { useState, useEffect } from 'react';
import { SIFSummary, ReportAnalysis } from '../../types/safety';
import { api } from '../../services/api';
import { RiskBadge } from '../common/RiskBadge';
import { SIFBadge } from '../common/SIFBadge';

interface SIFViewProps {
  sifSummary: SIFSummary | null;
  datasetId?: string;
  onOpenReport: (reportId: string) => void;
}

export const SIFView: React.FC<SIFViewProps> = ({ sifSummary, datasetId, onOpenReport }) => {
  const [highRiskList, setHighRiskList] = useState<ReportAnalysis[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getHighRiskReports(datasetId, 1, 20)
      .then((res) => setHighRiskList(res.items || []))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [datasetId]);

  if (!sifSummary) return null;

  return (
    <div className="space-y-6 text-[#172B3A]">
      {/* SIF Executive Overview Header */}
      <div className="bg-gradient-to-r from-rose-50 via-white to-blue-50 border border-rose-200 rounded-2xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="h-2.5 w-2.5 rounded-full bg-rose-600 animate-ping" />
            <h2 className="text-base font-mono font-bold text-rose-900 uppercase tracking-wider">
              Serious Injury & Fatality (SIF) Precursor Intelligence
            </h2>
          </div>
          <p className="text-xs font-sans text-[#526575] max-w-2xl">
            Real-time detection of high-energy hazards and compromised personal protective barriers across active refinery process operations.
          </p>
        </div>

        <div className="flex items-center gap-4 text-center">
          <div className="bg-white px-4 py-2.5 rounded-xl border border-[#D9E2EA] shadow-sm">
            <span className="text-[10px] font-mono text-[#718394] uppercase block font-semibold">SIF PRECURSOR RATE</span>
            <span className="text-2xl font-mono font-extrabold text-rose-600">
              {sifSummary.sif_precursor_rate_percentage}%
            </span>
          </div>
          <div className="bg-white px-4 py-2.5 rounded-xl border border-[#D9E2EA] shadow-sm">
            <span className="text-[10px] font-mono text-[#718394] uppercase block font-semibold">SIF PRECURSORS DETECTED</span>
            <span className="text-2xl font-mono font-extrabold text-rose-800">
              {sifSummary.sif_precursors_detected} <span className="text-xs text-[#718394]">/ {sifSummary.total_analyzed}</span>
            </span>
          </div>
        </div>
      </div>

      {/* SIF Category Breakdown & AI Risk Upgrades */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-white border border-[#D9E2EA] rounded-xl p-5 shadow-sm">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] mb-3 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-[#1769AA]" />
            SIF Precursor Categories
          </h3>
          <div className="space-y-2.5">
            {Object.entries(sifSummary.by_sif_category || {}).map(([cat, cnt]) => {
              const pct = ((cnt / sifSummary.total_analyzed) * 100).toFixed(1);
              return (
                <div key={cat} className="p-2.5 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA] text-xs font-mono flex items-center justify-between">
                  <span className="text-[#172B3A] font-medium truncate max-w-[70%]">{cat}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-rose-600 font-bold">{cnt}</span>
                    <span className="text-[#718394] text-[10px]">({pct}%)</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-white border border-[#D9E2EA] rounded-xl p-5 flex flex-col justify-between shadow-sm">
          <div>
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#1769AA] mb-2 flex items-center gap-2">
              AI Risk Upgrades vs Recorded Field Ratings
            </h3>
            <p className="text-xs font-sans text-[#526575] mb-4">
              AI evaluated <strong className="text-[#1769AA]">{sifSummary.risk_level_upgrades} observations</strong> at higher risk than initially recorded due to high-energy release vectors or overdue barriers.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs font-mono">
            <div className="p-3 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA]">
              <span className="text-[#718394] text-[10px] block mb-1 font-semibold">RECORDED HIGH RISK</span>
              <span className="text-xl font-bold text-rose-600">
                {sifSummary.by_recorded_risk_level?.['High'] || sifSummary.by_recorded_risk_level?.['HIGH'] || 0}
              </span>
            </div>
            <div className="p-3 rounded-lg bg-blue-50 border border-blue-200">
              <span className="text-[#1769AA] text-[10px] block mb-1 font-semibold">AI CALCULATED HIGH RISK</span>
              <span className="text-xl font-bold text-[#1769AA]">
                {sifSummary.by_ai_risk_level?.['HIGH'] || sifSummary.by_ai_risk_level?.['High'] || 0}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Prioritized SIF Precursor Feed */}
      <div className="bg-white border border-[#D9E2EA] rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-rose-600" />
              Prioritized SIF Precursor Records
            </h3>
            <p className="text-[11px] font-sans text-[#526575]">
              Observations with verified Serious Injury & Fatality precursor mechanisms
            </p>
          </div>
          <span className="text-xs font-mono text-[#718394]">
            {highRiskList.length} High-Risk Records
          </span>
        </div>

        {loading ? (
          <div className="p-8 text-center font-mono text-xs text-[#718394] animate-pulse">
            Loading SIF Precursors...
          </div>
        ) : highRiskList.length === 0 ? (
          <div className="p-6 text-center text-xs font-mono text-[#718394]">
            No SIF precursor records identified under current filters.
          </div>
        ) : (
          <div className="space-y-2.5">
            {highRiskList.map((a) => {
              const rep = a.report;
              return (
                <div
                  key={a.id}
                  onClick={() => onOpenReport(a.report_id)}
                  className="p-3.5 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA] hover:border-[#1769AA] hover:bg-white transition-all cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-3 group shadow-sm"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-[#1769AA] text-xs">
                        {rep?.original_id || a.report_id}
                      </span>
                      <span className="text-xs font-mono text-[#526575]">
                        • {rep?.refinery_unit} • {rep?.equipment}
                      </span>
                      <SIFBadge status={a.sif_precursor} size="sm" />
                      <RiskBadge level={a.ai_risk_level} size="sm" />
                    </div>
                    <p className="text-xs font-sans text-[#172B3A] max-w-3xl truncate">
                      "{a.observed_problem}"
                    </p>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-[11px] font-mono text-[#526575]">
                      Consequence: <strong className="text-[#172B3A]">{a.potential_consequence || 'Severe'}</strong>
                    </span>
                    <span className="text-[#1769AA] group-hover:underline font-mono text-xs font-bold">
                      Inspect 
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
