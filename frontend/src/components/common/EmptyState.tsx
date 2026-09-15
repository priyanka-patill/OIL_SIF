import React from 'react';
import { FileSearch } from 'lucide-react';

interface EmptyStateProps {
  type?: 'no_filter_matches' | 'field_not_found' | 'no_data';
  title?: string;
  message?: string;
  onClearFilters?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  type = 'no_filter_matches',
  title,
  message,
  onClearFilters,
}) => {
  if (type === 'field_not_found') {
    return null; // As per Rule #22: If field does not exist, hide component cleanly.
  }

  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-white border border-dashed border-[#D9E2EA] rounded-2xl my-4 shadow-sm">
      <div className="h-10 w-10 rounded-full bg-[#EEF3F7] border border-[#D9E2EA] flex items-center justify-center text-[#526575] mb-3">
        <FileSearch className="w-5 h-5 text-[#526575]" />
      </div>
      <h3 className="text-sm font-bold text-[#172B3A]">
        {title || (type === 'no_filter_matches' ? 'No Matching Safety Records' : 'No Data Available')}
      </h3>
      <p className="text-xs text-[#526575] mt-1 max-w-sm font-sans font-medium">
        {message || 'No records match the selected filters. Adjust your filter parameters or query.'}
      </p>
      {onClearFilters && (
        <button
          onClick={onClearFilters}
          className="mt-4 px-3.5 py-1.5 text-xs font-mono font-bold rounded-xl bg-[#EEF3F7] hover:bg-[#D9E2EA] text-[#1769AA] border border-[#D9E2EA] transition-colors shadow-xs"
        >
          Reset Active Filters
        </button>
      )}
    </div>
  );
};
