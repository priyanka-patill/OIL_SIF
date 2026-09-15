import React, { useState, useRef, useEffect } from 'react';
import { api } from '../../services/api';

interface Message {
  sender: 'user' | 'ai';
  text: string;
  suggestedActions?: string[];
  relevantReports?: any[];
  category?: string;
  timestamp: string;
}

interface AISafetyChatProps {
  onOpenReport: (reportId: string) => void;
  datasetId?: string;
  initialQuery?: string;
  onClearInitialQuery?: () => void;
}

export const AISafetyChat: React.FC<AISafetyChatProps> = ({
  onOpenReport,
  datasetId,
  initialQuery,
  onClearInitialQuery,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'ai',
      text: "### OIL Safety Intelligence Assistant\n\nI am directly connected to the **OIL Safety Intelligence Platform Database** with strict zero-hallucination and evidence grounding.\n\nAll metrics, Barrier Degradation (BDI) scores, Swiss Cheese layer defense states, SIF precursor escalation pathways, safety actions, and SLA deadlines are queried directly from live database tables.\n\nTry asking any of the intelligence inquiries below:",
      suggestedActions: [
        "Show critical SIF precursors.",
        "Why is BDI high?",
        "Which refinery units have the highest BDI?",
        "Which barriers are degraded?",
        "Which reports are correlated?",
        "Which factors are converging?",
        "Which actions breached SLA?",
        "Show active safety holds.",
        "Summarize the current safety situation."
      ],
      category: "SYSTEM",
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle incoming initialQuery from Dashboard or modals
  useEffect(() => {
    if (initialQuery && initialQuery.trim()) {
      handleSend(initialQuery);
      onClearInitialQuery?.();
    }
  }, [initialQuery]);

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMsg: Message = {
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.sendChatMessage(query, undefined, datasetId);
      const aiMsg: Message = {
        sender: 'ai',
        text: res.reply,
        suggestedActions: res.suggested_actions,
        relevantReports: res.relevant_reports,
        category: res.category,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'ai',
          text: ` Query failed: ${err.message}`,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const sampleQueries = [
    { label: " Critical SIF", q: "Show critical SIF precursors." },
    { label: " BDI Summary", q: "Explain BDI and summarize barrier degradation." },
    { label: " High BDI Units", q: "Which refinery units have the highest BDI?" },
    { label: " Degraded Barriers", q: "Which safety barriers are degraded or failed?" },
    { label: " Correlated Reports", q: "Which reports are correlated?" },
    { label: " Converging Factors", q: "Which factors are converging?" },
    { label: " SLA Breaches", q: "Which actions breached SLA?" },
    { label: " Safety Holds", q: "Show actions awaiting acknowledgement and active safety holds." },
    { label: " Recurring Equipment", q: "Which equipment has repeated barrier degradation?" },
    { label: " High-Potential", q: "Show high-potential near-miss reports." },
    { label: " Open Actions", q: "Which reports are open?" },
    { label: " Overview", q: "Summarize the current safety situation." },
  ];

  // Helper for Category Badges
  const getCategoryBadge = (cat?: string) => {
    switch (cat?.toUpperCase()) {
      case 'SIF_PRECURSOR_SUMMARY':
      case 'SIF_ESCALATION':
        return { label: 'SIF PRECURSOR ESCALATION', color: 'bg-rose-50 text-rose-800 border-rose-200' };
      case 'BDI_SUMMARY':
      case 'BDI_UNITS':
      case 'BDI_ANALYSIS':
        return { label: 'ANALYTICAL INDICATOR (BDI)', color: 'bg-purple-50 text-purple-800 border-purple-200' };
      case 'BARRIER_SUMMARY':
      case 'BARRIER_DEFENSE':
        return { label: 'SWISS CHEESE BARRIERS', color: 'bg-amber-50 text-amber-800 border-amber-200' };
      case 'SLA_BREACHES':
      case 'ACTION_ESCALATIONS':
      case 'SAFETY_HOLDS':
        return { label: 'SLA & ACTION GOVERNANCE', color: 'bg-blue-50 text-blue-800 border-blue-200' };
      case 'CORRELATIONS':
      case 'CONVERGING_FACTORS':
        return { label: 'MULTI-FACTOR CONVERGENCE', color: 'bg-indigo-50 text-indigo-800 border-indigo-200' };
      default:
        return { label: 'DATABASE GROUNDED', color: 'bg-emerald-50 text-emerald-800 border-emerald-200' };
    }
  };

  return (
    <div className="bg-white border border-[#D9E2EA] rounded-2xl flex flex-col h-[780px] overflow-hidden shadow-md">
      {/* Chat Header */}
      <div className="p-4 border-b border-[#D9E2EA] bg-[#EEF3F7] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-[#1769AA] flex items-center justify-center font-bold text-white shadow-sm text-lg">
            
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xs font-mono font-bold text-[#172B3A] uppercase tracking-wider">
                OIL Safety Intelligence Assistant
              </h2>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">
                GROUNDED IN DATABASE
              </span>
            </div>
            <p className="text-[11px] font-sans text-[#1769AA]">
              Zero-Hallucination SQL & Analytical Models • Swiss Cheese Barriers • BDI • SIF Escalation • SLA Governance
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono px-2 py-1 rounded bg-white text-[#526575] border border-[#D9E2EA]">
            PHASE 1–7 TELEMETRY ACTIVE
          </span>
        </div>
      </div>

      {/* Preset Quick Query Bar */}
      <div className="p-2.5 bg-[#F4F7FA] border-b border-[#D9E2EA] flex items-center gap-1.5 overflow-x-auto custom-scrollbar text-[11px] font-mono">
        <span className="text-[#718394] text-[10px] uppercase font-bold shrink-0 px-1">QUICK INQUIRIES:</span>
        {sampleQueries.map((item, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(item.q)}
            className="px-2.5 py-1 rounded-lg bg-white hover:bg-[#EEF3F7] text-[#172B3A] hover:text-[#1769AA] border border-[#D9E2EA] hover:border-[#1769AA]/40 shrink-0 transition-all text-[11px] shadow-sm"
          >
            {item.label}
          </button>
        ))}
      </div>

      {/* Messages Thread */}
      <div className="flex-1 p-5 overflow-y-auto custom-scrollbar space-y-4 bg-white">
        {messages.map((m, idx) => {
          const catBadge = m.sender === 'ai' ? getCategoryBadge(m.category) : null;
          return (
            <div
              key={idx}
              className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-3xl rounded-xl p-4 text-xs font-sans leading-relaxed ${
                  m.sender === 'user'
                    ? 'bg-[#1769AA] text-white shadow-sm rounded-br-none font-medium'
                    : 'bg-[#F4F7FA] border border-[#D9E2EA] text-[#172B3A] rounded-bl-none shadow-sm'
                }`}
              >
                {/* Category Badge for AI */}
                {catBadge && (
                  <div className="mb-2 pb-1.5 border-b border-[#D9E2EA] flex items-center justify-between">
                    <span className={`text-[9px] font-mono px-2 py-0.5 rounded font-bold border ${catBadge.color}`}>
                      {catBadge.label}
                    </span>
                    <span className="text-[10px] font-mono text-[#718394]">
                      LIVE ORM EVIDENCE
                    </span>
                  </div>
                )}

                <div className="whitespace-pre-wrap font-sans text-xs space-y-2">
                  {m.text}
                </div>

                {/* Linked Relevant Reports */}
                {m.relevantReports && m.relevantReports.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-[#D9E2EA] flex flex-wrap gap-2">
                    <span className="text-[10px] font-mono text-[#718394] uppercase block w-full">
                      Referenced Database Reports ({m.relevantReports.length}):
                    </span>
                    {m.relevantReports.map((r, rIdx) => (
                      <button
                        key={r.id || rIdx}
                        onClick={() => onOpenReport(r.id)}
                        className="px-2.5 py-1 rounded-lg bg-white hover:bg-[#EEF3F7] text-[#1769AA] border border-[#D9E2EA] font-mono text-[11px] font-bold transition-colors flex items-center gap-1.5 shadow-sm"
                      >
                        <span>Report {r.original_id || (r.id ? r.id.slice(0, 8) : 'Record')}</span>
                        {r.risk && (
                          <span
                            className={`px-1 rounded text-[9px] ${
                              String(r.risk).toLowerCase() === 'high' || String(r.risk).toLowerCase() === 'critical'
                                ? 'bg-rose-50 text-rose-800 border border-rose-200'
                                : 'bg-[#EEF3F7] text-[#526575]'
                            }`}
                          >
                            {r.risk}
                          </span>
                        )}
                        </button>
                    ))}
                  </div>
                )}

                {/* Suggested Follow-up Actions */}
                {m.suggestedActions && m.suggestedActions.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-[#D9E2EA] flex flex-wrap gap-1.5">
                    <span className="text-[10px] font-mono text-[#718394] uppercase block w-full">
                      Related Inquiries:
                    </span>
                    {m.suggestedActions.map((act, i) => (
                      <button
                        key={i}
                        onClick={() => handleSend(act)}
                        className="px-2.5 py-1 rounded-full bg-white hover:bg-[#EEF3F7] text-[#172B3A] hover:text-[#1769AA] border border-[#D9E2EA] font-mono text-[10px] transition-all shadow-sm"
                      >
                        {act}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <span className="text-[9px] font-mono text-[#718394] mt-1 px-1">
                {m.sender === 'user' ? 'YOU' : 'OIL SAFETY INTELLIGENCE ASSISTANT'} • {m.timestamp}
              </span>
            </div>
          );
        })}
        {loading && (
          <div className="flex items-center gap-2 text-xs font-mono text-[#1769AA] p-3 bg-blue-50 rounded-lg border border-blue-200 w-fit animate-pulse">
            <span className="h-2 w-2 rounded-full bg-[#1769AA] animate-ping" />
            <span>Querying Barrier Degradation (BDI), Swiss Cheese defense layers, and SIF Precursor models...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="p-4 border-t border-[#D9E2EA] bg-[#EEF3F7]">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask database questions: 'Show critical SIF precursors', 'Why is BDI high?', 'Which barriers failed?', 'Which actions breached SLA?'..."
            className="flex-1 bg-white border border-[#D9E2EA] focus:border-[#1769AA] rounded-xl px-4 py-3 text-xs font-sans text-[#172B3A] placeholder-[#718394] focus:outline-none focus:ring-1 focus:ring-[#1769AA]"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-6 py-3 rounded-xl bg-[#1769AA] hover:bg-[#123B5D] disabled:opacity-40 text-white font-mono text-xs font-bold transition-all shadow-sm"
          >
            Send 
          </button>
        </form>
      </div>
    </div>
  );
};

export default AISafetyChat;
