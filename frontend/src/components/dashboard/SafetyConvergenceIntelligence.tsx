import React from 'react';
import { BDICard } from './BDICard';
import { SafetyConvergenceCard } from './SafetyConvergenceCard';
import { BarrierFlowVisualization } from './BarrierFlowVisualization';
import { ActionControlCenter } from './ActionControlCenter';

interface SafetyConvergenceIntelligenceProps {
  datasetId?: string;
  onViewReport?: (reportId: string) => void;
  onViewAction?: (actionId: string) => void;
  onSelectUnit?: (unit: string) => void;
  onOpenChatWithQuery?: (query: string) => void;
  showEscalationFlow?: boolean;
}

export const SafetyConvergenceIntelligence: React.FC<SafetyConvergenceIntelligenceProps> = ({
  datasetId,
  onViewReport,
  onViewAction,
  onSelectUnit,
  onOpenChatWithQuery,
  showEscalationFlow = false,
}) => {
  return (
    <section className="space-y-6 my-6">
      {/* Top Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-[#D9E2EA] pb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl"></span>
            <h2 className="text-sm font-bold text-[#172B3A] uppercase tracking-wider">
              Safety Priority Alerts & Barrier Defense
            </h2>
          </div>
          <p className="text-xs text-[#526575] mt-0.5 font-medium">
            Key critical safety issues, safety barrier health, and active remediation tracking.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="px-3 py-1 bg-[#EEF3F7] text-[#1769AA] border border-[#D9E2EA] rounded-xl font-bold shadow-xs">
            Real-time Telemetry Active
          </span>
        </div>
      </div>

      {/* Top Priority Grid: Critical Safety Alert Spotlight & Safety Barrier Health */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SafetyConvergenceCard
          datasetId={datasetId}
          onViewReport={onViewReport}
          onViewAction={onViewAction}
          onOpenChatWithQuery={onOpenChatWithQuery}
        />
        <BDICard datasetId={datasetId} onSelectUnit={onSelectUnit} />
      </div>

      {/* Action Remediation & Governance Control Center */}
      <ActionControlCenter onViewAction={onViewAction} onViewReport={onViewReport} />

      {/* Step-by-Step Risk Escalation Flow (Conditional for Deep Views) */}
      {showEscalationFlow && <BarrierFlowVisualization datasetId={datasetId} />}
    </section>
  );
};
