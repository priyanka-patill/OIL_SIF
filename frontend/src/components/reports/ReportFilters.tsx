import React from 'react';
import { MetadataFieldOption } from '../../types/safety';

interface ReportFiltersProps {
  search: string;
  onSearchChange: (s: string) => void;
  filters: Record<string, string>;
  onFilterChange: (key: string, val: string) => void;
  onClearFilters: () => void;
  availableFilterFields: MetadataFieldOption[];
  onOpenSubmitReport?: () => void;
}

export const ReportFilters: React.FC<ReportFiltersProps> = ({
  search,
  onSearchChange,
  filters,
  onFilterChange,
  onClearFilters,
  availableFilterFields,
  onOpenSubmitReport,
}) => {
  const hasActiveFilters = search.trim() !== '' || Object.values(filters).some((v) => v !== '');

  return (
    <div className="bg-white border border-[#D9E2EA] rounded-2xl p-4 space-y-3 flex-1 shadow-sm">
      <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3">
        {/* Search Input */}
        <div className="relative flex-1">
          <input
            type="text"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search report narrative, equipment tags, causes, actions..."
            className="w-full bg-[#EEF3F7] border border-[#D9E2EA] focus:border-[#1769AA] rounded-xl px-3.5 py-2 text-xs font-sans text-[#172B3A] placeholder-[#718394] focus:outline-none focus:ring-1 focus:ring-[#1769AA] font-medium"
          />
          {search && (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-3 top-2.5 text-[#718394] hover:text-[#172B3A] text-xs font-bold"
            >
              ✕
            </button>
          )}
        </div>

        {/* Submit Safety Report & Reset Filters Buttons */}
        <div className="flex items-center gap-2">
          {onOpenSubmitReport && (
            <button
              type="button"
              onClick={onOpenSubmitReport}
              className="px-3.5 py-2 text-xs font-mono font-bold rounded-xl bg-[#2E8B57] hover:bg-[#256F46] text-white shadow-sm transition-all flex items-center gap-1.5 whitespace-nowrap"
            >
              Submit Safety Report
            </button>
          )}

          {hasActiveFilters && (
            <button
              onClick={onClearFilters}
              className="px-3 py-2 text-xs font-mono font-bold rounded-xl bg-[#EEF3F7] hover:bg-[#D9E2EA] text-[#1769AA] border border-[#D9E2EA] transition-colors whitespace-nowrap shadow-xs"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Dynamic Filter Dropdowns (Derived only from available dataset attributes) */}
      <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-[#D9E2EA]">
        <span className="text-[10px] font-mono font-bold uppercase text-[#526575] mr-1">
          Filters:
        </span>
        {availableFilterFields.map((f) => {
          // If field is constant (1 value), omit from dropdowns
          if (f.is_constant) return null;

          const currentVal = filters[f.field_name] || '';
          return (
            <select
              key={f.field_name}
              value={currentVal}
              onChange={(e) => onFilterChange(f.field_name, e.target.value)}
              className={`text-xs font-mono py-1 px-2.5 rounded-lg border focus:outline-none transition-all cursor-pointer ${
                currentVal
                  ? 'bg-[#EEF3F7] border-[#1769AA] text-[#1769AA] font-bold shadow-xs'
                  : 'bg-white border-[#D9E2EA] text-[#172B3A] hover:border-[#1769AA]'
              }`}
            >
              <option value="" className="bg-white text-[#526575]">
                All {f.display_name}s
              </option>
              {f.distinct_values.map((val) => (
                <option key={String(val)} value={String(val)} className="bg-white text-[#172B3A]">
                  {String(val)}
                </option>
              ))}
            </select>
          );
        })}
      </div>
    </div>
  );
};
