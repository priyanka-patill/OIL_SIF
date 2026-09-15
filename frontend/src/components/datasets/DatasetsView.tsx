import React, { useState, useEffect } from 'react';
import { DatasetItem, DatasetSchemaInfo, DataQualitySummary, DatasetComparisonData } from '../../types/safety';
import { api } from '../../services/api';

interface DatasetsViewProps {
  datasets: DatasetItem[];
  selectedDatasetId: string;
}

export const DatasetsView: React.FC<DatasetsViewProps> = ({ datasets, selectedDatasetId }) => {
  const [schema, setSchema] = useState<DatasetSchemaInfo | null>(null);
  const [quality, setQuality] = useState<DataQualitySummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');

  // Dataset Comparison State
  const [compDatasetA, setCompDatasetA] = useState<string>('');
  const [compDatasetB, setCompDatasetB] = useState<string>('');
  const [comparisonData, setComparisonData] = useState<DatasetComparisonData | null>(null);
  const [compLoading, setCompLoading] = useState(false);

  useEffect(() => {
    if (!selectedDatasetId) return;

    setLoading(true);
    Promise.all([
      api.getDatasetSchema(selectedDatasetId),
      api.getDataQuality(selectedDatasetId),
    ])
      .then(([schemaData, qualityData]) => {
        setSchema(schemaData);
        setQuality(qualityData);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [selectedDatasetId]);

  // Set default comparison datasets once available
  useEffect(() => {
    if (datasets.length >= 2 && !compDatasetA && !compDatasetB) {
      const singleDs = datasets.find((d) => d.dataset_type === 'single_factor' && !d.is_summary_dataset);
      const multiDs = datasets.find((d) => d.dataset_type === 'multi_factor' || d.dataset_type === 'high_potential');
      if (singleDs && multiDs) {
        setCompDatasetA(singleDs.id);
        setCompDatasetB(multiDs.id);
      } else {
        setCompDatasetA(datasets[0].id);
        setCompDatasetB(datasets[1].id);
      }
    }
  }, [datasets]);

  // Trigger comparison when datasets change
  useEffect(() => {
    if (compDatasetA && compDatasetB && compDatasetA !== compDatasetB) {
      setCompLoading(true);
      api.compareDatasets(compDatasetA, compDatasetB)
        .then((data) => setComparisonData(data))
        .catch((err) => console.error('Comparison error:', err))
        .finally(() => setCompLoading(false));
    }
  }, [compDatasetA, compDatasetB]);

  const filteredDatasets = datasets.filter((d) => {
    if (filterType === 'all') return true;
    if (filterType === 'single_factor') return d.dataset_type === 'single_factor';
    if (filterType === 'multi_factor') return d.dataset_type === 'multi_factor';
    if (filterType === 'high_potential') return d.dataset_type === 'high_potential';
    if (filterType === 'summary') return d.is_summary_dataset || d.dataset_type === 'summary';
    return true;
  });

  const getTypeBadge = (type?: string, isSummary?: boolean) => {
    if (isSummary || type === 'summary') {
      return <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 text-[10px] font-bold uppercase">Summary Sheet</span>;
    }
    if (type === 'high_potential') {
      return <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 text-[10px] font-bold uppercase">High Potential (HiPo)</span>;
    }
    if (type === 'multi_factor') {
      return <span className="px-2 py-0.5 rounded bg-purple-50 text-purple-800 border border-purple-200 text-[10px] font-bold uppercase">Multi-Factor</span>;
    }
    return <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200 text-[10px] font-bold uppercase">Single Factor</span>;
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-white border border-[#D9E2EA] rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl"></span>
            <h2 className="text-base font-mono font-bold text-[#172B3A] uppercase tracking-wider">
              Central Dataset Registry & Corpus Telemetry
            </h2>
          </div>
          <p className="text-xs font-sans text-[#526575] max-w-3xl">
            Multi-dataset safety corpus registry preserving sheet hierarchy, factor counts (1-factor to 4-factor), 
            dedicated high-potential flags, and side-by-side dataset comparative intelligence.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-[#F4F7FA] px-4 py-2 rounded-xl border border-[#D9E2EA] text-center">
            <span className="text-[10px] font-mono text-[#718394] uppercase block font-bold">ACTIVE DATASETS</span>
            <span className="text-xl font-mono font-bold text-[#1769AA]">{datasets.length}</span>
          </div>
          <div className="bg-[#F4F7FA] px-4 py-2 rounded-xl border border-[#D9E2EA] text-center">
            <span className="text-[10px] font-mono text-[#718394] uppercase block font-bold">OPERATIONAL REPORTS</span>
            <span className="text-xl font-mono font-bold text-[#2E8B57]">
              {datasets.reduce((sum, d) => sum + (d.is_summary_dataset ? 0 : d.row_count), 0)}
            </span>
          </div>
        </div>
      </div>

      {/* Dataset Type Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-[#D9E2EA] pb-3 overflow-x-auto">
        <button
          onClick={() => setFilterType('all')}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${filterType === 'all' ? 'bg-[#1769AA] text-white font-bold' : 'text-[#526575] hover:text-[#172B3A]'}`}
        >
          All Datasets ({datasets.length})
        </button>
        <button
          onClick={() => setFilterType('single_factor')}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${filterType === 'single_factor' ? 'bg-[#1769AA] text-white font-bold' : 'text-[#526575] hover:text-[#172B3A]'}`}
        >
          Single Factor ({datasets.filter(d => d.dataset_type === 'single_factor').length})
        </button>
        <button
          onClick={() => setFilterType('multi_factor')}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${filterType === 'multi_factor' ? 'bg-[#1769AA] text-white font-bold' : 'text-[#526575] hover:text-[#172B3A]'}`}
        >
          Multi-Factor ({datasets.filter(d => d.dataset_type === 'multi_factor').length})
        </button>
        <button
          onClick={() => setFilterType('high_potential')}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${filterType === 'high_potential' ? 'bg-rose-600 text-white font-bold' : 'text-[#526575] hover:text-[#172B3A]'}`}
        >
          High Potential ({datasets.filter(d => d.dataset_type === 'high_potential').length})
        </button>
        <button
          onClick={() => setFilterType('summary')}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${filterType === 'summary' ? 'bg-amber-600 text-white font-bold' : 'text-[#526575] hover:text-[#172B3A]'}`}
        >
          Summary Sheets ({datasets.filter(d => d.is_summary_dataset || d.dataset_type === 'summary').length})
        </button>
      </div>

      {/* Dataset Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredDatasets.map((d) => (
          <div
            key={d.id}
            className={`p-5 rounded-xl border shadow-sm space-y-3 text-xs font-mono transition-all ${
              d.id === selectedDatasetId 
                ? 'bg-[#EEF3F7] border-[#1769AA] ring-1 ring-[#1769AA]/30' 
                : 'bg-white border-[#D9E2EA] hover:border-[#1769AA]/50'
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="font-bold text-[#172B3A] text-sm">{d.dataset_name}</span>
              {getTypeBadge(d.dataset_type, d.is_summary_dataset)}
            </div>

            <div className="space-y-1.5 text-[#526575] pt-1 border-t border-[#D9E2EA]">
              <div className="flex justify-between">
                <span>Sheet Name:</span>
                <strong className="text-[#172B3A]">{d.sheet_name || d.dataset_name}</strong>
              </div>
              <div className="flex justify-between">
                <span>Factor Count:</span>
                <strong className="text-purple-700 font-bold">{d.factor_count ?? (d.is_summary_dataset ? 0 : 1)} Factor(s)</strong>
              </div>
              <div className="flex justify-between">
                <span>Row Count:</span>
                <strong className="text-[#2E8B57] font-bold">{d.row_count} {d.is_summary_dataset ? 'metadata rows' : 'reports'}</strong>
              </div>
              <div className="flex justify-between">
                <span>Data Quality:</span>
                <strong className="text-emerald-700">{d.data_quality_status || 'PASSED'}</strong>
              </div>
            </div>

            {d.factor_names && d.factor_names.length > 0 && (
              <div className="pt-2 border-t border-[#D9E2EA]">
                <span className="text-[10px] text-[#718394] block mb-1 uppercase font-bold">Active Factors:</span>
                <div className="flex flex-wrap gap-1">
                  {d.factor_names.map((fn, idx) => (
                    <span key={idx} className="px-1.5 py-0.5 rounded bg-[#F4F7FA] text-[#172B3A] text-[10px] border border-[#D9E2EA]">
                      {fn.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* DATASET COMPARISON TOOL */}
      <div className="bg-white border border-[#D9E2EA] rounded-2xl p-6 space-y-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#D9E2EA] pb-4">
          <div>
            <h3 className="text-sm font-mono font-bold text-[#172B3A] uppercase tracking-wider flex items-center gap-2">
              Multi-Dataset Safety Comparative Intelligence
            </h3>
            <p className="text-xs font-sans text-[#526575]">
              Compare any two safety datasets side-by-side to detect risk escalation and multi-factor barrier breakdown.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div>
              <label className="text-[10px] font-mono text-[#718394] block mb-1 font-bold">DATASET A (BASELINE)</label>
              <select
                value={compDatasetA}
                onChange={(e) => setCompDatasetA(e.target.value)}
                className="px-3 py-1.5 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA] text-xs font-mono text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
              >
                {datasets.filter(d => !d.is_summary_dataset).map((d) => (
                  <option key={d.id} value={d.id}>{d.dataset_name} ({d.factor_count} Factor)</option>
                ))}
              </select>
            </div>

            <span className="text-[#718394] font-mono pt-4 text-xs font-bold">VS</span>

            <div>
              <label className="text-[10px] font-mono text-[#718394] block mb-1 font-bold">DATASET B (TARGET)</label>
              <select
                value={compDatasetB}
                onChange={(e) => setCompDatasetB(e.target.value)}
                className="px-3 py-1.5 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA] text-xs font-mono text-[#172B3A] focus:outline-none focus:border-[#1769AA]"
              >
                {datasets.filter(d => !d.is_summary_dataset).map((d) => (
                  <option key={d.id} value={d.id}>{d.dataset_name} ({d.factor_count} Factor)</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {compLoading && (
          <div className="text-center py-6 text-xs font-mono text-[#718394] animate-pulse">
            Analyzing cross-dataset variance and factor distributions...
          </div>
        )}

        {comparisonData && !compLoading && (
          <div className="space-y-6">
            {/* Comparative KPI Header */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-4 rounded-xl bg-[#F4F7FA] border border-[#D9E2EA]">
                <span className="text-[#718394] text-[10px] block mb-1 uppercase font-bold">Total Reports</span>
                <div className="flex items-baseline justify-between">
                  <span className="text-[#172B3A]">{comparisonData.dataset_a.name}: <strong>{comparisonData.total_reports_a}</strong></span>
                  <span className="text-[#1769AA]">{comparisonData.dataset_b.name}: <strong>{comparisonData.total_reports_b}</strong></span>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#F4F7FA] border border-[#D9E2EA]">
                <span className="text-[#718394] text-[10px] block mb-1 uppercase font-bold">High Potential Incidents</span>
                <div className="flex items-baseline justify-between">
                  <span className="text-[#172B3A]">{comparisonData.high_potential_count_a}</span>
                  <span className="text-rose-700 font-bold">{comparisonData.high_potential_count_b}</span>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#F4F7FA] border border-[#D9E2EA]">
                <span className="text-[#718394] text-[10px] block mb-1 uppercase font-bold">Active Factors</span>
                <div className="flex items-baseline justify-between">
                  <span className="text-[#172B3A]">{comparisonData.dataset_a.factor_count} Factors</span>
                  <span className="text-purple-700 font-bold">{comparisonData.dataset_b.factor_count} Factors</span>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#F4F7FA] border border-[#D9E2EA]">
                <span className="text-[#718394] text-[10px] block mb-1 uppercase font-bold">Open / Pending Actions</span>
                <div className="flex items-baseline justify-between">
                  <span className="text-[#172B3A]">{comparisonData.open_actions_count_a}</span>
                  <span className="text-[#E5A11A] font-bold">{comparisonData.open_actions_count_b}</span>
                </div>
              </div>
            </div>

            {/* Side-by-Side Risk Distribution Comparison */}
            <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-xl p-5 space-y-4">
              <h4 className="text-xs font-mono font-bold text-[#172B3A] uppercase tracking-wider">
                Risk Distribution Comparison
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="border-b border-[#D9E2EA] text-[10px] font-bold text-[#526575] uppercase">
                      <th className="py-2">Risk Level</th>
                      <th className="py-2">{comparisonData.dataset_a.name} (Count / %)</th>
                      <th className="py-2">{comparisonData.dataset_b.name} (Count / %)</th>
                      <th className="py-2">Variance (Delta)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#D9E2EA]">
                    {comparisonData.risk_distribution_comparison.map((r, i) => (
                      <tr key={i}>
                        <td className="py-2.5 font-bold text-[#172B3A]">{r.risk_level}</td>
                        <td className="py-2.5 text-[#526575]">{r.count_a} ({r.percentage_a}%)</td>
                        <td className="py-2.5 text-[#1769AA] font-bold">{r.count_b} ({r.percentage_b}%)</td>
                        <td className="py-2.5">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            r.delta_percentage > 0 ? 'bg-rose-50 text-rose-800 border border-rose-200' : r.delta_percentage < 0 ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-[#EEF3F7] text-[#526575]'
                          }`}>
                            {r.delta_percentage > 0 ? `+${r.delta_percentage}%` : `${r.delta_percentage}%`}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* AI Comparative Insights */}
            {comparisonData.comparative_insights.length > 0 && (
              <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-200 space-y-2">
                <span className="text-[10px] font-mono text-[#1769AA] uppercase font-bold block">
                   AI Cross-Dataset Pattern Insights:
                </span>
                {comparisonData.comparative_insights.map((insight, idx) => (
                  <p key={idx} className="text-xs font-sans text-[#172B3A] flex items-start gap-2">
                    <span className="text-[#1769AA] font-mono">•</span>
                    <span>{insight}</span>
                  </p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Quality Scorecard */}
      {quality && (
        <div className="bg-white border border-[#D9E2EA] rounded-xl p-6 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-3">
            <div>
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-[#2E8B57]" />
                Data Quality Scorecard ({quality.dataset_name})
              </h3>
              <p className="text-[11px] font-sans text-[#526575]">
                Automated profiling evaluating completeness, uniqueness, and temporal integrity
              </p>
            </div>
            <div className="text-right">
              <span className="text-3xl font-mono font-bold text-[#2E8B57]">{quality.data_quality_score}%</span>
              <span className="text-[10px] font-mono text-[#718394] block font-bold">HEALTH SCORE</span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            <div className="p-3 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA]">
              <span className="text-[#718394] text-[10px] block mb-1 font-bold">VALID RECORDS</span>
              <span className="text-lg font-bold text-[#172B3A]">{quality.valid_records_count} / {quality.total_rows}</span>
            </div>
            <div className="p-3 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA]">
              <span className="text-[#718394] text-[10px] block mb-1 font-bold">MISSING VALUES</span>
              <span className="text-lg font-bold text-[#2E8B57]">{quality.missing_values_count}</span>
            </div>
            <div className="p-3 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA]">
              <span className="text-[#718394] text-[10px] block mb-1 font-bold">DUPLICATE IDS</span>
              <span className="text-lg font-bold text-[#2E8B57]">{quality.duplicate_ids_count}</span>
            </div>
            <div className="p-3 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA]">
              <span className="text-[#718394] text-[10px] block mb-1 font-bold">CONSTANT COLUMNS</span>
              <span className="text-lg font-bold text-[#E5A11A]">{quality.constant_fields_count}</span>
            </div>
          </div>

          <div className="p-3.5 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA] space-y-1.5">
            <span className="text-[10px] font-mono text-[#718394] uppercase block font-bold">Automated Profiling Notes:</span>
            {quality.summary_notes.map((note, i) => (
              <p key={i} className="text-xs font-sans text-[#172B3A] flex items-start gap-2">
                <span className="text-[#1769AA] font-mono">•</span>
                <span>{note}</span>
              </p>
            ))}
          </div>
        </div>
      )}

      {/* Dynamic Schema Columns Table */}
      {schema && (
        <div className="bg-white border border-[#D9E2EA] rounded-xl overflow-hidden shadow-sm">
          <div className="p-4 border-b border-[#D9E2EA] bg-[#EEF3F7] flex items-center justify-between">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] flex items-center gap-2">
              Detected Schema & Semantic Mapping ({schema.columns.length} Columns)
            </h3>
            <span className="text-[10px] font-mono text-[#526575]">
              Mapped: <strong className="text-[#1769AA]">{schema.mapped_fields_count}</strong> | Constant: <strong className="text-[#E5A11A]">{schema.constant_fields.length}</strong>
            </span>
          </div>

          <div className="overflow-x-auto custom-scrollbar">
            <table className="w-full text-left border-collapse text-xs font-mono">
              <thead>
                <tr className="bg-[#EEF3F7] border-b border-[#D9E2EA] text-[10px] font-bold text-[#526575] uppercase">
                  <th className="px-4 py-2.5">#</th>
                  <th className="px-4 py-2.5">Original Column Name</th>
                  <th className="px-4 py-2.5">Inferred Data Type</th>
                  <th className="px-4 py-2.5">Semantic Type</th>
                  <th className="px-4 py-2.5">Canonical Mapping</th>
                  <th className="px-4 py-2.5">Unique Count</th>
                  <th className="px-4 py-2.5">Constant Flag</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D9E2EA]">
                {schema.columns.map((col, idx) => (
                  <tr key={col.id} className="hover:bg-[#EEF3F7]/50 transition-colors">
                    <td className="px-4 py-2 text-[#718394]">{idx + 1}</td>
                    <td className="px-4 py-2 font-bold text-[#172B3A]">{col.original_name}</td>
                    <td className="px-4 py-2 text-[#1769AA]">{col.detected_data_type}</td>
                    <td className="px-4 py-2 text-blue-800">{col.semantic_type}</td>
                    <td className="px-4 py-2 text-[#2E8B57] font-semibold">
                      {col.mapped_canonical_field ? `→ ${col.mapped_canonical_field}` : '—'}
                    </td>
                    <td className="px-4 py-2 text-[#172B3A]">{col.unique_count}</td>
                    <td className="px-4 py-2">
                      {col.is_constant ? (
                        <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 text-[10px] font-bold">
                          CONSTANT ({col.constant_value})
                        </span>
                      ) : (
                        <span className="text-[#718394]">No</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
