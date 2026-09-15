import React from 'react';
import { SafetyReport } from '../../types/safety';
import { RiskBadge } from '../common/RiskBadge';
import { SIFBadge } from '../common/SIFBadge';
import { ColumnDef } from './ColumnSelector';

interface ReportTableProps {
  reports: SafetyReport[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  onPageChange: (newPage: number) => void;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  onSortChange: (columnKey: string) => void;
  onSelectReport: (report: SafetyReport) => void;
  columns: ColumnDef[];
}

export const ReportTable: React.FC<ReportTableProps> = ({
  reports,
  total,
  page,
  pageSize,
  totalPages,
  onPageChange,
  sortBy,
  sortOrder,
  onSortChange,
  onSelectReport,
  columns,
}) => {
  const visibleColumns = columns.filter((c) => c.visible);

  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: '2-digit' });
    } catch {
      return dateStr;
    }
  };

  const getStatusBadge = (status?: string | null) => {
    const s = (status || 'UNKNOWN').toUpperCase();
    if (s === 'OVERDUE') {
      return <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-[#D64545]/15 text-[#D64545] border border-[#D64545]/30">OVERDUE</span>;
    }
    if (s === 'OPEN') {
      return <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-[#E5A11A]/15 text-[#B87A00] border border-[#E5A11A]/30">OPEN</span>;
    }
    if (s === 'IN PROGRESS') {
      return <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-[#1769AA]/15 text-[#1769AA] border border-[#1769AA]/30">IN PROGRESS</span>;
    }
    if (s === 'CLOSED') {
      return <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-[#2E8B57]/15 text-[#2E8B57] border border-[#2E8B57]/30">CLOSED</span>;
    }
    return <span className="px-2 py-0.5 rounded-md text-[10px] font-mono text-[#526575] border border-[#D9E2EA] bg-[#EEF3F7]">{s}</span>;
  };

  return (
    <div className="bg-white border border-[#D9E2EA] rounded-2xl overflow-hidden flex flex-col shadow-sm">
      {/* Table container */}
      <div className="overflow-x-auto custom-scrollbar">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-[#EEF3F7] border-b border-[#D9E2EA] text-[10px] font-mono font-bold uppercase tracking-wider text-[#526575] select-none">
              {visibleColumns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => onSortChange(col.key)}
                  className="px-4 py-3 cursor-pointer hover:text-[#1769AA] transition-colors whitespace-nowrap"
                >
                  <div className="flex items-center gap-1.5">
                    <span>{col.label}</span>
                    {sortBy === col.key && (
                      <span className="text-[#1769AA] font-mono">
                        {sortOrder === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
              <th className="px-4 py-3 text-right">ACTION</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#D9E2EA] font-sans">
            {reports.map((report) => (
              <tr
                key={report.id}
                onClick={() => onSelectReport(report)}
                className="hover:bg-[#EEF3F7]/50 transition-colors cursor-pointer group"
              >
                {visibleColumns.map((col) => {
                  if (col.key === 'original_id') {
                    return (
                      <td key={col.key} className="px-4 py-3 font-mono font-bold text-[#1769AA] whitespace-nowrap">
                        {report.original_id || '—'}
                      </td>
                    );
                  }
                  if (col.key === 'report_date') {
                    return (
                      <td key={col.key} className="px-4 py-3 font-mono text-[#526575] font-medium whitespace-nowrap">
                        {formatDate(report.report_date)}
                      </td>
                    );
                  }
                  if (col.key === 'refinery_unit') {
                    return (
                      <td key={col.key} className="px-4 py-3 font-mono text-[#172B3A] whitespace-nowrap font-bold">
                        {report.refinery_unit || '—'}
                      </td>
                    );
                  }
                  if (col.key === 'equipment') {
                    return (
                      <td key={col.key} className="px-4 py-3 font-mono text-[#526575] whitespace-nowrap font-semibold">
                        {report.equipment || '—'}
                      </td>
                    );
                  }
                  if (col.key === 'work_type') {
                    return (
                      <td key={col.key} className="px-4 py-3 text-[#172B3A] whitespace-nowrap font-medium">
                        {report.work_type || '—'}
                      </td>
                    );
                  }
                  if (col.key === 'department') {
                    return (
                      <td key={col.key} className="px-4 py-3 text-[#172B3A] whitespace-nowrap font-medium">
                        {report.department || '—'}
                      </td>
                    );
                  }
                  if (col.key === 'description') {
                    return (
                      <td key={col.key} className="px-4 py-3 text-[#172B3A] max-w-xs truncate font-medium" title={report.description || ''}>
                        {report.description || '—'}
                      </td>
                    );
                  }
                  if (col.key === 'risk_level') {
                    return (
                      <td key={col.key} className="px-4 py-3 whitespace-nowrap">
                        <RiskBadge level={report.risk_level} size="sm" />
                      </td>
                    );
                  }
                  if (col.key === 'potential_consequence') {
                    return (
                      <td key={col.key} className="px-4 py-3 text-[#526575] whitespace-nowrap font-medium">
                        {report.potential_consequence || '—'}
                      </td>
                    );
                  }
                  if (col.key === 'immediate_cause') {
                    return (
                      <td key={col.key} className="px-4 py-3 text-[#526575] whitespace-nowrap font-medium">
                        {report.immediate_cause || '—'}
                      </td>
                    );
                  }
                  if (col.key === 'corrective_action') {
                    return (
                      <td key={col.key} className="px-4 py-3 text-[#172B3A] max-w-xs truncate font-medium" title={report.corrective_action || ''}>
                        {report.corrective_action || '—'}
                      </td>
                    );
                  }
                  if (col.key === 'action_status') {
                    return (
                      <td key={col.key} className="px-4 py-3 whitespace-nowrap">
                        {getStatusBadge(report.action_status)}
                      </td>
                    );
                  }
                  return (
                    <td key={col.key} className="px-4 py-3 text-[#526575] whitespace-nowrap">
                      {String((report as any)[col.key] ?? '—')}
                    </td>
                  );
                })}
                <td className="px-4 py-3 text-right whitespace-nowrap">
                  <span className="text-[#1769AA] group-hover:text-[#123B5D] font-mono text-xs font-bold">
                    Inspect 
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="px-4 py-3 bg-[#EEF3F7] border-t border-[#D9E2EA] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs font-mono text-[#526575]">
        <div>
          Showing <span className="text-[#172B3A] font-extrabold">{reports.length > 0 ? (page - 1) * pageSize + 1 : 0}</span> to{' '}
          <span className="text-[#172B3A] font-extrabold">{Math.min(page * pageSize, total)}</span> of{' '}
          <span className="text-[#1769AA] font-extrabold">{total}</span> records
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="px-3 py-1 rounded-lg bg-white border border-[#D9E2EA] disabled:opacity-40 hover:bg-[#EEF3F7] text-[#172B3A] font-bold transition-colors shadow-xs"
          >
            ◀ Prev
          </button>
          <span>
            Page <strong className="text-[#172B3A] font-extrabold">{page}</strong> of <strong className="text-[#172B3A] font-extrabold">{totalPages || 1}</strong>
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="px-3 py-1 rounded-lg bg-white border border-[#D9E2EA] disabled:opacity-40 hover:bg-[#EEF3F7] text-[#172B3A] font-bold transition-colors shadow-xs"
          >
            Next ▶
          </button>
        </div>
      </div>
    </div>
  );
};
