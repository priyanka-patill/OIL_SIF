import React from 'react';
import { ReportCounts } from '../../types/safety';

interface AnalyticsViewProps {
  counts: ReportCounts | null;
  onSelectFilter?: (field: string, val: string) => void;
}

export const AnalyticsView: React.FC<AnalyticsViewProps> = ({ counts, onSelectFilter }) => {
  if (!counts) return null;

  const depts = Object.entries(counts.by_department || {}).sort((a, b) => b[1] - a[1]);
  const workTypes = Object.entries(counts.by_work_type || {}).sort((a, b) => b[1] - a[1]);
  const total = counts.total_reports || 75;

  return (
    <div className="space-y-6">
      <div className="bg-white border border-[#D9E2EA] rounded-2xl p-6 shadow-sm">
        <h2 className="text-base font-mono font-bold text-[#172B3A] uppercase tracking-wider mb-1 flex items-center gap-2">
          Deep Safety Analytics & Distribution Cross-Tabs
        </h2>
        <p className="text-xs font-sans text-[#526575]">
          Multidimensional operational safety analytics derived directly from factual report dimensions.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Department Distribution */}
        {depts.length > 0 && (
          <div className="bg-white border border-[#D9E2EA] rounded-xl p-5 space-y-4 shadow-sm">
            <div>
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-[#1769AA]" />
                Department & Contractor Distribution
              </h3>
              <p className="text-[11px] font-sans text-[#526575]">
                Near-miss observation breakdown by functional team
              </p>
            </div>

            <div className="space-y-3">
              {depts.map(([dept, cnt]) => {
                const pct = ((cnt / total) * 100).toFixed(1);
                return (
                  <div
                    key={dept}
                    onClick={() => onSelectFilter?.('department', dept)}
                    className="p-3 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA] hover:border-[#1769AA]/50 transition-all cursor-pointer space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-[#172B3A] font-bold">{dept}</span>
                      <span className="text-[#1769AA] font-bold">
                        {cnt} <span className="text-[#718394] text-[10px]">({pct}%)</span>
                      </span>
                    </div>
                    <div className="h-2 w-full bg-[#EEF3F7] rounded-full overflow-hidden">
                      <div
                        style={{ width: `${pct}%` }}
                        className="h-full bg-[#1769AA] rounded-full"
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Work Type Distribution */}
        {workTypes.length > 0 && (
          <div className="bg-white border border-[#D9E2EA] rounded-xl p-5 space-y-4 shadow-sm">
            <div>
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-[#E5A11A]" />
                Work Activity Type Distribution
              </h3>
              <p className="text-[11px] font-sans text-[#526575]">
                Risk density across routine operations, maintenance, and critical tasks
              </p>
            </div>

            <div className="space-y-3">
              {workTypes.map(([wt, cnt]) => {
                const pct = ((cnt / total) * 100).toFixed(1);
                return (
                  <div
                    key={wt}
                    onClick={() => onSelectFilter?.('work_type', wt)}
                    className="p-3 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA] hover:border-[#E5A11A]/50 transition-all cursor-pointer space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-[#172B3A] font-bold">{wt}</span>
                      <span className="text-[#E5A11A] font-bold">
                        {cnt} <span className="text-[#718394] text-[10px]">({pct}%)</span>
                      </span>
                    </div>
                    <div className="h-2 w-full bg-[#EEF3F7] rounded-full overflow-hidden">
                      <div
                        style={{ width: `${pct}%` }}
                        className="h-full bg-[#E5A11A] rounded-full"
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
