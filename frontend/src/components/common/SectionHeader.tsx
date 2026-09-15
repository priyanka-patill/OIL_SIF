import React from 'react';

interface SectionHeaderProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  description,
  action,
  className = '',
}) => {
  return (
    <div className={`flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 pb-4 border-b border-[#D9E2EA] ${className}`}>
      <div>
        <h2 className="text-base font-bold text-[#172B3A] tracking-tight">
          {title}
        </h2>
        {description && (
          <p className="text-sm text-[#526575] mt-0.5 leading-relaxed font-medium">
            {description}
          </p>
        )}
      </div>
      {action && (
        <div className="flex items-center gap-2 shrink-0">
          {action}
        </div>
      )}
    </div>
  );
};
