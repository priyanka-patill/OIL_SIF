import React from 'react';
import { SIFSummary } from '../../types/safety';

interface PPEProblemChartProps {
  sifSummary: SIFSummary | null;
}

export const PPEProblemChart: React.FC<PPEProblemChartProps> = ({ sifSummary }) => {
  if (!sifSummary || !sifSummary.by_sif_category) return null;

  const categories = Object.entries(sifSummary.by_sif_category).sort((a, b) => b[1] - a[1]);

  return (
    <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 shadow-sm">
      <div className="mb-4">
        <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-[#1769AA]"></span>
          Observed PPE & SIF Hazard Categories
        </h3>
        <p className="text-[11px] font-sans text-[#526575] font-medium">
          NLP-classified risk vectors derived directly from report descriptions
        </p>
      </div>

      {/* Dataset Context Banner (Rule #15 compliance) */}
      <div className="mb-4 p-2.5 rounded-xl bg-[#EEF3F7] border border-[#D9E2EA] text-[11px] font-mono text-[#526575] flex items-center justify-between">
        <span className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-[#2E8B57]"></span>
          DATASET CONTEXT: <strong className="text-[#172B3A]">PPE_NonCompliance = True</strong> across all 75 observations
        </span>
        <span className="text-[10px] text-[#718394] uppercase font-semibold">Single-Value Dimension</span>
      </div>

      <div className="space-y-3">
        {categories.map(([category, count]) => {
          const total = sifSummary.total_analyzed || 75;
          const percent = ((count / total) * 100).toFixed(1);
          return (
            <div key={category} className="space-y-1">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[#172B3A] font-bold truncate max-w-[80%]">{category}</span>
                <span className="text-[#1769AA] font-extrabold">
                  {count} <span className="text-[#718394] font-semibold text-[10px]">({percent}%)</span>
                </span>
              </div>
              <div className="h-2 w-full bg-[#EEF3F7] rounded-full overflow-hidden border border-[#D9E2EA]">
                <div
                  style={{ width: `${percent}%` }}
                  className="h-full bg-gradient-to-r from-[#123B5D] via-[#1769AA] to-[#168C8C] rounded-full"
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
