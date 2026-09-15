import React, { useState, useEffect } from 'react';
import { BDISummaryResponse, BDITrendPoint } from '../../types/safety';
import { api } from '../../services/api';
import { InfoTooltip } from '../common/InfoTooltip';

interface BDICardProps {
  datasetId?: string;
  onSelectUnit?: (unit: string) => void;
}

export const BDICard: React.FC<BDICardProps> = ({ datasetId, onSelectUnit }) => {
  const [bdiSummary, setBdiSummary] = useState<BDISummaryResponse | null>(null);
  const [trends, setTrends] = useState<BDITrendPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showDetails, setShowDetails] = useState<boolean>(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getBDISummary(datasetId).catch(() => null),
      api.getBDITrends(datasetId).catch(() => ({ trends: [] }))
    ])
      .then(([summaryRes, trendsRes]) => {
        if (summaryRes) setBdiSummary(summaryRes);
        if (trendsRes && trendsRes.trends) setTrends(trendsRes.trends);
      })
      .finally(() => setLoading(false));
  }, [datasetId]);

  if (loading) {
    return (
      <div className="bg-white border border-[#D9E2EA] rounded-2xl p-6 animate-pulse space-y-4 shadow-sm">
        <div className="h-5 w-40 bg-[#EEF3F7] rounded-lg"></div>
        <div className="h-16 w-32 bg-[#EEF3F7] rounded-lg"></div>
        <div className="h-4 w-full bg-[#EEF3F7] rounded-lg"></div>
      </div>
    );
  }

  if (!bdiSummary || bdiSummary.average_bdi === undefined) {
    return (
      <div className="bg-white border border-[#D9E2EA] rounded-2xl p-6 text-center text-[#526575] text-xs font-medium shadow-sm">
        Safety barrier condition data currently updating.
      </div>
    );
  }

  const score = bdiSummary.average_bdi;
  let scoreClass = 'MINIMAL DEGRADATION';
  let statusExplanation = 'Safety defense barriers are intact and operating properly.';
  let badgeColor = 'bg-[#2E8B57]/15 text-[#2E8B57] border-[#2E8B57]/30 font-bold';
  let barColor = 'from-[#2E8B57] to-[#168C8C]';

  if (score >= 80.0) {
    scoreClass = 'SEVERE';
    statusExplanation = 'Several identified safety barriers require immediate attention.';
    badgeColor = 'bg-[#D64545]/15 text-[#D64545] border-[#D64545]/30 font-bold';
    barColor = 'from-[#D64545] to-[#E67E22]';
  } else if (score >= 60.1) {
    scoreClass = 'SIGNIFICANT';
    statusExplanation = 'Multiple safety barriers are showing signs of degradation.';
    badgeColor = 'bg-[#E67E22]/15 text-[#E67E22] border-[#E67E22]/30 font-bold';
    barColor = 'from-[#E67E22] to-[#E5A11A]';
  } else if (score >= 40.1) {
    scoreClass = 'MODERATE';
    statusExplanation = 'Some safety barriers require maintenance and monitoring.';
    badgeColor = 'bg-[#E5A11A]/15 text-[#B87A00] border-[#E5A11A]/30 font-bold';
    barColor = 'from-[#E5A11A] to-[#2589C7]';
  } else if (score >= 20.1) {
    scoreClass = 'LOW';
    statusExplanation = 'Safety barriers are generally healthy with minor observations.';
    badgeColor = 'bg-[#2589C7]/15 text-[#2589C7] border-[#2589C7]/30 font-bold';
    barColor = 'from-[#1769AA] to-[#2589C7]';
  }

  return (
    <div className="bg-white border border-[#D9E2EA] rounded-2xl p-6 shadow-sm flex flex-col justify-between space-y-4">
      <div>
        {/* Header */}
        <div className="flex items-start justify-between pb-3 border-b border-[#D9E2EA]">
          <div>
            <div className="flex items-center gap-1.5">
              <h3 className="text-sm font-bold text-[#172B3A]">
                Safety Barrier Health
              </h3>
              <InfoTooltip
                title="Safety Barrier Health"
                text="Measures the condition of physical, operational, and procedural safety barriers designed to prevent incidents."
              />
            </div>
            <p className="text-xs text-[#526575] mt-0.5 font-medium">
              Overall Defense Condition Score
            </p>
          </div>
          <span className={`px-2.5 py-1 text-xs font-bold rounded-lg border uppercase tracking-wider ${badgeColor}`}>
            {scoreClass}
          </span>
        </div>

        {/* Score & Gauge */}
        <div className="mt-4 flex items-baseline gap-2">
          <span className="text-5xl font-black tracking-tight text-[#172B3A] tabular-nums">
            {score.toFixed(1)}
          </span>
          <span className="text-sm text-[#718394] font-bold">/ 100</span>
        </div>

        {/* Visual Progress Bar */}
        <div className="w-full bg-[#EEF3F7] rounded-full h-3 mt-3 mb-4 overflow-hidden border border-[#D9E2EA]">
          <div
            className={`h-full rounded-full bg-gradient-to-r ${barColor} transition-all duration-500`}
            style={{ width: `${Math.min(100, Math.max(5, score))}%` }}
          />
        </div>

        {/* User-Friendly Meaning */}
        <div className="bg-[#EEF3F7] p-3.5 rounded-xl border border-[#D9E2EA] space-y-1">
          <span className="text-[11px] font-bold text-[#526575] block uppercase tracking-wider">
            WHAT DOES THIS MEAN?
          </span>
          <p className="text-xs text-[#172B3A] font-semibold leading-relaxed">
            "{statusExplanation}"
          </p>
        </div>
      </div>

      {/* Progressive Disclosure Toggle */}
      <div className="border-t border-[#D9E2EA] pt-3">
        <button
          type="button"
          onClick={() => setShowDetails(!showDetails)}
          className="w-full flex items-center justify-between text-xs font-bold text-[#1769AA] hover:text-[#123B5D] transition-colors py-1"
        >
          <span>{showDetails ? 'Hide BDI Technical Details ▲' : 'View BDI Technical Details ▼'}</span>
          <span className="text-[11px] text-[#718394] font-medium">BDI calculation, degraded barriers & trends</span>
        </button>

        {showDetails && (
          <div className="mt-3 p-4 bg-[#EEF3F7] rounded-xl border border-[#D9E2EA] space-y-4 text-xs animate-in fade-in duration-200">
            {/* Dominant Degraded Barriers */}
            <div>
              <span className="text-[#172B3A] font-bold block mb-2">
                Primary Degraded Barriers:
              </span>
              <div className="flex flex-wrap gap-2">
                {bdiSummary.dominant_degraded_barriers && bdiSummary.dominant_degraded_barriers.length > 0 ? (
                  bdiSummary.dominant_degraded_barriers.slice(0, 3).map((b, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 bg-white border border-[#D9E2EA] text-[#D64545] text-xs font-bold rounded-lg shadow-xs"
                    >
                       {b.barrier_name} ({b.count} reports)
                    </span>
                  ))
                ) : (
                  <span className="text-[#718394] text-xs font-medium">No degraded barriers recorded.</span>
                )}
              </div>
            </div>

            {/* Top Vulnerable Units */}
            {bdiSummary.top_vulnerable_units && bdiSummary.top_vulnerable_units.length > 0 && (
              <div>
                <span className="text-[#172B3A] font-bold block mb-2">
                  Highest Risk Process Units:
                </span>
                <div className="flex flex-wrap gap-2">
                  {bdiSummary.top_vulnerable_units.slice(0, 3).map((u, idx) => (
                    <button
                      type="button"
                      key={idx}
                      onClick={() => onSelectUnit && onSelectUnit(u.unit)}
                      className="px-2.5 py-1 bg-white border border-[#D9E2EA] hover:border-[#1769AA] text-[#1769AA] text-xs font-bold rounded-lg transition-colors shadow-xs"
                    >
                       {u.unit} (Score: {u.average_bdi.toFixed(1)})
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Trend & Technical Notes */}
            <div className="pt-2 border-t border-[#D9E2EA] space-y-1.5 text-[11px] text-[#526575]">
              <div className="flex items-center justify-between">
                <span className="font-medium">Technical Metric Name:</span>
                <span className="font-mono text-[#1769AA] font-bold">Barrier Degradation Index (BDI)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="font-medium">Historical Inspection Trajectory:</span>
                <span className="text-[#172B3A] font-bold">{trends.length >= 3 ? `${trends.length} periods evaluated` : 'Sufficient historical sample'}</span>
              </div>
              <p className="text-[10px] text-[#718394] pt-1 italic font-medium">
                * Internal prototype analytical index evaluating defense layer erosion across safety reports.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
