import React from 'react';

interface RefineryUnitChartProps {
  byUnit: Record<string, number>;
  total: number;
  onSelectUnit?: (unit: string) => void;
  selectedUnit?: string;
}

export const RefineryUnitChart: React.FC<RefineryUnitChartProps> = ({
  byUnit,
  total,
  onSelectUnit,
  selectedUnit,
}) => {
  if (!byUnit || Object.keys(byUnit).length === 0) return null;

  const sortedUnits = Object.entries(byUnit)
    .sort((a, b) => b[1] - a[1]);

  const maxVal = Math.max(...sortedUnits.map(([_, v]) => v), 1);

  return (
    <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-[#1769AA]"></span>
            Process Unit Distribution
          </h3>
          <p className="text-[11px] font-sans text-[#526575] font-medium">
            Near-miss density across operating refinery plants (click to filter)
          </p>
        </div>
        {selectedUnit && (
          <button
            onClick={() => onSelectUnit?.('')}
            className="text-[10px] font-mono px-2 py-0.5 rounded-lg bg-[#EEF3F7] text-[#1769AA] border border-[#D9E2EA] hover:bg-[#D9E2EA] font-bold shadow-xs"
          >
            Clear ({selectedUnit})
          </button>
        )}
      </div>

      <div className="space-y-2.5 max-h-64 overflow-y-auto custom-scrollbar pr-1">
        {sortedUnits.map(([unitName, count]) => {
          const isSelected = selectedUnit?.toLowerCase() === unitName.toLowerCase();
          const percent = ((count / total) * 100).toFixed(1);
          const barWidth = Math.max(5, (count / maxVal) * 100);

          return (
            <div
              key={unitName}
              onClick={() => onSelectUnit?.(isSelected ? '' : unitName)}
              className={`p-2.5 rounded-xl border transition-all cursor-pointer ${
                isSelected
                  ? 'bg-[#EEF3F7] border-[#1769AA] ring-1 ring-[#1769AA] shadow-xs'
                  : 'bg-white border-[#D9E2EA] hover:border-[#1769AA] hover:bg-[#EEF3F7]/50'
              }`}
            >
              <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                <span className="font-bold text-[#172B3A] truncate">{unitName}</span>
                <span className="text-[#526575] font-semibold">
                  <strong className="text-[#1769AA]">{count}</strong> ({percent}%)
                </span>
              </div>
              <div className="h-2 w-full bg-[#EEF3F7] rounded-full overflow-hidden border border-[#D9E2EA]">
                <div
                  style={{ width: `${barWidth}%` }}
                  className={`h-full rounded-full transition-all ${
                    count >= 10
                      ? 'bg-gradient-to-r from-[#D64545] to-[#E67E22]'
                      : 'bg-gradient-to-r from-[#123B5D] to-[#1769AA]'
                  }`}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
