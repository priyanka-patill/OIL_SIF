import React, { useState, useEffect } from 'react';
import { ReportAnalysis } from '../../types/safety';
import { api } from '../../services/api';
import { RiskBadge } from '../common/RiskBadge';
import { SIFBadge } from '../common/SIFBadge';

interface PredictabilityViewProps {
  datasetId?: string;
  onOpenReport: (reportId: string) => void;
}

export const PredictabilityView: React.FC<PredictabilityViewProps> = ({ datasetId, onOpenReport }) => {
  const [analyses, setAnalyses] = useState<ReportAnalysis[]>([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState<ReportAnalysis | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getHighRiskReports(datasetId, 1, 30)
      .then((res) => {
        setAnalyses(res.items || []);
        if (res.items && res.items.length > 0) {
          setSelectedAnalysis(res.items[0]);
        }
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [datasetId]);

  const esc = selectedAnalysis?.escalation_scenario;

  return (
    <div className="space-y-6">
      {/* Title & Guidance Header */}
      <div className="bg-white border border-[#D9E2EA] rounded-2xl p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xl"></span>
          <h2 className="text-base font-mono font-bold text-[#172B3A] uppercase tracking-wider">
            SIF Risk Prediction & Preventive Intelligence
          </h2>
        </div>
        <p className="text-xs font-sans text-[#526575] max-w-3xl">
          Probabilistic risk-escalation modeling and barrier defense intelligence. Evaluates the potential trajectory of unresolved safety conditions across operating process units.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left List: High-Risk Case Selector */}
        <div className="bg-white border border-[#D9E2EA] rounded-xl p-4 flex flex-col h-[680px] shadow-sm">
          <div className="pb-3 border-b border-[#D9E2EA] mb-3 flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-[#172B3A] uppercase">
              Evaluated Cases ({analyses.length})
            </span>
            <span className="text-[10px] font-mono text-[#1769AA] font-bold">SELECT TO MODEL</span>
          </div>

          {loading ? (
            <div className="p-8 text-center font-mono text-xs text-[#718394] animate-pulse">
              Loading Safety Cases...
            </div>
          ) : (
            <div className="space-y-2 overflow-y-auto custom-scrollbar flex-1 pr-1">
              {analyses.map((a) => {
                const isSelected = selectedAnalysis?.id === a.id;
                const rep = a.report;
                return (
                  <div
                    key={a.id}
                    onClick={() => setSelectedAnalysis(a)}
                    className={`p-3 rounded-lg border transition-all cursor-pointer text-xs font-mono ${
                      isSelected
                        ? 'bg-[#EEF3F7] border-[#1769AA] ring-1 ring-[#1769AA]/30 shadow-sm'
                        : 'bg-[#F4F7FA] border-[#D9E2EA] hover:border-[#1769AA]/50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-[#1769AA]">{rep?.original_id || a.report_id}</span>
                      <RiskBadge level={a.ai_risk_level} size="sm" />
                    </div>
                    <p className="text-[#172B3A] font-sans text-[11px] truncate mb-1">
                      "{a.observed_problem}"
                    </p>
                    <div className="flex items-center justify-between text-[10px] text-[#718394]">
                      <span>{rep?.refinery_unit}</span>
                      <span>{a.sif_category.split('/')[0]}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Detail: 6-Stage Potential Escalation & Actions */}
        <div className="lg:col-span-2 space-y-4">
          {selectedAnalysis ? (
            <div className="space-y-4">
              {/* Selected Case Header */}
              <div className="bg-white border border-[#D9E2EA] rounded-xl p-5 flex items-start justify-between shadow-sm">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-mono font-bold text-[#1769AA]">
                      {selectedAnalysis.report?.original_id || selectedAnalysis.report_id}
                    </span>
                    <span className="text-xs font-mono text-[#526575]">
                      • {selectedAnalysis.report?.refinery_unit} • {selectedAnalysis.report?.equipment}
                    </span>
                    <SIFBadge status={selectedAnalysis.sif_precursor} size="sm" />
                  </div>
                  <p className="text-sm font-sans text-[#172B3A] font-medium">
                    "{selectedAnalysis.observed_problem}"
                  </p>
                </div>
                <button
                  onClick={() => onOpenReport(selectedAnalysis.report_id)}
                  className="px-3 py-1.5 rounded-lg bg-[#1769AA] hover:bg-[#123B5D] text-white text-xs font-mono font-bold transition-colors shrink-0 shadow-sm"
                >
                  Full Report 
                </button>
              </div>

              {/* 6-Stage Potential Escalation Model */}
              {esc && (
                <div className="bg-white border border-[#D9E2EA] rounded-xl p-5 space-y-3 shadow-sm">
                  <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-2">
                    <h3 className="text-xs font-mono font-bold text-[#123B5D] uppercase tracking-wider flex items-center gap-2">
                      Risk-Escalation Scenario (Potential Progression)
                    </h3>
                    <span className="text-[10px] font-mono text-[#718394] uppercase">
                      Non-Deterministic Scenario Analysis
                    </span>
                  </div>

                  <div className="space-y-2 text-xs font-mono">
                    <div className="p-3 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA]">
                      <span className="text-[#526575] text-[10px] font-bold block mb-0.5 uppercase">1. CURRENT CONDITION</span>
                      <p className="text-[#172B3A] font-sans">{esc.current_condition}</p>
                    </div>
                    <div className="text-center text-[#718394] font-mono text-xs">↓</div>
                    <div className="p-3 rounded-lg bg-blue-50/60 border border-blue-200">
                      <span className="text-blue-800 text-[10px] font-bold block mb-0.5 uppercase">2. CONTINUED EXPOSURE</span>
                      <p className="text-[#172B3A] font-sans">{esc.continued_exposure}</p>
                    </div>
                    <div className="text-center text-[#718394] font-mono text-xs">↓</div>
                    <div className="p-3 rounded-lg bg-amber-50/60 border border-amber-200">
                      <span className="text-amber-800 text-[10px] font-bold block mb-0.5 uppercase">3. LOSS OF CONTROL</span>
                      <p className="text-[#172B3A] font-sans">{esc.loss_of_control}</p>
                    </div>
                    <div className="text-center text-[#718394] font-mono text-xs">↓</div>
                    <div className="p-3 rounded-lg bg-orange-50/60 border border-orange-200">
                      <span className="text-orange-800 text-[10px] font-bold block mb-0.5 uppercase">4. INCIDENT EVENT</span>
                      <p className="text-[#172B3A] font-sans">{esc.incident_event}</p>
                    </div>
                    <div className="text-center text-[#718394] font-mono text-xs">↓</div>
                    <div className="p-3 rounded-lg bg-rose-50/60 border border-rose-200">
                      <span className="text-rose-800 text-[10px] font-bold block mb-0.5 uppercase">5. SERIOUS CONSEQUENCE</span>
                      <p className="text-[#172B3A] font-sans">{esc.serious_consequence}</p>
                    </div>
                    <div className="text-center text-[#718394] font-mono text-xs">↓</div>
                    <div className="p-3.5 rounded-lg bg-red-100/70 border border-red-300 shadow-sm">
                      <span className="text-red-900 text-[10px] font-bold block mb-0.5 uppercase">6. POTENTIAL SIF FATAL CONSEQUENCE</span>
                      <p className="text-red-950 font-sans font-semibold">{esc.potential_fatal_consequence}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Recommended Actions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-rose-50/60 border border-rose-200 rounded-xl p-4">
                  <h4 className="text-xs font-mono font-bold text-rose-900 uppercase mb-1.5 flex items-center gap-1.5">
                    Immediate Action
                  </h4>
                  <p className="text-xs font-sans text-rose-950 leading-relaxed">
                    {selectedAnalysis.immediate_action_recommendation}
                  </p>
                </div>

                <div className="bg-emerald-50/60 border border-emerald-200 rounded-xl p-4">
                  <h4 className="text-xs font-mono font-bold text-emerald-900 uppercase mb-1.5 flex items-center gap-1.5">
                    Preventive Strategy
                  </h4>
                  <p className="text-xs font-sans text-emerald-950 leading-relaxed">
                    {selectedAnalysis.preventive_action_recommendation}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white border border-[#D9E2EA] rounded-xl p-12 text-center text-[#718394] font-mono text-xs shadow-sm">
              Select a safety observation on the left to review its predictive risk-escalation scenario.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
