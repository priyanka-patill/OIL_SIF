import React, { useState, useMemo } from 'react';
import { SafetyReport } from '../../types/safety';

interface ReportTrendProps {
  reports: SafetyReport[];
  hasDateField: boolean;
}

export const ReportTrend: React.FC<ReportTrendProps> = ({ reports, hasDateField }) => {
  if (!hasDateField || !reports || reports.length === 0) {
    return null; // Omit if date field doesn't exist
  }

  const [timeRange, setTimeRange] = useState<'30d' | '6m' | '1y' | 'all'>('all');

  // Aggregate reports by month/year or week
  const trendData = useMemo(() => {
    const buckets: Record<string, number> = {};

    reports.forEach((rep) => {
      if (!rep.report_date) return;
      const d = new Date(rep.report_date);
      if (isNaN(d.getTime())) return;

      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
      buckets[key] = (buckets[key] || 0) + 1;
    });

    const sortedKeys = Object.keys(buckets).sort();
    return sortedKeys.map((k) => ({
      period: k,
      count: buckets[k],
    }));
  }, [reports]);

  if (trendData.length === 0) return null;

  const maxCount = Math.max(...trendData.map((d) => d.count), 1);

  return (
    <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-[#1769AA]"></span>
            Observation Trend Over Time
          </h3>
          <p className="text-[11px] font-sans text-[#526575] font-medium">
            Historical incident & near-miss logging timeline
          </p>
        </div>

        {/* Time range buttons */}
        <div className="flex items-center gap-1 bg-[#EEF3F7] border border-[#D9E2EA] rounded-xl p-1 text-[10px] font-mono shadow-inner">
          {(['30d', '6m', '1y', 'all'] as const).map((r) => (
            <button
              key={r}
              onClick={() => setTimeRange(r)}
              className={`px-2.5 py-1 rounded-lg uppercase font-bold transition-all ${
                timeRange === r
                  ? 'bg-white text-[#1769AA] border border-[#D9E2EA] shadow-xs'
                  : 'text-[#526575] hover:text-[#172B3A]'
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* Bar Chart Visualization */}
      <div className="h-44 flex items-end gap-2 pt-4 px-2 overflow-x-auto custom-scrollbar">
        {trendData.map((d) => {
          const heightPercent = Math.max(8, (d.count / maxCount) * 100);
          return (
            <div
              key={d.period}
              className="flex-1 min-w-[36px] flex flex-col items-center gap-1.5 group cursor-pointer"
            >
              <div className="text-[10px] font-mono font-bold text-[#1769AA] opacity-0 group-hover:opacity-100 transition-opacity">
                {d.count}
              </div>
              <div className="w-full bg-[#EEF3F7] rounded-t-md overflow-hidden h-32 flex items-end border border-[#D9E2EA]">
                <div
                  style={{ height: `${heightPercent}%` }}
                  className="w-full bg-gradient-to-t from-[#123B5D] to-[#1769AA] group-hover:from-[#1769AA] group-hover:to-[#2589C7] rounded-t transition-all"
                />
              </div>
              <span className="text-[9px] font-mono font-semibold text-[#526575] truncate max-w-[48px]">
                {d.period}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
