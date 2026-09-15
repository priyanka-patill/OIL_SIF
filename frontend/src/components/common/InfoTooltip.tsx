import React, { useState } from 'react';
import { Info } from 'lucide-react';

interface InfoTooltipProps {
  text: string;
  title?: string;
  className?: string;
}

export const InfoTooltip: React.FC<InfoTooltipProps> = ({ text, title, className = '' }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={`relative inline-flex items-center ${className}`}>
      <button
        type="button"
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        onClick={() => setIsOpen(!isOpen)}
        className="w-4 h-4 rounded-full bg-[#EEF3F7] hover:bg-[#D9E2EA] text-[#526575] hover:text-[#1769AA] text-[10px] font-bold inline-flex items-center justify-center border border-[#D9E2EA] transition-colors focus:outline-none ml-1.5 shrink-0 shadow-xs"
        aria-label="More information"
      >
        <Info className="w-2.5 h-2.5" />
      </button>

      {isOpen && (
        <div className="absolute z-50 bottom-full mb-2 left-1/2 -translate-x-1/2 w-64 p-3 bg-[#123B5D] text-white text-xs rounded-xl shadow-xl border border-[#184D7A] pointer-events-none animate-in fade-in duration-150">
          {title && (
            <div className="font-bold text-[#2589C7] mb-1 text-[11px] uppercase tracking-wider">
              {title}
            </div>
          )}
          <p className="leading-relaxed text-blue-100 text-[11px] font-normal">{text}</p>
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px border-4 border-transparent border-t-[#123B5D]" />
        </div>
      )}
    </div>
  );
};
