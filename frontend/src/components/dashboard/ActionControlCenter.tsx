import React, { useState, useEffect } from 'react';
import { SLADashboardResponse, SLAActionItemResponse } from '../../types/safety';
import { api } from '../../services/api';
import { InfoTooltip } from '../common/InfoTooltip';

interface ActionControlCenterProps {
  onViewAction?: (actionId: string) => void;
  onViewReport?: (reportId: string) => void;
}

export const ActionControlCenter: React.FC<ActionControlCenterProps> = ({
  onViewAction,
  onViewReport,
}) => {
  const [dashboard, setDashboard] = useState<SLADashboardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [acknowledgingId, setAcknowledgingId] = useState<string | null>(null);

  const fetchDashboard = () => {
    api.getSLADashboard()
      .then(setDashboard)
      .catch(() => setDashboard(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleAcknowledge = async (actionId: string) => {
    setAcknowledgingId(actionId);
    try {
      await api.acknowledgeAction(actionId, {
        actor_name: 'Control Room Duty Officer',
        actor_role: 'Unit In-Charge',
        comments: 'Acknowledged via Action Control Center Dashboard'
      });
      fetchDashboard();
    } catch (err) {
      console.error('Failed to acknowledge action:', err);
    } finally {
      setAcknowledgingId(null);
    }
  };

  if (loading) {
    return (
      <div className="bg-white border border-[#D9E2EA] rounded-2xl p-6 animate-pulse space-y-4 shadow-sm">
        <div className="h-5 w-48 bg-[#EEF3F7] rounded"></div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 bg-[#EEF3F7] rounded-xl"></div>
          ))}
        </div>
      </div>
    );
  }

  const data = dashboard || {
    critical_open: 0,
    awaiting_acknowledgement: 0,
    approaching_sla: 0,
    sla_breached: 0,
    escalated: 0,
    contained: 0,
    awaiting_verification: 0,
    closed: 0,
    total_active_actions: 0,
    active_actions: []
  };

  const metricCards = [
    { label: 'CRITICAL', count: data.critical_open, color: 'text-[#D64545]', border: 'border-[#D64545]/30 bg-[#D64545]/10 font-bold', tooltip: 'Critical safety issues requiring immediate containment' },
    { label: 'HIGH PRIORITY', count: data.approaching_sla + data.escalated, color: 'text-[#E67E22]', border: 'border-[#E67E22]/30 bg-[#E67E22]/10 font-bold', tooltip: 'High priority actions approaching deadline or escalated' },
    { label: 'PENDING', count: data.awaiting_acknowledgement, color: 'text-[#B87A00]', border: 'border-[#E5A11A]/30 bg-[#E5A11A]/10 font-bold', tooltip: 'Actions awaiting initial supervisor acknowledgment' },
    { label: 'OVERDUE', count: data.sla_breached, color: 'text-[#D64545]', border: 'border-[#D64545]/30 bg-[#D64545]/10 font-bold', tooltip: 'Actions past target resolution deadline' },
    { label: 'COMPLETED', count: data.closed, color: 'text-[#2E8B57]', border: 'border-[#2E8B57]/30 bg-[#2E8B57]/10 font-bold', tooltip: 'Successfully remediated and closed action items' },
  ];

  return (
    <div className="bg-white border border-[#D9E2EA] rounded-2xl p-6 shadow-sm space-y-5">
      {/* Title */}
      <div className="flex items-center justify-between pb-3 border-b border-[#D9E2EA]">
        <div>
          <div className="flex items-center gap-1.5">
            <h3 className="text-sm font-bold text-[#172B3A]">
              Action Remediation & Governance Center
            </h3>
            <InfoTooltip
              title="Action Center"
              text="Tracks corrective safety actions, target resolution deadlines, and escalation status."
            />
          </div>
          <p className="text-xs text-[#526575] mt-0.5 font-medium">
            What needs action? Who is responsible? How urgent is it?
          </p>
        </div>
        <span className="text-xs text-[#718394] font-semibold">
          Auto-updated • Standard 60m SLA Active
        </span>
      </div>

      {/* Categories KPI Row */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {metricCards.map((m, idx) => (
          <div key={idx} className={`p-3.5 rounded-xl border ${m.border} flex flex-col justify-between text-center shadow-xs`}>
            <div className="flex items-center justify-center gap-1 mb-1">
              <span className="text-[10px] font-bold text-[#172B3A] uppercase tracking-wider">
                {m.label}
              </span>
              <InfoTooltip text={m.tooltip} />
            </div>
            <div className={`text-2xl font-black ${m.color} tabular-nums`}>
              {m.count}
            </div>
          </div>
        ))}
      </div>

      {/* Active Actions Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold text-[#172B3A] uppercase tracking-wider">
            Active Safety Action Items ({data.active_actions.length})
          </h4>
          <span className="text-xs text-[#718394] font-medium">Task-oriented priority queue</span>
        </div>

        {data.active_actions.length === 0 ? (
          <div className="py-6 text-center text-[#526575] text-xs border border-dashed border-[#D9E2EA] rounded-xl font-medium bg-[#EEF3F7]">
            No pending safety actions requiring immediate attention.
          </div>
        ) : (
          <div className="overflow-x-auto custom-scrollbar">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#D9E2EA] bg-[#EEF3F7] text-[#526575] text-[11px] uppercase font-bold">
                  <th className="py-2.5 px-3 rounded-l-lg">What Needs Action?</th>
                  <th className="py-2.5 px-3">Who Is Responsible?</th>
                  <th className="py-2.5 px-3">How Urgent?</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right rounded-r-lg">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D9E2EA]">
                {data.active_actions.slice(0, 5).map((act: SLAActionItemResponse) => {
                  const isBreached = act.formatted_countdown.startsWith('BREACHED');
                  return (
                    <tr key={act.action_id} className="hover:bg-[#EEF3F7]/50 transition-colors">
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 text-[10px] font-bold rounded-md ${
                              act.severity === 'CRITICAL'
                                ? 'bg-[#D64545]/15 text-[#D64545] border border-[#D64545]/30'
                                : act.severity === 'HIGH'
                                ? 'bg-[#E67E22]/15 text-[#E67E22] border border-[#E67E22]/30'
                                : 'bg-[#1769AA]/15 text-[#1769AA] border border-[#1769AA]/30'
                            }`}
                          >
                            {act.severity}
                          </span>
                          <span className="text-[#172B3A] font-bold truncate max-w-[240px]">
                            {act.title}
                          </span>
                        </div>
                        <div className="text-[10px] text-[#718394] font-medium mt-0.5">
                          Report ID: {act.report_id}
                        </div>
                      </td>

                      <td className="py-3 px-3">
                        <span className="text-[#1769AA] font-bold">{act.assigned_role}</span>
                        {act.escalation_level > 0 && (
                          <span className="ml-1.5 px-1.5 py-0.5 text-[9px] bg-purple-100 text-purple-800 border border-purple-200 rounded font-bold">
                            Level {act.escalation_level} Escalation
                          </span>
                        )}
                      </td>

                      <td className="py-3 px-3">
                        <span
                          className={`font-mono text-xs ${
                            isBreached ? 'text-[#D64545] font-extrabold animate-pulse' : 'text-[#B87A00] font-bold'
                          }`}
                        >
                           {act.formatted_countdown}
                        </span>
                      </td>

                      <td className="py-3 px-3">
                        <span className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-[#EEF3F7] border border-[#D9E2EA] text-[#172B3A]">
                          {act.sla_state}
                        </span>
                      </td>

                      <td className="py-3 px-3 text-right space-x-2">
                        {!act.acknowledged_at && (
                          <button
                            type="button"
                            disabled={acknowledgingId === act.action_id}
                            onClick={() => handleAcknowledge(act.action_id)}
                            className="px-3 py-1 bg-[#2E8B57]/15 hover:bg-[#2E8B57]/30 border border-[#2E8B57]/40 text-[#2E8B57] rounded-lg text-xs font-bold transition-colors shadow-xs"
                          >
                            {acknowledgingId === act.action_id ? '...' : 'Acknowledge'}
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => onViewAction && onViewAction(act.action_id)}
                          className="px-3 py-1 bg-white hover:bg-[#EEF3F7] border border-[#D9E2EA] text-[#172B3A] rounded-lg text-xs font-bold transition-colors shadow-xs"
                        >
                          View Action
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
