import React, { useState, useEffect } from 'react';
import { RecurringIssuesResponse } from '../../types/safety';
import { api } from '../../services/api';

interface RecurringViewProps {
  datasetId?: string;
  onOpenReport: (reportId: string) => void;
}

export const RecurringView: React.FC<RecurringViewProps> = ({ datasetId, onOpenReport }) => {
  const [data, setData] = useState<RecurringIssuesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState<'equipment' | 'unit' | 'department' | 'work_type'>('equipment');

  useEffect(() => {
    setLoading(true);
    api.getRecurringIssues(datasetId)
      .then((res) => setData(res))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [datasetId]);

  if (loading) {
    return <div className="p-12 text-center text-xs font-mono text-[#1769AA] animate-pulse">Analyzing Recurring Safety Clusters...</div>;
  }

  if (!data) return null;

  const currentItems = {
    equipment: data.by_equipment,
    unit: data.by_refinery_unit,
    department: data.by_department,
    work_type: data.by_work_type,
  }[activeCategory];

  return (
    <div className="space-y-6">
      <div className="bg-white border border-[#D9E2EA] rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl"></span>
            <h2 className="text-base font-mono font-bold text-[#172B3A] uppercase tracking-wider">
              Recurring Safety Issues & Chronic Hotspots
            </h2>
          </div>
          <p className="text-xs font-sans text-[#526575] max-w-2xl">
            Detects repetitive near-miss occurrences across equipment tags, refinery units, and work activity patterns to eradicate systemic root causes.
          </p>
        </div>

        <div className="bg-[#F4F7FA] px-4 py-2 rounded-xl border border-[#D9E2EA] text-center">
          <span className="text-[10px] font-mono text-[#718394] uppercase block font-bold">RECURRING CLUSTERS</span>
          <span className="text-2xl font-mono font-bold text-[#E5A11A]">{data.total_recurring_clusters}</span>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex items-center gap-2 border-b border-[#D9E2EA] pb-3 text-xs font-mono">
        <button
          onClick={() => setActiveCategory('equipment')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
            activeCategory === 'equipment'
              ? 'bg-blue-50 text-[#1769AA] border border-blue-200 font-bold'
              : 'text-[#526575] hover:text-[#172B3A]'
          }`}
        >
           Repeated Equipment ({data.by_equipment.length})
        </button>
        <button
          onClick={() => setActiveCategory('unit')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
            activeCategory === 'unit'
              ? 'bg-blue-50 text-[#1769AA] border border-blue-200 font-bold'
              : 'text-[#526575] hover:text-[#172B3A]'
          }`}
        >
           Refinery Units ({data.by_refinery_unit.length})
        </button>
        <button
          onClick={() => setActiveCategory('department')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
            activeCategory === 'department'
              ? 'bg-blue-50 text-[#1769AA] border border-blue-200 font-bold'
              : 'text-[#526575] hover:text-[#172B3A]'
          }`}
        >
           Departments ({data.by_department.length})
        </button>
        <button
          onClick={() => setActiveCategory('work_type')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
            activeCategory === 'work_type'
              ? 'bg-blue-50 text-[#1769AA] border border-blue-200 font-bold'
              : 'text-[#526575] hover:text-[#172B3A]'
          }`}
        >
           Work Types ({data.by_work_type.length})
        </button>
      </div>

      {/* Clusters Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {currentItems.map((item) => (
          <div
            key={item.identifier}
            className="p-5 rounded-xl bg-white border border-[#D9E2EA] hover:border-[#1769AA]/50 transition-all space-y-3 shadow-sm"
          >
            <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
              <span className="font-mono font-bold text-[#172B3A] text-sm">{item.identifier}</span>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-[#EEF3F7] text-[#526575] text-[10px] font-mono font-bold">
                  {item.count} Observations
                </span>
                {item.sif_precursor_count > 0 && (
                  <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 text-[10px] font-mono font-bold">
                    {item.sif_precursor_count} SIF Precursors
                  </span>
                )}
              </div>
            </div>

            <div className="space-y-1.5 text-xs">
              <span className="text-[10px] font-mono text-[#718394] uppercase block font-bold">Sample Problem Descriptions:</span>
              {item.sample_descriptions.map((d, i) => (
                <p key={i} className="text-[#172B3A] font-sans text-xs bg-[#F4F7FA] p-2 rounded border border-[#D9E2EA] truncate">
                  "{d}"
                </p>
              ))}
            </div>

            {item.sample_report_ids && item.sample_report_ids.length > 0 && (
              <div className="flex items-center gap-2 pt-2 border-t border-[#D9E2EA] text-[11px] font-mono">
                <span className="text-[#718394]">Related IDs:</span>
                <div className="flex flex-wrap gap-1">
                  {item.sample_report_ids.map((id) => (
                    <span key={id} className="text-[#1769AA] font-bold px-1.5 py-0.5 rounded bg-blue-50 border border-blue-200">
                      {id}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
