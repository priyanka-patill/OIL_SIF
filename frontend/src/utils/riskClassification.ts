/**
 * Centralized Frontend Risk Classification & Normalization Utility.
 * Single source of truth for risk levels across all dashboard components, KPI cards,
 * tables, and report details.
 * 
 * Standard Risk Levels:
 * - HIGH (Red/Orange)
 * - MEDIUM (Amber/Yellow)
 * - LOW (Green)
 * 
 * Note: SIF Precursor (YES/NO) and HiPo Near Miss (YES/NO) are separate independent flags.
 */

export type StandardRiskLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export function classifyRiskFromFields(item?: Record<string, any> | null): StandardRiskLevel {
  if (!item) return 'MEDIUM';

  const desc = String(item.description || item.Observation || item.Near_Miss_Description || '').toLowerCase();
  const consequence = String(item.potential_consequence || item.PotentialConsequence || item.Potential_Consequence || '').toLowerCase();
  const workType = String(item.work_type || item.WorkType || item.Work_Type || '').toLowerCase();

  const highPotential = Boolean(item.high_potential || item.High_Potential_Near_Miss);
  const sifFlag = Boolean(item.sif_precursor || item.SIF_Precursor);

  const highConsequences = [
    'fatality', 'death', 'severe injury', 'lost-time', 'lost time',
    'explosion', 'fire', 'bleve', 'hydrocarbon release', 'gas leak', 'sour gas', 'h2s',
    'toxic', 'toxic release', 'collapse', 'electrocution', 'amputation', 'blowout'
  ];
  const highWorkTypes = [
    'hot work', 'confined space', 'work at height', 'height', 'energy isolation',
    'loto', 'electrical', 'high pressure', 'crane', 'heavy lift', 'line break'
  ];

  const hasHighConsequence = highConsequences.some(kw => consequence.includes(kw) || desc.includes(kw));
  const hasHighWorkType = highWorkTypes.some(kw => workType.includes(kw) || desc.includes(kw));

  let factorsCount = 0;
  if (item.ppe_issue || item.PPE_NonCompliance) factorsCount++;
  if (item.supervisor_factor || item.Supervisor_Negligence) factorsCount++;
  if (item.maintenance_factor || item.Maintenance_Delay_or_Issue) factorsCount++;
  if (item.repeated_issue || item.Repeated_Issue_Ignored) factorsCount++;

  if (hasHighConsequence || (hasHighWorkType && (sifFlag || highPotential || factorsCount >= 2)) || factorsCount >= 3) {
    return 'HIGH';
  }

  const mediumConsequences = [
    'minor injury', 'first aid', 'equipment damage', 'leak', 'spill',
    'degradation', 'corrosion', 'overdue', 'malfunction', 'uncontained', 'exposure'
  ];
  const hasMediumConsequence = mediumConsequences.some(kw => consequence.includes(kw) || desc.includes(kw));

  if (hasMediumConsequence || factorsCount >= 1 || hasHighWorkType || highPotential || sifFlag) {
    return 'MEDIUM';
  }

  return 'LOW';
}

export function normalizeRiskLevel(val?: string | null, fallbackItem?: Record<string, any> | null): StandardRiskLevel {
  if (val && typeof val === 'string' && val.trim() !== '') {
    const cleaned = val.trim().toUpperCase();
    if (cleaned === 'HIGH' || cleaned === 'HIGH RISK' || cleaned.startsWith('HIGH') || cleaned === 'CRITICAL' || cleaned === 'SERIOUS') {
      return 'HIGH';
    }
    if (cleaned === 'MEDIUM' || cleaned === 'MEDIUM RISK' || cleaned.startsWith('MED') || cleaned === 'SIGNIFICANT' || cleaned === 'MODERATE') {
      return 'MEDIUM';
    }
    if (cleaned === 'LOW' || cleaned === 'LOW RISK' || cleaned.startsWith('LOW') || cleaned === 'MINIMAL' || cleaned === 'MINOR') {
      return 'LOW';
    }
  }

  if (fallbackItem) {
    return classifyRiskFromFields(fallbackItem);
  }

  return 'MEDIUM';
}

export function getRiskLabel(val?: string | null, fallbackItem?: Record<string, any> | null): StandardRiskLevel {
  return normalizeRiskLevel(val, fallbackItem);
}

export function getRiskBadgeStyle(val?: string | null): {
  bgClass: string;
  textClass: string;
  borderClass: string;
  dotClass: string;
  hexColor: string;
} {
  const norm = normalizeRiskLevel(val);

  if (norm === 'HIGH') {
    return {
      bgClass: 'bg-[#D64545]/15',
      textClass: 'text-[#D64545]',
      borderClass: 'border-[#D64545]/30',
      dotClass: 'bg-[#D64545] animate-pulse',
      hexColor: '#D64545',
    };
  }

  if (norm === 'MEDIUM') {
    return {
      bgClass: 'bg-[#E5A11A]/15',
      textClass: 'text-[#B87A00]',
      borderClass: 'border-[#E5A11A]/40',
      dotClass: 'bg-[#E5A11A]',
      hexColor: '#E5A11A',
    };
  }

  return {
    bgClass: 'bg-[#2E8B57]/15',
    textClass: 'text-[#2E8B57]',
    borderClass: 'border-[#2E8E57]/30',
    dotClass: 'bg-[#2E8B57]',
    hexColor: '#2E8B57',
  };
}

export function calculateRiskCounts(reports: Array<{ risk_level?: string | null }>): {
  HIGH: number;
  MEDIUM: number;
  LOW: number;
  total: number;
} {
  let high = 0;
  let medium = 0;
  let low = 0;

  reports.forEach((r) => {
    const norm = normalizeRiskLevel(r.risk_level);
    if (norm === 'HIGH') high++;
    else if (norm === 'MEDIUM') medium++;
    else if (norm === 'LOW') low++;
  });

  return {
    HIGH: high,
    MEDIUM: medium,
    LOW: low,
    total: reports.length,
  };
}
