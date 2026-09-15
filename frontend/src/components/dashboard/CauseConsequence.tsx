import React from 'react';

interface CauseConsequenceProps {
  consequences: Record<string, number>;
  causes: Record<string, number>;
  total: number;
  onSelectConsequence?: (consequence: string) => void;
  selectedConsequence?: string;
}

export const CauseConsequence: React.FC<CauseConsequenceProps> = ({
  consequences,
  causes,
  total,
  onSelectConsequence,
  selectedConsequence,
}) => {
  const sortedCons = Object.entries(consequences || {}).sort((a, b) => b[1] - a[1]);
  const sortedCauses = Object.entries(causes || {}).sort((a, b) => b[1] - a[1]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Potential Consequences (What could happen) */}
      {sortedCons.length > 0 && (
        <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-[#D64545]"></span>
                Potential Consequences
              </h3>
              <p className="text-[11px] font-sans text-[#526575] font-medium">
                Severity if barriers failed (click to filter)
              </p>
            </div>
            {selectedConsequence && (
              <button
                onClick={() => onSelectConsequence?.('')}
                className="text-[10px] font-mono px-2 py-0.5 rounded-lg bg-[#EEF3F7] text-[#1769AA] border border-[#D9E2EA] hover:bg-[#D9E2EA] font-bold shadow-xs"
              >
                Clear
              </button>
            )}
          </div>

          <div className="space-y-2">
            {sortedCons.map(([conName, cnt]) => {
              const isSelected = selectedConsequence?.toLowerCase() === conName.toLowerCase();
              const pct = ((cnt / total) * 100).toFixed(1);
              return (
                <div
                  key={conName}
                  onClick={() => onSelectConsequence?.(isSelected ? '' : conName)}
                  className={`p-2.5 rounded-xl border text-xs font-mono transition-all cursor-pointer flex items-center justify-between ${
                    isSelected
                      ? 'bg-[#EEF3F7] border-[#D64545] ring-1 ring-[#D64545] shadow-xs'
                      : 'bg-white border-[#D9E2EA] hover:border-[#D64545] hover:bg-[#EEF3F7]/50'
                  }`}
                >
                  <span className="text-[#172B3A] font-bold truncate">{conName}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[#D64545] font-extrabold">{cnt}</span>
                    <span className="text-[10px] text-[#718394] font-semibold">({pct}%)</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Immediate Causes (Why it happened) */}
      {sortedCauses.length > 0 && (
        <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 shadow-sm">
          <div className="mb-3">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-[#E5A11A]"></span>
              Immediate Root Causes
            </h3>
            <p className="text-[11px] font-sans text-[#526575] font-medium">
              Underlying failure mechanisms and behaviors
            </p>
          </div>

          <div className="space-y-2">
            {sortedCauses.map(([causeName, cnt]) => {
              const pct = ((cnt / total) * 100).toFixed(1);
              return (
                <div
                  key={causeName}
                  className="p-2.5 rounded-xl border border-[#D9E2EA] bg-white text-xs font-mono flex items-center justify-between shadow-xs"
                >
                  <span className="text-[#172B3A] font-bold truncate">{causeName}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[#B87A00] font-extrabold">{cnt}</span>
                    <span className="text-[10px] text-[#718394] font-semibold">({pct}%)</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
