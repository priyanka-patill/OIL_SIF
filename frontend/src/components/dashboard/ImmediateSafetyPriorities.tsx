import React from 'react';
import { SafetyReport } from '../../types/safety';
import { normalizeRiskLevel } from '../../utils/riskClassification';
import { RiskBadge } from '../common/RiskBadge';
import { AlertTriangle, Eye, ArrowRight, CheckCircle2, Clock } from 'lucide-react';

interface ImmediateSafetyPrioritiesProps {
  reports: SafetyReport[];
  onViewReport: (reportId: string) => void;
  onViewAllReports: () => void;
}

export const ImmediateSafetyPriorities: React.FC<ImmediateSafetyPrioritiesProps> = ({
  reports,
  onViewReport,
  onViewAllReports,
}) => {
  // Priority sorting: HIGH > MEDIUM > LOW
  // Secondary sorting: Overdue/Open action status & SIF precursor status
  const sortedReports = [...reports].sort((a, b) => {
    const riskA = normalizeRiskLevel(a.risk_level, a.raw_data);
    const riskB = normalizeRiskLevel(b.risk_level, b.raw_data);
    const scoreMap: Record<string, number> = { HIGH: 3, MEDIUM: 2, LOW: 1 };

    const diff = (scoreMap[riskB] || 0) - (scoreMap[riskA] || 0);
    if (diff !== 0) return diff;

    const getStatusWeight = (r: SafetyReport) => {
      let weight = 0;
      const status = (r.action_status || '').toUpperCase();
      if (status === 'OVERDUE') weight += 10;
      if (status === 'OPEN' || status === 'IN PROGRESS') weight += 5;
      if (r.sif_precursor || r.high_potential) weight += 3;
      return weight;
    };

    return getStatusWeight(b) - getStatusWeight(a);
  });

  const top3 = sortedReports.slice(0, 3);

  return (
    <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-4 shadow-sm my-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#D9E2EA]">
        <div>
          <h2 className="text-sm font-bold text-[#172B3A] uppercase tracking-wider flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-[#D64545]" />
            IMMEDIATE SAFETY PRIORITIES
          </h2>
          <p className="text-xs text-[#526575] font-medium mt-0.5">
            Critical observations and actions requiring prompt attention.
          </p>
        </div>
        {reports.length > 0 && (
          <button
            type="button"
            onClick={onViewAllReports}
            className="text-xs font-bold text-[#1769AA] hover:text-[#123B5D] flex items-center gap-1 hover:underline shrink-0"
          >
            View All Safety Reports <ArrowRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {top3.length === 0 ? (
        <div className="p-6 text-center text-xs font-semibold text-[#718394] bg-[#F4F7FA] border border-dashed border-[#D9E2EA] rounded-xl flex items-center justify-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-[#2E8B57]" />
          No immediate safety priorities identified.
        </div>
      ) : (
        <div className="space-y-3">
          {top3.map((rep) => {
            const isOverdue = (rep.action_status || '').toUpperCase() === 'OVERDUE';

            return (
              <div
                key={rep.id}
                className="p-4 bg-[#F4F7FA] border border-[#D9E2EA] hover:border-[#1769AA]/40 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all shadow-xs"
              >
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <RiskBadge level={rep.risk_level} size="sm" />
                    {rep.original_id && (
                      <span className="text-[10px] font-mono font-bold text-[#526575] bg-white px-2 py-0.5 rounded border border-[#D9E2EA]">
                        ID: {rep.original_id}
                      </span>
                    )}
                    {isOverdue && (
                      <span className="text-[10px] font-bold text-[#D64545] bg-[#D64545]/15 border border-[#D64545]/30 px-2 py-0.5 rounded flex items-center gap-1">
                        <Clock className="w-3 h-3" /> OVERDUE SLA
                      </span>
                    )}
                  </div>

                  <p className="text-xs font-bold text-[#172B3A] line-clamp-1">
                    {rep.description || rep.hazard || 'Safety observation reported in operational area.'}
                  </p>

                  <div className="flex items-center gap-3 text-[11px] text-[#526575] font-medium flex-wrap">
                    <span>
                      <strong className="text-[#172B3A]">Unit:</strong> {rep.refinery_unit || 'General Facility'} {rep.equipment ? `— ${rep.equipment}` : ''}
                    </span>
                    <span>•</span>
                    <span>
                      <strong className="text-[#172B3A]">Action:</strong> {rep.corrective_action || rep.action_status || 'Containment & verification pending'}
                    </span>
                  </div>
                </div>

                <div className="shrink-0 flex items-center">
                  <button
                    type="button"
                    onClick={() => onViewReport(rep.id)}
                    className="px-3.5 py-1.5 rounded-xl bg-white border border-[#D9E2EA] hover:border-[#1769AA] text-[#1769AA] hover:bg-[#EEF3F7] text-xs font-bold transition-all shadow-xs flex items-center gap-1.5"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    View Details
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
