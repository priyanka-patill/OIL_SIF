import React, { useState, useEffect } from 'react';
import { AuditTimelineResponse, AuditTimelineEvent } from '../../types/safety';
import { api } from '../../services/api';

interface AuditTimelineViewProps {
  reportId?: string;
  actionId?: string;
}

export const AuditTimelineView: React.FC<AuditTimelineViewProps> = ({ reportId, actionId }) => {
  const [timeline, setTimeline] = useState<AuditTimelineResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);

  const fetchTimeline = async () => {
    setLoading(true);
    try {
      if (reportId) {
        const data = await api.getReportAuditTimeline(reportId);
        setTimeline(data);
      } else if (actionId) {
        const data = await api.getActionAuditTimeline(actionId);
        setTimeline(data);
      }
    } catch (err) {
      console.error('Failed to load audit timeline:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (reportId || actionId) {
      fetchTimeline();
    }
  }, [reportId, actionId]);

  const getEventBadgeColor = (eventType: string) => {
    switch (eventType) {
      case 'DETECTION':
        return 'bg-blue-50 text-blue-800 border-blue-200';
      case 'CORRELATION':
        return 'bg-blue-50 text-blue-800 border-blue-200';
      case 'BARRIER_ASSESSMENT':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'BDI_CALCULATION':
        return 'bg-purple-50 text-purple-800 border-purple-200';
      case 'SIF_ESCALATION':
        return 'bg-rose-50 text-rose-800 border-rose-200 font-bold animate-pulse';
      case 'ACTION_CREATION':
        return 'bg-indigo-50 text-indigo-800 border-indigo-200';
      case 'SAFETY_HOLD':
        return 'bg-red-50 text-red-800 border-red-200 font-bold';
      case 'SLA_BREACH':
      case 'ESCALATION':
        return 'bg-rose-50 text-rose-800 border-rose-200';
      case 'ACKNOWLEDGEMENT':
      case 'CONTAINMENT':
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
      case 'VERIFICATION':
      case 'CLOSURE':
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
      case 'HUMAN_FEEDBACK':
        return 'bg-purple-50 text-purple-800 border-purple-200';
      default:
        return 'bg-[#EEF3F7] text-[#526575] border-[#D9E2EA]';
    }
  };

  return (
    <div className="bg-white border border-[#D9E2EA] rounded-2xl p-5 space-y-4 shadow-sm">
      <div className="flex items-center justify-between border-b border-[#D9E2EA] pb-3">
        <div>
          <h3 className="text-xs font-mono font-bold text-[#172B3A] uppercase tracking-wider flex items-center gap-2">
            Immutable Platform Audit Trail Timeline
          </h3>
          <p className="text-[11px] font-sans text-[#526575]">
            Chronological audit log stream verifying lifecycle integrity and human decisions.
          </p>
        </div>
        <button
          onClick={fetchTimeline}
          disabled={loading}
          className="px-2.5 py-1 bg-[#EEF3F7] hover:bg-slate-200 text-[#172B3A] border border-[#D9E2EA] rounded-lg text-xs font-mono transition-colors"
        >
          {loading ? 'Refreshing...' : ' Refresh Stream'}
        </button>
      </div>

      {loading ? (
        <div className="py-12 text-center text-xs font-mono text-[#1769AA] animate-pulse">
          Loading audit events timeline...
        </div>
      ) : !timeline || timeline.events.length === 0 ? (
        <div className="py-12 text-center text-xs font-mono text-[#718394]">
          No audit events recorded for this entity yet.
        </div>
      ) : (
        <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#D9E2EA]">
          {timeline.events.map((evt) => {
            const isExpanded = expandedEventId === evt.event_id;
            return (
              <div key={evt.event_id} className="relative group">
                {/* Timeline node dot */}
                <div className={`absolute -left-6 top-1.5 w-4 h-4 rounded-full border-2 bg-white flex items-center justify-center transition-all ${
                  evt.severity === 'CRITICAL' ? 'border-rose-600 scale-110 shadow-sm' : 'border-[#1769AA]'
                }`}>
                  <div className={`w-1.5 h-1.5 rounded-full ${evt.severity === 'CRITICAL' ? 'bg-rose-600 animate-ping' : 'bg-[#1769AA]'}`} />
                </div>

                <div className="bg-[#F4F7FA] border border-[#D9E2EA] rounded-xl p-3.5 space-y-2 hover:border-[#1769AA]/40 transition-all shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getEventBadgeColor(evt.event_type)}`}>
                        {evt.event_type}
                      </span>
                      {evt.is_simulated && (
                        <span className="px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 text-[9px] font-bold">
                          SIMULATED
                        </span>
                      )}
                      <span className="font-bold text-[#172B3A]">{evt.title}</span>
                    </div>
                    <span className="text-[#718394] text-[11px]">{evt.formatted_time}</span>
                  </div>

                  <p className="text-xs font-sans text-[#526575]">
                    {evt.description}
                  </p>

                  <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-[#D9E2EA] text-[11px] font-mono text-[#526575]">
                    <div className="flex items-center gap-3">
                      <span>Actor: <strong className="text-[#172B3A]">{evt.actor}</strong></span>
                      {evt.bdi !== null && evt.bdi !== undefined && (
                        <span>BDI: <strong className="text-[#E5A11A]">{evt.bdi.toFixed(1)}</strong></span>
                      )}
                      {evt.sif_status && (
                        <span>SIF: <strong className={evt.sif_status === 'YES' ? 'text-rose-700' : 'text-[#718394]'}>{evt.sif_status}</strong></span>
                      )}
                    </div>

                    {evt.evidence && Object.keys(evt.evidence).length > 0 && (
                      <button
                        onClick={() => setExpandedEventId(isExpanded ? null : evt.event_id)}
                        className="text-[#1769AA] hover:underline text-[10px] font-bold"
                      >
                        {isExpanded ? 'Hide Payload' : 'View Payload Details'}
                      </button>
                    )}
                  </div>

                  {isExpanded && evt.evidence && (
                    <div className="mt-2 bg-white rounded-lg p-2.5 border border-[#D9E2EA] text-[10px] font-mono text-[#172B3A] max-h-48 overflow-y-auto shadow-inner">
                      <pre className="whitespace-pre-wrap">{JSON.stringify(evt.evidence, null, 2)}</pre>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

