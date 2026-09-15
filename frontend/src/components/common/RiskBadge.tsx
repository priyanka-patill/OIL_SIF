import React from 'react';

interface RiskBadgeProps {
  level: string | null | undefined;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, size = 'md', showIcon = true }) => {
  const norm = (level || 'UNKNOWN').toUpperCase();

  let colorClasses = 'bg-[#EEF3F7] text-[#526575] border-[#D9E2EA] font-semibold';
  let dotColor = 'bg-[#718394]';

  if (norm === 'CRITICAL' || norm === 'HIGH') {
    colorClasses = 'bg-[#D64545]/10 text-[#D64545] border-[#D64545]/30 font-bold shadow-xs';
    dotColor = 'bg-[#D64545] animate-pulse';
  } else if (norm === 'MEDIUM') {
    colorClasses = 'bg-[#E5A11A]/15 text-[#B87A00] border-[#E5A11A]/40 font-bold';
    dotColor = 'bg-[#E5A11A]';
  } else if (norm === 'LOW') {
    colorClasses = 'bg-[#2E8B57]/15 text-[#2E8B57] border-[#2E8B57]/30 font-bold';
    dotColor = 'bg-[#2E8B57]';
  }

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs font-mono font-medium',
    md: 'px-2.5 py-1 text-xs font-mono font-bold tracking-wide',
    lg: 'px-3.5 py-1.5 text-sm font-mono font-bold tracking-wider',
  }[size];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-lg border uppercase tracking-wider ${sizeClasses} ${colorClasses}`}
    >
      {showIcon && <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />}
      {norm}
    </span>
  );
};
