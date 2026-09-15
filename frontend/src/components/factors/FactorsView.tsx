import React, { useState, useEffect } from 'react';
import { FactorSummaryData, FactorCombinationsData, HighPotentialIntelligenceData } from '../../types/safety';
import { api } from '../../services/api';

interface FactorsViewProps {
  onOpenReport?: (reportId: string) => void;
}

export const FactorsView: React.FC<FactorsViewProps> = () => {
  const [summary, setSummary] = useState<FactorSummaryData | null>(null);
  const [combinations, setCombinations] = useState<FactorCombinationsData | null>(null);
  const [hipo, setHipo] = useState<HighPotentialIntelligenceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'combinations' | 'hipo' | 'summary'>('combinations');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getFactorSummary(),
      api.getFactorCombinations(),
      api.getHighPotentialIntelligence(),
    ])
      .then(([sumData, combData, hipoData]) => {
        setSummary(sumData);
        setCombinations(combData);
        setHipo(hipoData);
      })
      .catch((err) => console.error('Error fetching factor intelligence:', err))
      .finally(() => setLoading(false));
  }, []);

  const getDangerBadge = (level: string) => {
    const l = (level || 'LOW').toUpperCase();
    if (l === 'CRITICAL') {
      return (
        <span className="px-2.5 py-1 rounded bg-rose-100 text-rose-800 border border-rose-300 text-[10px] font-mono font-bold uppercase animate-pulse">
          CRITICAL DANGER
        </span>
      );
    }
    if (l === 'HIGH') {
      return (
        <span className="px-2.5 py-1 rounded bg-rose-50 text-rose-700 border border-rose-200 text-[10px] font-mono font-bold uppercase">
          HIGH DANGER
        </span>
      );
    }
    if (l === 'MODERATE') {
      return (
        <span className="px-2.5 py-1 rounded bg-amber-50 text-amber-800 border border-amber-200 text-[10px] font-mono font-bold uppercase">
          MODERATE DANGER
        </span>
      );
    }
    return (
      <span className="px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-mono font-bold uppercase">
        LOW DANGER
      </span>
    );
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-xs font-mono text-[#1769AA] space-y-2">
        <div className="animate-spin text-2xl"></div>
        <p>Loading multi-factor safety intelligence & compound danger models...</p>
      </div>
    );
  }

  const tiers = combinations ? [1, 2, 3, 4].map((count) => {
    const matching = (combinations.combinations || []).filter((c) => c.factor_count === count);
    const totalReports = count === 1 ? combinations.level_1_count : count === 2 ? combinations.level_2_count : count === 3 ? combinations.level_3_count : combinations.level_4_count;
    const highRisk = matching.reduce((sum, c) => sum + c.high_risk_count, 0);
    const hipoCnt = matching.reduce((sum, c) => sum + c.high_potential_count, 0);
    const highRiskPct = totalReports > 0 ? Math.round((highRisk / totalReports) * 100) : 0;
    const avgDanger = matching.length > 0 ? Math.round(matching.reduce((sum, c) => sum + c.danger_score, 0) / matching.length) : (count * 25);
    const dangerLevel = count === 4 ? 'CRITICAL' : count === 3 ? 'HIGH' : count === 2 ? 'MODERATE' : 'LOW';
    const label = count === 4 ? '4-Factor Compound Failure' : count === 3 ? '3-Factor Escalation' : count === 2 ? '2-Factor Co-Occurrence' : 'Single Isolated Factor';

    return {
      factor_count: count,
      factor_label: label,
      total_reports: totalReports,
      high_risk_reports: highRisk,
      high_risk_percentage: highRiskPct,
      sif_precursor_count: hipoCnt,
      danger_score: avgDanger,
      danger_level: dangerLevel,
    };
  }) : [];

  return (
    <div className="space-y-6 text-[#172B3A]">
      {/* Header */}
      <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl"></span>
            <h2 className="text-base font-mono font-bold text-[#172B3A] uppercase tracking-wider">
              Safety Factor & Combination Intelligence
            </h2>
          </div>
          <p className="text-xs font-sans text-[#526575] max-w-3xl">
            Empirical multi-factor analysis demonstrating how non-compliance risk escalates non-linearly when 
            PPE violations combine with Supervisor Negligence, Maintenance Delays, and Recurring Systemic Defects.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-white px-4 py-2 rounded-xl border border-[#D9E2EA] text-center shadow-sm">
            <span className="text-[10px] font-mono text-[#718394] uppercase block font-semibold">ANALYZED FACTORS</span>
            <span className="text-xl font-mono font-bold text-[#1769AA]">4 PRIMARY</span>
          </div>
          <div className="bg-white px-4 py-2 rounded-xl border border-[#D9E2EA] text-center shadow-sm">
            <span className="text-[10px] font-mono text-[#718394] uppercase block font-semibold">HIGHEST DANGER</span>
            <span className="text-xl font-mono font-bold text-rose-600">4-FACTOR TIER</span>
          </div>
        </div>
      </div>

      {/* Navigation Subtabs */}
      <div className="flex items-center gap-2 border-b border-[#D9E2EA] pb-3">
        <button
          onClick={() => setActiveTab('combinations')}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${
            activeTab === 'combinations' ? 'bg-[#1769AA] text-white font-bold shadow-sm' : 'text-[#526575] hover:text-[#172B3A]'
          }`}
        >
          Factor Compounding & Danger Matrix
        </button>
        <button
          onClick={() => setActiveTab('hipo')}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${
            activeTab === 'hipo' ? 'bg-[#1769AA] text-white font-bold shadow-sm' : 'text-[#526575] hover:text-[#172B3A]'
          }`}
        >
          High-Potential (HiPo) Intelligence ({hipo?.total_high_potential_incidents || 0})
        </button>
        <button
          onClick={() => setActiveTab('summary')}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${
            activeTab === 'summary' ? 'bg-[#1769AA] text-white font-bold shadow-sm' : 'text-[#526575] hover:text-[#172B3A]'
          }`}
        >
          Individual Factor Prevalence
        </button>
      </div>

      {/* TAB 1: COMBINATIONS & DANGER MATRIX */}
      {activeTab === 'combinations' && combinations && (
        <div className="space-y-6">
          {/* 4-Tier Compounding Escalation Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {tiers.map((tier) => (
              <div
                key={tier.factor_count}
                className={`p-5 rounded-2xl border flex flex-col justify-between transition-all shadow-sm ${
                  tier.factor_count === 4
                    ? 'bg-rose-50/60 border-rose-300'
                    : tier.factor_count === 3
                    ? 'bg-rose-50/40 border-rose-200'
                    : tier.factor_count === 2
                    ? 'bg-amber-50/40 border-amber-200'
                    : 'bg-white border-[#D9E2EA]'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono uppercase tracking-widest text-[#526575] font-bold">
                      {tier.factor_label}
                    </span>
                    {getDangerBadge(tier.danger_level)}
                  </div>
                  <div className="text-2xl font-mono font-bold text-[#172B3A] mb-1">
                    {tier.total_reports} <span className="text-xs font-normal text-[#718394]">Reports</span>
                  </div>
                </div>

                <div className="space-y-2 pt-3 border-t border-[#D9E2EA] text-xs font-mono">
                  <div className="flex justify-between">
                    <span className="text-[#718394]">High Risk Rate:</span>
                    <strong className={tier.high_risk_percentage > 50 ? 'text-rose-600 font-bold' : 'text-[#172B3A]'}>
                      {tier.high_risk_percentage}% ({tier.high_risk_reports})
                    </strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#718394]">SIF Precursors:</span>
                    <strong className="text-rose-600 font-bold">{tier.sif_precursor_count}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#718394]">Danger Score:</span>
                    <strong className="text-[#1769AA] font-bold">{tier.danger_score} / 100</strong>
                  </div>

                  {/* Progress bar */}
                  <div className="h-1.5 w-full bg-[#EEF3F7] rounded-full overflow-hidden mt-1">
                    <div
                      style={{ width: `${tier.danger_score}%` }}
                      className={`h-full rounded-full ${
                        tier.factor_count === 4
                          ? 'bg-rose-600'
                          : tier.factor_count === 3
                          ? 'bg-rose-500'
                          : tier.factor_count === 2
                          ? 'bg-amber-500'
                          : 'bg-emerald-500'
                      }`}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* AI Danger Rankings Table */}
          <div className="bg-white border border-[#D9E2EA] rounded-2xl p-6 space-y-4 shadow-sm">
            <div>
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] flex items-center gap-2">
                Compound Danger Rankings Across Factor Combinations
              </h3>
              <p className="text-xs font-sans text-[#526575]">
                Mathematical multi-barrier failure escalation model ranking active refinery risk density.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#EEF3F7] text-[#526575] uppercase text-[10px] border-b border-[#D9E2EA]">
                  <tr>
                    <th className="p-3">Rank</th>
                    <th className="p-3">Combination Tier</th>
                    <th className="p-3">Factors Included</th>
                    <th className="p-3 text-center">Reports</th>
                    <th className="p-3 text-center">High Risk %</th>
                    <th className="p-3 text-center">SIF Precursors</th>
                    <th className="p-3 text-center">Danger Score</th>
                    <th className="p-3 text-right">Assessment</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#D9E2EA]">
                  {combinations.danger_ranked_combinations.map((rank, index) => (
                    <tr key={rank.combination_key} className="hover:bg-[#F4F7FA] transition-colors">
                      <td className="p-3 font-bold text-[#1769AA]">#{index + 1}</td>
                      <td className="p-3 font-bold text-[#172B3A]">{rank.combination_key}</td>
                      <td className="p-3">
                        <div className="flex flex-wrap gap-1">
                          {rank.factor_names.map((f, i) => (
                            <span key={i} className="px-1.5 py-0.5 rounded bg-[#EEF3F7] border border-[#D9E2EA] text-[#172B3A] text-[10px]">
                              {f}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="p-3 text-center text-[#172B3A] font-bold">{rank.report_count}</td>
                      <td className="p-3 text-center">
                        <span className={`font-bold ${rank.high_risk_ratio > 0.5 ? 'text-rose-600' : 'text-[#172B3A]'}`}>
                          {Math.round(rank.high_risk_ratio * 100)}%
                        </span>
                      </td>
                      <td className="p-3 text-center text-rose-600 font-bold">{rank.high_potential_count}</td>
                      <td className="p-3 text-center font-bold text-[#1769AA]">{rank.danger_score}/100</td>
                      <td className="p-3 text-right">{getDangerBadge(rank.danger_level)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: HIGH-POTENTIAL (HIPO) INTELLIGENCE */}
      {activeTab === 'hipo' && hipo && (
        <div className="space-y-6">
          {/* HiPo Overview Card */}
          <div className="bg-gradient-to-r from-rose-50 via-white to-blue-50 border border-rose-200 rounded-2xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-sm">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="h-2.5 w-2.5 rounded-full bg-rose-600 animate-ping" />
                <h3 className="text-base font-mono font-bold text-rose-900 uppercase tracking-wider">
                  Dedicated High-Potential (HiPo) Incident Telemetry
                </h3>
              </div>
              <p className="text-xs font-sans text-[#526575] max-w-2xl">
                Analysis of {hipo.total_high_potential_incidents} operational near-miss events where multiple defense barriers were simultaneously compromised, 
                presenting immediate catastrophic release or fatality potential.
              </p>
            </div>

            <div className="flex items-center gap-4 text-center">
              <div className="bg-white px-4 py-2.5 rounded-xl border border-[#D9E2EA] shadow-sm">
                <span className="text-[10px] font-mono text-[#718394] uppercase block font-semibold">RECORDED HIGH/CRITICAL</span>
                <span className="text-2xl font-mono font-extrabold text-rose-600">
                  {Math.round(((hipo.critical_risk_count + hipo.high_risk_count) / (hipo.total_high_potential_incidents || 1)) * 100)}%
                </span>
              </div>
              <div className="bg-white px-4 py-2.5 rounded-xl border border-[#D9E2EA] shadow-sm">
                <span className="text-[10px] font-mono text-[#718394] uppercase block font-semibold">MULTI-BARRIER FAILURE RATE</span>
                <span className="text-2xl font-mono font-extrabold text-rose-800">
                  {Math.round((hipo.multi_barrier_failure_count / (hipo.total_high_potential_incidents || 1)) * 100)}%
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Root Causes */}
            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-4 shadow-sm">
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-rose-600" />
                Top High-Potential Root Causes
              </h4>
              <div className="space-y-2 text-xs font-mono">
                {hipo.top_immediate_causes.slice(0, 6).map((item) => (
                  <div key={item.cause} className="flex items-center justify-between p-2.5 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA]">
                    <span className="text-[#172B3A] font-medium truncate max-w-[80%]">{item.cause}</span>
                    <span className="text-rose-600 font-bold">{item.count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Potential Consequences */}
            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-4 shadow-sm">
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-[#172B3A] flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-rose-600" />
                Top High-Potential Consequences
              </h4>
              <div className="space-y-2 text-xs font-mono">
                {hipo.top_potential_consequences.slice(0, 6).map((item) => (
                  <div key={item.consequence} className="flex items-center justify-between p-2.5 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA]">
                    <span className="text-[#172B3A] font-medium truncate max-w-[80%]">{item.consequence}</span>
                    <span className="text-rose-600 font-bold">{item.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Key Failure Patterns & Imperatives */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-3 shadow-sm">
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-[#1769AA] flex items-center gap-2">
                Key Failure Patterns
              </h4>
              <div className="space-y-2 text-xs font-sans text-[#172B3A]">
                {hipo.key_failure_patterns.map((pat, i) => (
                  <div key={i} className="p-3 rounded-lg bg-[#F4F7FA] border border-[#D9E2EA] space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-[#1769AA]">{pat.pattern_name}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-300 font-bold">{pat.severity_rating}</span>
                    </div>
                    <div className="text-[11px] text-[#526575]">
                      Incident Count: <strong className="text-[#172B3A]">{pat.incident_count}</strong> | Factors: {pat.factor_combination.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-3 shadow-sm">
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-[#2E8B57] flex items-center gap-2">
                Proactive Engineering Imperatives
              </h4>
              <ul className="space-y-2 text-xs font-sans text-[#172B3A]">
                {hipo.preventive_imperatives.map((imp, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-[#2E8B57] font-bold mt-0.5"></span>
                    <span>{imp}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: INDIVIDUAL FACTOR SUMMARY */}
      {activeTab === 'summary' && summary && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {summary.factors.map((f) => (
              <div key={f.factor_name} className="p-5 rounded-2xl bg-white border border-[#D9E2EA] space-y-3 shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-[#172B3A]">{f.display_name || f.factor_name}</span>
                  <span className="px-2 py-0.5 rounded bg-blue-50 text-[#1769AA] border border-blue-200 text-[10px] font-mono font-bold">
                    {f.percentage}%
                  </span>
                </div>
                <div className="text-2xl font-mono font-bold text-[#1769AA]">
                  {f.total_count} <span className="text-xs text-[#718394] font-normal">Reports</span>
                </div>
                <div className="space-y-1 text-xs font-mono pt-2 border-t border-[#D9E2EA]">
                  <div className="flex justify-between text-[#526575]">
                    <span>High Risk Rate:</span>
                    <strong className="text-rose-600 font-bold">
                      {f.total_count > 0 ? Math.round((f.high_risk_count / f.total_count) * 100) : 0}% ({f.high_risk_count})
                    </strong>
                  </div>
                  <div className="flex justify-between text-[#526575]">
                    <span>High Potential:</span>
                    <strong className="text-rose-600 font-bold">{f.high_potential_count}</strong>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
