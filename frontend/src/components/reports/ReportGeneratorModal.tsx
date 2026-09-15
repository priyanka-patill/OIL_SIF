import React, { useState, useEffect } from 'react';
import { Modal } from '../common/Modal';
import { api } from '../../services/api';
import { DatasetItem, MetadataFieldOption, ExportPreviewData, ExportFilterParams } from '../../types/safety';

interface ReportGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  datasets: DatasetItem[];
  selectedDatasetId: string;
  availableFilterFields: MetadataFieldOption[];
}

export const ReportGeneratorModal: React.FC<ReportGeneratorModalProps> = ({
  isOpen,
  onClose,
  datasets,
  selectedDatasetId,
  availableFilterFields = [],
}) => {
  const [format, setFormat] = useState<'PDF' | 'EXCEL' | 'CSV'>('PDF');
  const [datasetId, setDatasetId] = useState<string>(selectedDatasetId || '');
  const [riskLevel, setRiskLevel] = useState<string>('');
  const [department, setDepartment] = useState<string>('');
  const [refineryUnit, setRefineryUnit] = useState<string>('');
  const [reportType, setReportType] = useState<string>('');
  const [actionStatus, setActionStatus] = useState<string>('');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');

  const [preview, setPreview] = useState<ExportPreviewData | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (selectedDatasetId) {
      setDatasetId(selectedDatasetId);
    }
  }, [selectedDatasetId]);

  // Extract distinct values supported by dataset
  const unitField = availableFilterFields.find((f) => f.field_name === 'refinery_unit');
  const deptField = availableFilterFields.find((f) => f.field_name === 'department');
  const riskField = availableFilterFields.find((f) => f.field_name === 'risk_level');
  const statusField = availableFilterFields.find((f) => f.field_name === 'action_status');
  const typeField = availableFilterFields.find((f) => f.field_name === 'report_type');
  const hasDateField =
    availableFilterFields.length === 0 ||
    availableFilterFields.some(
      (f) => f.field_name === 'report_date' || f.data_type === 'DATETIME' || f.field_name === 'incident_date'
    );

  // Fetch live export preview
  useEffect(() => {
    if (!isOpen) return;

    setLoadingPreview(true);
    const params: ExportFilterParams = {
      dataset_id: datasetId || undefined,
      risk_level: riskLevel || undefined,
      department: department || undefined,
      refinery_unit: refineryUnit || undefined,
      report_type: reportType || undefined,
      action_status: actionStatus || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    };

    api.getExportPreview(params)
      .then(setPreview)
      .catch(console.error)
      .finally(() => setLoadingPreview(false));
  }, [isOpen, datasetId, riskLevel, department, refineryUnit, reportType, actionStatus, dateFrom, dateTo]);

  const handleDownload = () => {
    setDownloading(true);
    const params: ExportFilterParams = {
      dataset_id: datasetId || undefined,
      risk_level: riskLevel || undefined,
      department: department || undefined,
      refinery_unit: refineryUnit || undefined,
      report_type: reportType || undefined,
      action_status: actionStatus || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    };

    let downloadUrl = '';
    if (format === 'PDF') downloadUrl = api.getExportPdfUrl(params);
    else if (format === 'EXCEL') downloadUrl = api.getExportExcelUrl(params);
    else downloadUrl = api.getExportCsvUrl(params);

    // Trigger download
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', '');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setTimeout(() => {
      setDownloading(false);
      onClose();
    }, 1000);
  };

  const handleClearFilters = () => {
    setRiskLevel('');
    setDepartment('');
    setRefineryUnit('');
    setReportType('');
    setActionStatus('');
    setDateFrom('');
    setDateTo('');
  };

  if (!isOpen) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Generate Safety Intelligence Report"
      subtitle="Export executive safety reports with dynamic schema-aware filtering"
      size="2xl"
    >
      <div className="space-y-6 text-[#172B3A]">
        {/* 1. Format Selector */}
        <div>
          <label className="text-xs font-mono font-bold text-[#526575] uppercase tracking-wider block mb-2">
            Select Export Document Format
          </label>
          <div className="grid grid-cols-3 gap-3">
            <button
              type="button"
              onClick={() => setFormat('PDF')}
              className={`p-4 rounded-xl border text-left transition-all ${format === 'PDF'
                  ? 'bg-blue-50 border-[#1769AA] text-[#1769AA] ring-1 ring-[#1769AA] shadow-sm'
                  : 'bg-[#EEF3F7] border-[#D9E2EA] text-[#526575] hover:border-[#1769AA] hover:bg-white'
                }`}
            >
              <div className="text-2xl mb-1"></div>
              <div className="font-mono text-xs font-bold text-[#172B3A]">Executive PDF Report</div>
              <div className="text-[11px] text-[#718394] mt-1">
                Executive summary, SIF precursor breakdown, and AI recommendations.
              </div>
            </button>

            <button
              type="button"
              onClick={() => setFormat('EXCEL')}
              className={`p-4 rounded-xl border text-left transition-all ${format === 'EXCEL'
                  ? 'bg-emerald-50 border-[#2E8B57] text-[#2E8B57] ring-1 ring-[#2E8B57] shadow-sm'
                  : 'bg-[#EEF3F7] border-[#D9E2EA] text-[#526575] hover:border-[#2E8B57] hover:bg-white'
                }`}
            >
              <div className="text-2xl mb-1"></div>
              <div className="font-mono text-xs font-bold text-[#172B3A]">Excel Workbook (.xlsx)</div>
              <div className="text-[11px] text-[#718394] mt-1">
                Multi-sheet workbook with KPIs, full report registry, and action items.
              </div>
            </button>

            <button
              type="button"
              onClick={() => setFormat('CSV')}
              className={`p-4 rounded-xl border text-left transition-all ${format === 'CSV'
                  ? 'bg-blue-50 border-[#1769AA] text-[#1769AA] ring-1 ring-[#1769AA] shadow-sm'
                  : 'bg-[#EEF3F7] border-[#D9E2EA] text-[#526575] hover:border-[#1769AA] hover:bg-white'
                }`}
            >
              <div className="text-2xl mb-1"></div>
              <div className="font-mono text-xs font-bold text-[#172B3A]">Raw CSV Export</div>
              <div className="text-[11px] text-[#718394] mt-1">
                Clean RFC-4180 CSV for spreadsheet and BI tool ingestion.
              </div>
            </button>
          </div>
        </div>

        {/* 2. Dynamic Schema-Aware Filters */}
        <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-xl p-4 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-[#1769AA] flex items-center gap-2">
              Filter Selection (Active Dataset Supported)
            </h4>
            <button
              type="button"
              onClick={handleClearFilters}
              className="text-[11px] font-mono text-[#526575] hover:text-[#1769AA] underline"
            >
              Clear Filters
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs font-mono">
            {/* Dataset selection */}
            <div>
              <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Target Dataset</label>
              <select
                value={datasetId}
                onChange={(e) => setDatasetId(e.target.value)}
                className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
              >
                <option value="">All Active Datasets</option>
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.dataset_name} ({d.row_count} rows)
                  </option>
                ))}
              </select>
            </div>

            {/* Risk Level */}
            {(!riskField || !riskField.is_constant) && (
              <div>
                <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Risk Level</label>
                <select
                  value={riskLevel}
                  onChange={(e) => setRiskLevel(e.target.value)}
                  className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                >
                  <option value="">All Risk Levels</option>
                  {riskField && riskField.distinct_values && riskField.distinct_values.length > 0 ? (
                    riskField.distinct_values.map((r: any) => (
                      <option key={String(r)} value={String(r)}>
                        {String(r)} Risk
                      </option>
                    ))
                  ) : (
                    <>
                      <option value="High">High Risk</option>
                      <option value="Medium">Medium Risk</option>
                      <option value="Low">Low Risk</option>
                    </>
                  )}
                </select>
              </div>
            )}

            {/* Refinery Unit */}
            {unitField && !unitField.is_constant && (
              <div>
                <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Refinery Unit</label>
                <select
                  value={refineryUnit}
                  onChange={(e) => setRefineryUnit(e.target.value)}
                  className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                >
                  <option value="">All Refinery Units</option>
                  {unitField.distinct_values?.map((u: any) => (
                    <option key={String(u)} value={String(u)}>
                      {String(u)}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Department */}
            {deptField && !deptField.is_constant && (
              <div>
                <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Department</label>
                <select
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                >
                  <option value="">All Departments</option>
                  {deptField.distinct_values?.map((d: any) => (
                    <option key={String(d)} value={String(d)}>
                      {String(d)}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Action Status */}
            {(!statusField || !statusField.is_constant) && (
              <div>
                <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Action Status</label>
                <select
                  value={actionStatus}
                  onChange={(e) => setActionStatus(e.target.value)}
                  className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                >
                  <option value="">All Statuses</option>
                  {statusField && statusField.distinct_values && statusField.distinct_values.length > 0 ? (
                    statusField.distinct_values.map((s: any) => (
                      <option key={String(s)} value={String(s)}>
                        {String(s)}
                      </option>
                    ))
                  ) : (
                    <>
                      <option value="Open">Open</option>
                      <option value="In Progress">In Progress</option>
                      <option value="Closed">Closed</option>
                      <option value="Overdue">Overdue</option>
                    </>
                  )}
                </select>
              </div>
            )}

            {/* Report Type */}
            {typeField && !typeField.is_constant && typeField.distinct_values && typeField.distinct_values.length > 0 && (
              <div>
                <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Report Type</label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                >
                  <option value="">All Report Types</option>
                  {typeField.distinct_values.map((t: any) => (
                    <option key={String(t)} value={String(t)}>
                      {String(t)}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Date Range Start & End */}
            {hasDateField && (
              <>
                <div>
                  <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Date From</label>
                  <input
                    type="date"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                    className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                  />
                </div>

                <div>
                  <label className="text-[10px] text-[#526575] uppercase block mb-1 font-semibold">Date To</label>
                  <input
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                    className="w-full bg-white border border-[#D9E2EA] rounded-lg p-2 text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
                  />
                </div>
              </>
            )}
          </div>
        </div>

        {/* 3. Live Telemetry Preview Card */}
        <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-xl p-4 space-y-2 shadow-sm">
          <span className="text-[10px] font-mono text-[#718394] uppercase block font-semibold">LIVE MATCHING TELEMETRY:</span>
          {loadingPreview ? (
            <div className="text-xs font-mono text-[#1769AA] animate-pulse">Calculating matching records...</div>
          ) : preview ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="bg-white p-2.5 rounded-lg border border-[#D9E2EA] shadow-sm">
                <span className="text-[#718394] text-[10px] block font-semibold">MATCHING RECORDS</span>
                <span className="text-lg font-bold text-[#1769AA]">{preview.total_matching_reports}</span>
              </div>
              <div className="bg-white p-2.5 rounded-lg border border-[#D9E2EA] shadow-sm">
                <span className="text-[#718394] text-[10px] block font-semibold">HIGH RISK</span>
                <span className="text-lg font-bold text-rose-600">{preview.by_risk_level?.['High'] || preview.by_risk_level?.['HIGH'] || 0}</span>
              </div>
              <div className="bg-white p-2.5 rounded-lg border border-[#D9E2EA] shadow-sm">
                <span className="text-[#718394] text-[10px] block font-semibold">SIF PRECURSORS</span>
                <span className="text-lg font-bold text-rose-600">{preview.sif_precursor_count}</span>
              </div>
              <div className="bg-white p-2.5 rounded-lg border border-[#D9E2EA] shadow-sm">
                <span className="text-[#718394] text-[10px] block font-semibold">OVERDUE ACTIONS</span>
                <span className="text-lg font-bold text-amber-600">{preview.overdue_count}</span>
              </div>
            </div>
          ) : null}
        </div>

        {/* 4. Footer Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-[#D9E2EA]">
          <span className="text-[11px] font-mono text-[#718394]">
            Export generates uncorrupted, valid {format} document.
          </span>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-[#EEF3F7] hover:bg-[#D9E2EA] text-[#526575] font-mono text-xs font-semibold transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleDownload}
              disabled={downloading || (preview?.total_matching_reports === 0)}
              className="px-6 py-2 rounded-xl bg-[#1769AA] hover:bg-[#123B5D] text-white font-mono text-xs font-bold transition-all shadow-sm disabled:opacity-50 flex items-center gap-2"
            >
              {downloading ? 'Preparing Download...' : `Download ${format} Report `}
            </button>
          </div>
        </div>
      </div>
    </Modal>
  );
};
