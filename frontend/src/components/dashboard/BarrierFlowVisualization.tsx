import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { InfoTooltip } from '../common/InfoTooltip';

interface BarrierFlowVisualizationProps {
  datasetId?: string;
  onSelectBarrier?: (barrierName: string) => void;
}

export const BarrierFlowVisualization: React.FC<BarrierFlowVisualizationProps> = ({
  datasetId,
  onSelectBarrier,
}) => {
  const [barrierSummary, setBarrierSummary] = useState<any>(null);
  const [selectedStage, setSelectedStage] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    setLoading(true);
    api.getBarrierSummary(datasetId)
      .then(setBarrierSummary)
      .catch(() => setBarrierSummary(null))
      .finally(() => setLoading(false));
  }, [datasetId]);

  const defaultBarriers = [
    { name: 'PPE & Personal Protection', stage: '1. Observed Condition', type: 'PPE', icon: '', desc: 'Unsafe conditions or non-compliance observed on-site.' },
    { name: 'Equipment Maintenance Integrity', stage: '2. Exposure', type: 'MAINTENANCE', icon: '', desc: 'Workers exposed to uncontained operational hazards.' },
    { name: 'Supervisory & Operational Oversight', stage: '3. Barrier Weakened', type: 'SUPERVISION', icon: '', desc: 'Control barriers degraded or missing oversight.' },
    { name: 'Corrective Action Remediation', stage: '4. Loss of Control', type: 'ACTION', icon: '', desc: 'Near-miss event occurs without immediate containment.' },
    { name: 'Recurrence Prevention & Systemic Learning', stage: '5. Potential Consequence', type: 'LEARNING', icon: '', desc: 'Potential for severe injury, fatality, or facility damage.' }
  ];

  const getBarrierStatus = (barrierName: string) => {
    if (!barrierSummary) return { status: 'INTACT', color: 'border-[#2E8B57]/40 text-[#2E8B57] bg-[#2E8B57]/10 font-bold' };
    const degradedDist = barrierSummary.degraded_distribution || {};
    const failedDist = barrierSummary.failed_distribution || {};

    let degradedCount = 0;
    let failedCount = 0;

    Object.entries(failedDist).forEach(([k, v]) => {
      if (k.toLowerCase().includes(barrierName.toLowerCase().slice(0, 5))) failedCount += Number(v);
    });
    Object.entries(degradedDist).forEach(([k, v]) => {
      if (k.toLowerCase().includes(barrierName.toLowerCase().slice(0, 5))) degradedCount += Number(v);
    });

    if (failedCount > 0) {
      return { status: 'FAILED', count: failedCount, color: 'border-[#D64545]/40 text-[#D64545] bg-[#D64545]/10 font-bold' };
    }
    if (degradedCount > 0) {
      return { status: 'DEGRADED', count: degradedCount, color: 'border-[#E5A11A]/40 text-[#B87A00] bg-[#E5A11A]/10 font-bold' };
    }
    return { status: 'INTACT', color: 'border-[#2E8B57]/40 text-[#2E8B57] bg-[#2E8B57]/10 font-bold' };
  };

  return (
    <div className="bg-white border border-[#D9E2EA] rounded-2xl p-6 shadow-sm space-y-4">
      {/* Title Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#D9E2EA]">
        <div>
          <div className="flex items-center gap-1.5">
            <h3 className="text-sm font-bold text-[#172B3A]">
              How Did the Safety Risk Develop?
            </h3>
            <InfoTooltip
              title="Swiss Cheese Barrier Model"
              text="Illustrates how safety risks escalate step-by-step when multiple defense layers fail or become degraded simultaneously."
            />
          </div>
          <p className="text-xs text-[#526575] mt-0.5 font-medium">
            Swiss Cheese Barrier Analysis — Step-by-Step Risk Escalation
          </p>
        </div>
        <span className="text-xs font-bold text-[#1769AA] bg-[#EEF3F7] border border-[#D9E2EA] px-3 py-1 rounded-xl shadow-xs">
          Active Defense Flow
        </span>
      </div>

      {/* Visual Step-by-Step Flow */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
        {defaultBarriers.map((b, idx) => {
          const st = getBarrierStatus(b.name);
          const isSelected = selectedStage === idx;

          return (
            <div
              key={idx}
              onClick={() => {
                setSelectedStage(isSelected ? null : idx);
                if (onSelectBarrier) onSelectBarrier(b.name);
              }}
              className={`p-3.5 rounded-xl border ${st.color} cursor-pointer hover:border-[#1769AA] transition-all flex flex-col justify-between space-y-2 shadow-xs ${
                isSelected ? 'ring-2 ring-[#1769AA] shadow-md' : ''
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-lg">{b.icon}</span>
                  <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md bg-white/80 border border-[#D9E2EA] shadow-xs">
                    {st.status}
                  </span>
                </div>
                <div className="text-xs font-bold text-[#172B3A]">{b.stage}</div>
                <div className="text-[11px] text-[#526575] font-medium mt-1 leading-snug">{b.name}</div>
              </div>
              <div className="text-[10px] text-[#1769AA] font-bold pt-1 border-t border-[#D9E2EA] flex items-center justify-between">
                <span>Stage {idx + 1}</span>
                <span>Click for details </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Stage Explanation Drawer */}
      {selectedStage !== null && (
        <div className="p-4 bg-[#EEF3F7] rounded-xl border border-[#D9E2EA] text-xs space-y-2 animate-in fade-in duration-150">
          <div className="flex items-center justify-between">
            <span className="font-bold text-[#1769AA] text-sm">
              {defaultBarriers[selectedStage].stage}: {defaultBarriers[selectedStage].name}
            </span>
            <button
              type="button"
              onClick={() => setSelectedStage(null)}
              className="text-[#526575] hover:text-[#172B3A] text-xs font-bold"
            >
              ✕ Close
            </button>
          </div>
          <p className="text-[#172B3A] leading-relaxed font-medium">
            {defaultBarriers[selectedStage].desc}
          </p>
          <div className="text-[11px] text-[#526575] pt-1 font-semibold">
            Status: <span className="font-bold text-[#172B3A]">{getBarrierStatus(defaultBarriers[selectedStage].name).status}</span> across active dataset reports.
          </div>
        </div>
      )}

      {/* Simple Flow Footer */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-3 bg-[#EEF3F7] rounded-xl border border-[#D9E2EA] text-xs">
        <div className="flex items-center gap-2 flex-wrap text-[#172B3A]">
          <span className="font-bold text-[#526575]">Risk Escalation Path:</span>
          <span className="font-medium">Observed Condition</span>
          <span className="text-[#718394]"></span>
          <span className="font-medium">Exposure</span>
          <span className="text-[#718394]"></span>
          <span className="font-medium">Barrier Weakened</span>
          <span className="text-[#718394]"></span>
          <span className="font-medium">Loss of Control</span>
          <span className="text-[#718394]"></span>
          <span className="text-[#D64545] font-extrabold">Consequence</span>
        </div>
      </div>
    </div>
  );
};
