import React from 'react';
import { StatusBeacon } from '../common/StatusBeacon';
import { DatasetItem, UserRole } from '../../types/safety';
import { PlusCircle, FileSpreadsheet, UserCheck, Database, HardDrive } from 'lucide-react';

interface TopBarProps {
  title: string;
  subtitle?: string;
  datasets: DatasetItem[];
  selectedDatasetId: string;
  onSelectDataset: (id: string) => void;
  systemStatus: string;
  totalReports: number;
  activeRole: UserRole;
  onRoleChange: (role: UserRole) => void;
  onOpenReportGenerator: () => void;
  onOpenSubmitReport?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  title,
  subtitle,
  datasets,
  selectedDatasetId,
  onSelectDataset,
  systemStatus,
  totalReports,
  activeRole,
  onRoleChange,
  onOpenReportGenerator,
  onOpenSubmitReport,
}) => {
  return (
    <header className="h-[60px] bg-white/95 backdrop-blur border-b border-[#D9E2EA] px-6 flex items-center justify-between sticky top-0 z-30 select-none shrink-0 shadow-sm">
      <div>
        <h1 className="text-base font-bold text-[#172B3A] flex items-center gap-2">
          {title}
        </h1>
        {subtitle && <p className="text-xs text-[#526575] font-medium mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-2.5">
        {/* Submit Safety Report Button */}
        {onOpenSubmitReport && (
          <button
            type="button"
            onClick={onOpenSubmitReport}
            className="px-3.5 py-1.5 rounded-xl bg-[#2E8B57] hover:bg-[#256F46] text-white text-xs font-bold transition-all shadow-sm flex items-center gap-1.5 shrink-0"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            Submit Report
          </button>
        )}

        {/* Export Report Button */}
        <button
          type="button"
          onClick={onOpenReportGenerator}
          className="px-3 py-1.5 rounded-xl bg-white border border-[#D9E2EA] hover:border-[#1769AA] text-[#1769AA] hover:bg-[#EEF3F7] text-xs font-semibold transition-all flex items-center gap-1.5 shrink-0 shadow-sm"
        >
          <FileSpreadsheet className="w-3.5 h-3.5" />
          Export
        </button>

        {/* User Role Selector */}
        <div className="hidden sm:flex items-center gap-1.5 bg-[#EEF3F7] border border-[#D9E2EA] rounded-xl px-3 py-1.5 text-xs">
          <span className="text-[#526575] font-semibold">Role:</span>
          <select
            value={activeRole}
            onChange={(e) => onRoleChange(e.target.value as UserRole)}
            className="bg-transparent text-[#1769AA] font-bold focus:outline-none cursor-pointer text-xs"
          >
            <option value="Safety Officer" className="bg-white text-[#172B3A]">Safety Officer</option>
            <option value="Management" className="bg-white text-[#172B3A]">Management</option>
            <option value="Administrator" className="bg-white text-[#172B3A]">Administrator</option>
          </select>
        </div>

        {/* Dataset Selector */}
        {datasets.length > 0 && (
          <div className="hidden lg:flex items-center gap-1.5 bg-[#EEF3F7] border border-[#D9E2EA] rounded-xl px-3 py-1.5 text-xs">
            <span className="text-[#526575] font-semibold">Dataset:</span>
            <select
              value={selectedDatasetId}
              onChange={(e) => onSelectDataset(e.target.value)}
              className="bg-transparent text-[#1769AA] font-bold focus:outline-none cursor-pointer max-w-[140px] truncate"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id} className="bg-white text-[#172B3A]">
                  {d.dataset_name} ({d.row_count})
                </option>
              ))}
            </select>
          </div>
        )}

        {/* DB Record Count */}
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#EEF3F7] border border-[#D9E2EA] text-xs font-semibold">
          <span className="text-[#526575]">DB:</span>
          <span className="text-[#1769AA] font-bold">{totalReports}</span>
        </div>

        {/* System Health Beacon */}
        <StatusBeacon status={systemStatus} />
      </div>
    </header>
  );
};
