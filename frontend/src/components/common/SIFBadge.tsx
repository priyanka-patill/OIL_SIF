import React from 'react';

interface SIFBadgeProps {
  status: 'YES' | 'NO' | 'UNCERTAIN' | string | null | undefined;
  size?: 'sm' | 'md' | 'lg';
}

export const SIFBadge: React.FC<SIFBadgeProps> = ({ status, size = 'md' }) => {
  const norm = (status || 'NO').toUpperCase();

  let colorClasses = 'bg-[#EEF3F7] text-[#526575] border-[#D9E2EA]';
  let label = 'SIF: NO';

  if (norm === 'YES' || norm === 'TRUE') {
    colorClasses = 'bg-[#D64545]/15 text-[#D64545] border-[#D64545]/40 font-bold shadow-xs';
    label = 'SIF PRECURSOR';
  } else if (norm === 'UNCERTAIN') {
    colorClasses = 'bg-[#E5A11A]/15 text-[#B87A00] border-[#E5A11A]/40 font-bold';
    label = 'SIF UNCERTAIN';
  } else {
    colorClasses = 'bg-[#EEF3F7] text-[#526575] border-[#D9E2EA] font-semibold';
    label = 'NON-SIF';
  }

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs font-mono font-medium',
    md: 'px-2.5 py-1 text-xs font-mono font-bold tracking-wider',
    lg: 'px-3.5 py-1.5 text-sm font-mono font-bold tracking-wider',
  }[size];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-lg border uppercase ${sizeClasses} ${colorClasses}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          norm === 'YES' ? 'bg-[#D64545] animate-ping' : norm === 'UNCERTAIN' ? 'bg-[#E5A11A]' : 'bg-[#718394]'
        }`}
      />
      {label}
    </span>
  );
};
