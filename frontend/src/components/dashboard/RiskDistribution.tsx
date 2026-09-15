import React from 'react';

interface RiskDistributionProps {
  byRiskLevel: Record<string, number>;
  total: number;
  onSelectRisk?: (risk: string) => void;
  selectedRisk?: string;
}

export const RiskDistribution: React.FC<RiskDistributionProps> = ({
  byRiskLevel,
  total,
  onSelectRisk,
  selectedRisk,
}) => {
  const categories = [
    { key: 'High', label: 'HIGH RISK', color: 'bg-[#D64545]', barColor: 'bg-[#D64545]', textColor: 'text-[#D64545]', borderColor: 'border-[#D64545]/40' },
    { key: 'Medium', label: 'MEDIUM RISK', color: 'bg-[#E5A11A]', barColor: 'bg-[#E5A11A]', textColor: 'text-[#B87A00]', borderColor: 'border-[#E5A11A]/40' },
    { key: 'Low', label: 'LOW RISK', color: 'bg-[#2E8B57]', barColor: 'bg-[#2E8B57]', textColor: 'text-[#2E8B57]', borderColor: 'border-[#2E8B57]/40' },
  ];

  const items = categories.map((cat) => {
    const count = byRiskLevel[cat.key] || byRiskLevel[cat.key.toUpperCase()] || 0;
    const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : '0';
    return { ...cat, count, percentage };
  });

  return (
    <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 shadow-sm flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-[#D64545]"></span>
            Recorded Risk Distribution
          </h3>
          <p className="text-[11px] font-sans text-[#526575] font-medium">
            Interactive breakdown of evaluated severity ratings
          </p>
        </div>
        {selectedRisk && (
          <button
            onClick={() => onSelectRisk?.('')}
            className="text-[10px] font-mono px-2 py-0.5 rounded-lg bg-[#EEF3F7] text-[#1769AA] border border-[#D9E2EA] hover:bg-[#D9E2EA] font-bold shadow-xs"
          >
            Clear Filter ({selectedRisk})
          </button>
        )}
      </div>

      {/* Progress Bar Visualizer */}
      <div className="h-4 w-full bg-[#EEF3F7] rounded-full overflow-hidden flex p-0.5 gap-0.5 mb-5 border border-[#D9E2EA]">
        {items.map((item) => {
          const width = Number(item.percentage);
          if (width <= 0) return null;
          return (
            <div
              key={item.key}
              style={{ width: `${width}%` }}
              title={`${item.label}: ${item.count} (${item.percentage}%)`}
              onClick={() => onSelectRisk?.(item.key)}
              className={`h-full ${item.barColor} transition-all duration-300 cursor-pointer hover:opacity-90 rounded-sm`}
            />
          );
        })}
      </div>

      {/* Interactive Category Cards */}
      <div className="grid grid-cols-3 gap-2.5">
        {items.map((item) => {
          const isSelected = selectedRisk?.toLowerCase() === item.key.toLowerCase();
          return (
            <button
              key={item.key}
              onClick={() => onSelectRisk?.(isSelected ? '' : item.key)}
              className={`p-3 rounded-xl border text-left transition-all ${
                isSelected
                  ? `${item.borderColor} bg-[#EEF3F7] shadow-sm ring-1 ring-[#1769AA]`
                  : 'border-[#D9E2EA] bg-white hover:bg-[#EEF3F7]/60'
              }`}
            >
              <div className="flex items-center gap-1.5 mb-1">
                <span className={`h-2 w-2 rounded-full ${item.color}`} />
                <span className="text-[10px] font-mono font-bold text-[#526575] uppercase truncate">
                  {item.label}
                </span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className={`text-xl font-mono font-black ${item.textColor}`}>
                  {item.count}
                </span>
                <span className="text-[10px] font-mono font-semibold text-[#718394]">
                  {item.percentage}%
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
