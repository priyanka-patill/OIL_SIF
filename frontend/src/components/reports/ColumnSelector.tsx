import React, { useState } from 'react';

export interface ColumnDef {
  key: string;
  label: string;
  visible: boolean;
  required?: boolean;
}

interface ColumnSelectorProps {
  columns: ColumnDef[];
  onToggleColumn: (key: string) => void;
}

export const ColumnSelector: React.FC<ColumnSelectorProps> = ({ columns, onToggleColumn }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative inline-block text-left">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-3.5 py-2 rounded-xl bg-white border border-[#D9E2EA] text-xs font-mono font-bold text-[#1769AA] hover:bg-[#EEF3F7] flex items-center gap-1.5 transition-colors shadow-xs"
      >
        <span> Columns ({columns.filter((c) => c.visible).length})</span>
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-20" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-white border border-[#D9E2EA] shadow-xl z-30 p-2 text-xs font-mono space-y-1 text-[#172B3A]">
            <div className="px-2 py-1 text-[10px] font-bold text-[#526575] uppercase border-b border-[#D9E2EA]">
              Customize Table Columns
            </div>
            <div className="max-h-56 overflow-y-auto custom-scrollbar pt-1">
              {columns.map((col) => (
                <label
                  key={col.key}
                  className={`flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-[#EEF3F7] cursor-pointer ${
                    col.required ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={col.visible}
                    disabled={col.required}
                    onChange={() => onToggleColumn(col.key)}
                    className="rounded border-[#D9E2EA] text-[#1769AA] focus:ring-0 bg-white"
                  />
                  <span className="text-[#172B3A] font-medium truncate">{col.label}</span>
                </label>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
