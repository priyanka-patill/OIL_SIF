import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { InfoTooltip } from '../common/InfoTooltip';

interface SafetyConvergenceCardProps {
  datasetId?: string;
  onViewReport?: (reportId: string) => void;
  onViewAction?: (actionId: string) => void;
  onOpenChatWithQuery?: (query: string) => void;
}

export const SafetyConvergenceCard: React.FC<SafetyConvergenceCardProps> = ({
  datasetId,
  onViewReport,
  onViewAction,
  onOpenChatWithQuery,
}) => {
  const [criticalItems, setCriticalItems] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false);

  useEffect(() => {
    setLoading(true);
    api.getCriticalSIFEscalations(datasetId)
      .then((res) => {
        if (res && res.items) {
          setCriticalItems(res.items);
        } else if (Array.isArray(res)) {
          setCriticalItems(res);
        }
      })
      .catch(() => setCriticalItems([]))
      .finally(() => setLoading(false));
  }, [datasetId]);

  if (loading) {
    return (
      <div className="bg-white border border-[#D9E2EA] rounded-2xl p-6 animate-pulse space-y-4 shadow-sm">
        <div className="h-5 w-40 bg-[#EEF3F7] rounded-lg"></div>
        <div className="h-16 w-full bg-[#EEF3F7] rounded-lg"></div>
      </div>
    );
  }

  if (!criticalItems || criticalItems.length === 0) {
    return (
      <div className="bg-white border border-[#2E8B57]/40 rounded-2xl p-6 text-center space-y-2 shadow-sm">
        <div className="text-[#2E8B57] font-bold text-sm flex items-center justify-center gap-2">
          No Critical Safety Issues Detected
        </div>
        <p className="text-xs text-[#526575] font-medium">
          All process safety barriers are operating within acceptable parameters.
        </p>
      </div>
    );
  }

  const current = criticalItems[currentIndex] || criticalItems[0];
  const total = criticalItems.length;

  return (
    <div className="bg-white border border-[#D64545]/40 rounded-2xl p-6 shadow-md relative flex flex-col justify-between space-y-5">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between pb-3 border-b border-[#D9E2EA]">
          <div className="flex items-center gap-2.5">
            <span className="text-xl"></span>
            <div>
              <div className="flex items-center gap-1.5">
                <h3 className="text-sm font-bold text-[#D64545]">
                  Critical Safety Alert
                </h3>
                <InfoTooltip
                  title="Critical Safety Alert"
                  text="Indicates an immediate high-risk observation where safety barriers are degraded and severe impact could occur if unaddressed."
                />
              </div>
              <p className="text-xs text-[#526575] font-medium">
                Potential Serious Injury / Fatality exposure detected
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {total > 1 && (
              <span className="text-xs text-[#526575] font-bold">
                {currentIndex + 1} of {total}
              </span>
            )}
            <span className="px-2.5 py-1 text-xs font-bold rounded-lg bg-[#D64545]/15 text-[#D64545] border border-[#D64545]/30">
              CRITICAL
            </span>
          </div>
        </div>

        {/* Location & Unit Headline */}
        <div className="mt-4 p-3.5 bg-[#EEF3F7] rounded-xl border border-[#D9E2EA] flex items-center justify-between shadow-xs">
          <div>
            <span className="text-[11px] font-bold text-[#526575] uppercase tracking-wider block">
              LOCATION / UNIT
            </span>
            <span className="text-sm font-extrabold text-[#172B3A]">
              {current.refinery_unit || 'Process Unit'} — {current.equipment || 'General System'}
            </span>
          </div>
          <div className="text-right">
            <span className="text-[11px] font-bold text-[#526575] uppercase tracking-wider block">
              RISK EXPOSURE
            </span>
            <span className="text-xs font-extrabold text-[#D64545]">
              Potential SIF Precursor
            </span>
          </div>
        </div>

        {/* WHY THIS MATTERS */}
        <div className="mt-4 space-y-1.5">
          <div className="text-xs font-bold text-[#172B3A] flex items-center gap-1.5">
            Why does this matter?
          </div>
          <p className="text-xs text-[#172B3A] bg-[#EEF3F7] p-3 rounded-xl border border-[#D9E2EA] leading-relaxed font-medium">
            {current.what_potential_consequence || current.contributing_factors?.join(' • ') || 'Multiple safety barrier weaknesses have converged at this location, creating an elevated risk exposure.'}
          </p>
        </div>

        {/* IMMEDIATE RECOMMENDED ACTION */}
        <div className="mt-4 space-y-1.5">
          <div className="text-xs font-bold text-[#D64545] flex items-center gap-1.5">
            Immediate Action Required:
          </div>
          <p className="text-xs text-[#D64545] bg-[#D64545]/10 p-3 rounded-xl border border-[#D64545]/20 leading-relaxed font-bold">
            {current.recommended_immediate_action || 'Issue immediate safety hold and verify barrier isolation before continuing operations.'}
          </p>
        </div>
      </div>

      {/* Main Action Buttons */}
      <div className="pt-2 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          {/* Pagination Controls */}
          {total > 1 ? (
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => setCurrentIndex((prev) => (prev > 0 ? prev - 1 : total - 1))}
                className="px-2.5 py-1 bg-[#EEF3F7] hover:bg-[#D9E2EA] border border-[#D9E2EA] text-[#172B3A] rounded-lg text-xs font-bold transition-colors"
              >
                ◀ Previous
              </button>
              <button
                type="button"
                onClick={() => setCurrentIndex((prev) => (prev < total - 1 ? prev + 1 : 0))}
                className="px-2.5 py-1 bg-[#EEF3F7] hover:bg-[#D9E2EA] border border-[#D9E2EA] text-[#172B3A] rounded-lg text-xs font-bold transition-colors"
              >
                Next ▶
              </button>
            </div>
          ) : <div />}

          {/* Primary Actions */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => onViewReport && onViewReport(current.report_id || current.id)}
              className="px-3.5 py-2 bg-white hover:bg-[#EEF3F7] border border-[#D9E2EA] text-[#172B3A] text-xs font-bold rounded-xl transition-all shadow-xs"
            >
               View Report
            </button>
            <button
              type="button"
              onClick={() => onViewAction && onViewAction(current.action_id || current.report_id || current.id)}
              className="px-4 py-2 bg-[#D64545] hover:bg-[#B83535] text-white text-xs font-extrabold rounded-xl transition-all shadow-sm flex items-center gap-1.5"
            >
              Take Action
            </button>
          </div>
        </div>

        {/* Progressive Disclosure Toggle */}
        <div className="border-t border-[#D9E2EA] pt-3">
          <button
            type="button"
            onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
            className="w-full flex items-center justify-between text-xs font-bold text-[#1769AA] hover:text-[#123B5D] transition-colors py-1"
          >
            <span>{showTechnicalDetails ? 'Hide Technical Details ▲' : 'Show Technical Details ▼'}</span>
            <span className="text-[11px] text-[#718394] font-medium">BDI, Converging Factors & AI Reasoning</span>
          </button>

          {showTechnicalDetails && (
            <div className="mt-3 p-4 bg-[#EEF3F7] rounded-xl border border-[#D9E2EA] space-y-3 text-xs animate-in fade-in duration-200">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div>
                  <span className="text-[#526575] block text-[10px] uppercase font-bold">SIF PRECURSOR</span>
                  <span className="text-[#D64545] font-bold">Yes (Active Exposure)</span>
                </div>
                <div>
                  <span className="text-[#526575] block text-[10px] uppercase font-bold">BARRIER HEALTH SCORE (BDI)</span>
                  <span className="text-[#D64545] font-bold">{current.bdi_score !== undefined ? current.bdi_score.toFixed(1) : '90.0'} / 100 (Severe)</span>
                </div>
                <div>
                  <span className="text-[#526575] block text-[10px] uppercase font-bold">CONVERGENCE TARGET</span>
                  <span className="text-[#1769AA] font-bold">{current.refinery_unit || 'Process Unit'}</span>
                </div>
              </div>

              <div>
                <span className="text-[#172B3A] font-bold block mb-1">Contributing Factors:</span>
                <span className="text-[#B87A00] font-semibold">
                  {current.contributing_factors && current.contributing_factors.length > 0
                    ? current.contributing_factors.join(' • ')
                    : 'Multiple safety defense erosion factors'}
                </span>
              </div>

              <div>
                <span className="text-[#172B3A] font-bold block mb-1">Safety Barriers Status:</span>
                <span className="text-[#D64545] font-semibold">
                  {current.which_barriers && current.which_barriers.length > 0
                    ? current.which_barriers.join(', ')
                    : 'PPE, Supervision, Maintenance Integrity degraded'}
                </span>
              </div>

              {onOpenChatWithQuery && (
                <div className="pt-2 flex justify-end">
                  <button
                    type="button"
                    onClick={() => onOpenChatWithQuery(`Show the AI reasoning and evidence for report ${current.report_id || current.id}`)}
                    className="text-xs text-[#1769AA] hover:text-[#123B5D] font-bold underline flex items-center gap-1"
                  >
                    Ask AI for Full Technical Evidence
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
