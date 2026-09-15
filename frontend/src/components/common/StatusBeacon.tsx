import React from 'react';

interface StatusBeaconProps {
  status: 'healthy' | 'degraded' | 'offline' | string;
  label?: string;
}

export const StatusBeacon: React.FC<StatusBeaconProps> = ({ status, label }) => {
  const s = status.toLowerCase();
  const isHealthy = s === 'healthy' || s === 'connected' || s === 'system operational' || s === 'online';
  const isWarning = s === 'degraded' || s === 'warning';
  const isError = s === 'offline' || s === 'error' || s === 'failed';

  let dotColor = 'bg-[#2589C7]';
  let pingColor = 'bg-[#2589C7]';
  if (isHealthy) {
    dotColor = 'bg-[#2E8B57]';
    pingColor = 'bg-[#2E8B57]';
  } else if (isWarning) {
    dotColor = 'bg-[#E5A11A]';
    pingColor = 'bg-[#E5A11A]';
  } else if (isError) {
    dotColor = 'bg-[#D64545]';
    pingColor = 'bg-[#D64545]';
  }

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#EEF3F7] border border-[#D9E2EA] text-xs font-mono shadow-xs">
      <span className="relative flex h-2 w-2">
        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${pingColor} opacity-75`}></span>
        <span className={`relative inline-flex rounded-full h-2 w-2 ${dotColor}`}></span>
      </span>
      <span className="text-[#172B3A] font-bold uppercase">{label || (isHealthy ? 'SYSTEM OPERATIONAL' : isWarning ? 'SYSTEM DEGRADED' : isError ? 'SYSTEM OFFLINE' : status)}</span>
    </div>
  );
};
