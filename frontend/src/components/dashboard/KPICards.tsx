import React from 'react';
import { ReportCounts, SafetyReport, SIFSummary } from '../../types/safety';
import { normalizeRiskLevel } from '../../utils/riskClassification';
import { InfoTooltip } from '../common/InfoTooltip';
import {
  ShieldAlert,
  AlertTriangle,
  Clock,
  FileText,
  AlertCircle,
  CheckCircle2,
  CheckSquare,
  TrendingUp
} from 'lucide-react';

interface KPICardsProps {
  counts: ReportCounts | null;
  sifSummary: SIFSummary | null;
  reports?: SafetyReport[];
  onFilterRisk?: (risk: string) => void;
  onFilterStatus?: (status: string) => void;
  onFilterSIF?: () => void;
}

export const KPICards: React.FC<KPICardsProps> = ({
  counts,
  sifSummary,
  reports,
  onFilterRisk,
  onFilterStatus,
  onFilterSIF,
}) => {
  if (!counts && (!reports || reports.length === 0)) return null;

  const total = reports && reports.length > 0 ? reports.length : (counts?.total_reports || 0);

  const highRisk = reports && reports.length > 0
    ? reports.filter((r) => normalizeRiskLevel(r.risk_level, r.raw_data) === 'HIGH').length
    : (counts?.by_risk_level?.['HIGH'] ?? counts?.by_risk_level?.['High'] ?? 0);

  const medRisk = reports && reports.length > 0
    ? reports.filter((r) => normalizeRiskLevel(r.risk_level, r.raw_data) === 'MEDIUM').length
    : (counts?.by_risk_level?.['MEDIUM'] ?? counts?.by_risk_level?.['Medium'] ?? 0);

  const lowRisk = reports && reports.length > 0
    ? reports.filter((r) => normalizeRiskLevel(r.risk_level, r.raw_data) === 'LOW').length
    : (counts?.by_risk_level?.['LOW'] ?? counts?.by_risk_level?.['Low'] ?? 0);


  const openActions = counts?.by_action_status?.['Open'] || counts?.by_action_status?.['OPEN'] || 0;
  const inProgressActions = counts?.by_action_status?.['In Progress'] || 0;
  const closedActions = counts?.by_action_status?.['Closed'] || 0;
  const overdueActions = counts?.by_action_status?.['Overdue'] || counts?.by_action_status?.['OVERDUE'] || 0;

  const sifCount = sifSummary?.sif_precursors_detected || 0;
  const sifRate = sifSummary?.sif_precursor_rate_percentage || 0;

  // Determine overall safety status based on existing data
  let overallStatus = 'STABLE';
  let overallBadge = 'bg-[#2E8B57]/15 text-[#2E8B57] border-[#2E8B57]/30 font-bold';
  let overallText = 'Normal operational safety profile. Safety barriers are active.';

  if (sifCount > 0 || highRisk > 5 || overdueActions > 5) {
    overallStatus = 'CRITICAL ATTENTION REQUIRED';
    overallBadge = 'bg-[#D64545]/15 text-[#D64545] border-[#D64545]/30 font-bold';
    overallText = `Active critical SIF exposures (${sifCount}) and high-risk items require immediate supervision.`;
  } else if (highRisk > 0 || overdueActions > 0) {
    overallStatus = 'ATTENTION REQUIRED';
    overallBadge = 'bg-[#E5A11A]/15 text-[#B87A00] border-[#E5A11A]/40 font-bold';
    overallText = `${highRisk} high-risk observations and ${overdueActions} overdue actions pending remediation.`;
  }

  const primaryCards = [
    {
      title: 'Critical SIF Precursors',
      value: sifCount,
      sublabel: `${sifRate}% precursor rate`,
      icon: <ShieldAlert className="w-5 h-5 text-[#D64545]" />,
      tooltip: 'Serious Injury or Fatality exposure hazards identified across safety reports.',
      textColor: 'text-[#D64545]',
      cardClass: 'border-[#D64545]/30 bg-white hover:border-[#D64545] cursor-pointer shadow-sm hover:shadow-md',
      onClick: onFilterSIF,
    },
    {
      title: 'High-Risk Observations',
      value: highRisk,
      sublabel: `${total > 0 ? ((highRisk / total) * 100).toFixed(1) : 0}% of all records`,
      icon: <AlertTriangle className="w-5 h-5 text-[#D64545]" />,
      tooltip: 'Reports classified with elevated consequence or severe potential impact.',
      textColor: 'text-[#D64545]',
      cardClass: 'border-[#D64545]/30 bg-white hover:border-[#D64545] cursor-pointer shadow-sm hover:shadow-md',
      onClick: () => onFilterRisk?.('High'),
    },
    {
      title: 'Overdue Actions',
      value: overdueActions,
      sublabel: `${openActions + inProgressActions} pending remediation`,
      icon: <Clock className="w-5 h-5 text-[#E5A11A]" />,
      tooltip: 'Corrective actions past their target SLA deadline.',
      textColor: overdueActions > 0 ? 'text-[#E5A11A]' : 'text-[#2E8B57]',
      cardClass: 'border-[#E5A11A]/40 bg-white hover:border-[#E5A11A] cursor-pointer shadow-sm hover:shadow-md',
      onClick: () => onFilterStatus?.('Overdue'),
    },
    {
      title: 'Total Safety Reports',
      value: total,
      sublabel: 'Active records ingested',
      icon: <FileText className="w-5 h-5 text-[#1769AA]" />,
      tooltip: 'Total near-miss observations and safety reports analyzed.',
      textColor: 'text-[#172B3A]',
      cardClass: 'border-[#D9E2EA] bg-white shadow-sm',
      onClick: undefined,
    },
  ];

  const secondaryCards = [
    {
      title: 'Medium Risk',
      value: medRisk,
      sublabel: `${total > 0 ? ((medRisk / total) * 100).toFixed(1) : 0}% of records`,
      icon: <AlertCircle className="w-4 h-4 text-[#B87A00]" />,
      textColor: 'text-[#B87A00]',
      onClick: () => onFilterRisk?.('Medium'),
    },
    {
      title: 'Low Risk',
      value: lowRisk,
      sublabel: `${total > 0 ? ((lowRisk / total) * 100).toFixed(1) : 0}% of records`,
      icon: <CheckCircle2 className="w-4 h-4 text-[#2E8B57]" />,
      textColor: 'text-[#2E8B57]',
      onClick: () => onFilterRisk?.('Low'),
    },
    {
      title: 'Closed Actions',
      value: closedActions,
      sublabel: 'Remediated & verified',
      icon: <CheckSquare className="w-4 h-4 text-[#2E8B57]" />,
      textColor: 'text-[#2E8B57]',
      onClick: () => onFilterStatus?.('Closed'),
    },
    {
      title: 'AI Risk Upgrades',
      value: sifSummary?.risk_level_upgrades || 0,
      sublabel: 'Upgraded vs initial log',
      icon: <TrendingUp className="w-4 h-4 text-[#1769AA]" />,
      textColor: 'text-[#1769AA]',
      onClick: undefined,
    },
  ];

  return (
    <div className="space-y-5">
      {/* STEP 1: SAFETY OVERVIEW STATUS BANNER */}
      <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-[#526575] uppercase tracking-wider">
              OVERALL SAFETY STATUS
            </span>
            <InfoTooltip
              title="Safety Status"
              text="Reflects the current overall facility safety condition based on active SIF precursors, high-risk observations, and overdue actions."
            />
          </div>
          <p className="text-sm text-[#172B3A] mt-1 font-semibold">
            {overallText}
          </p>
        </div>
        <div className="shrink-0">
          <span className={`px-3.5 py-1.5 text-xs font-bold rounded-xl border uppercase tracking-wider shadow-xs ${overallBadge}`}>
            {overallStatus}
          </span>
        </div>
      </div>

      {/* STEP 2: WHAT NEEDS ATTENTION? (PRIMARY ACTION CARDS) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        {primaryCards.map((c, i) => (
          <div
            key={i}
            onClick={c.onClick}
            className={`p-5 rounded-2xl border transition-all duration-150 ${c.cardClass} flex flex-col justify-between space-y-2`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1">
                <span className="text-xs font-bold text-[#172B3A]">
                  {c.title}
                </span>
                {c.tooltip && <InfoTooltip text={c.tooltip} />}
              </div>
              <span className="text-lg leading-none">{c.icon}</span>
            </div>

            <div className="flex items-baseline gap-1 my-1">
              <span className={`text-3xl font-black tracking-tight ${c.textColor} tabular-nums`}>
                {c.value}
              </span>
            </div>

            <span className="text-xs text-[#526575] font-medium">
              {c.sublabel}
            </span>
          </div>
        ))}
      </div>

      {/* SECONDARY BREAKDOWN CARDS */}
      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-4">
        {secondaryCards.map((c, i) => (
          <div
            key={i}
            onClick={c.onClick}
            className="p-4 rounded-2xl bg-[#EEF3F7] border border-[#D9E2EA] hover:border-[#1769AA] transition-all cursor-pointer flex items-center justify-between shadow-xs"
          >
            <div>
              <div className="text-[11px] font-bold text-[#526575]">
                {c.title}
              </div>
              <div className={`text-xl font-black ${c.textColor} tabular-nums mt-0.5`}>
                {c.value}
              </div>
              <div className="text-[10px] text-[#718394] font-medium">
                {c.sublabel}
              </div>
            </div>
            <span className="text-lg">{c.icon}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
