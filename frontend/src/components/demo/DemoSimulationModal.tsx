import React, { useState, useEffect } from 'react';
import { DemoStatusResponse, DemoScenarioExecutionResponse } from '../../types/safety';
import { api } from '../../services/api';
import { AuditTimelineView } from '../audit/AuditTimelineView';

interface DemoSimulationModalProps {
  onClose: () => void;
  onOpenReport?: (reportId: string) => void;
}

export const DemoSimulationModal: React.FC<DemoSimulationModalProps> = ({ onClose, onOpenReport }) => {
  const [demoStatus, setDemoStatus] = useState<DemoStatusResponse | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<string>('CRITICAL_SIF_PRECURSOR');
  const [executionResult, setExecutionResult] = useState<DemoScenarioExecutionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionStepResult, setActionStepResult] = useState<string | null>(null);
  const [showEmailPreview, setShowEmailPreview] = useState(false);
  const [activeTab, setActiveTab] = useState<'pipeline' | 'email' | 'audit'>('pipeline');

  const fetchStatus = async () => {
    try {
      const st = await api.getDemoStatus();
      setDemoStatus(st);
    } catch (err) {
      console.error('Failed to get demo status:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleLoadScenario = async (scType?: string) => {
    const targetScenario = scType || selectedScenario;
    setLoading(true);
    setActionStepResult(null);
    try {
      const res = await api.loadDemoScenario(targetScenario);
      setExecutionResult(res);
      fetchStatus();
    } catch (err: any) {
      alert(`Failed to load scenario: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleTimeTravel = async (advanceMins: number) => {
    setLoading(true);
    try {
      const res = await api.timeTravelDemo(advanceMins, executionResult?.action_id || undefined);
      setActionStepResult(`Advanced +${advanceMins}m virtual time. State: ${res.action_sla_state} (Level ${res.escalation_level})`);
      fetchStatus();
    } catch (err: any) {
      alert(`Time travel failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateStep = async (step: string) => {
    if (!executionResult?.action_id) {
      alert('Please load a scenario first.');
      return;
    }
    setLoading(true);
    try {
      const res = await api.simulateDemoStep({
        step,
        action_id: executionResult.action_id,
        actor_name: 'Lead Safety Engineer',
        actor_role: 'Safety Officer',
        notes: 'Simulated demonstration action through evaluation console',
      });
      setActionStepResult(`Simulated ${step} successfully! (State: ${res.sla_state})`);
      fetchStatus();
    } catch (err: any) {
      alert(`Step simulation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-900/40 backdrop-blur-md animate-fadeIn overflow-y-auto">
      <div className="bg-white border border-[#D9E2EA] rounded-2xl w-full max-w-5xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Banner Header */}
        <div className="bg-[#EEF3F7] border-b border-[#D9E2EA] p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl animate-pulse"></span>
              <h2 className="text-sm sm:text-base font-mono font-bold text-[#172B3A] uppercase tracking-wider">
                Hackathon Demonstration & Simulation Controller
              </h2>
              <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-bold">
                SAFE SIMULATION MODE ACTIVE
              </span>
            </div>
            <p className="text-xs font-sans text-[#526575] mt-1">
              External notifications are strictly suppressed. Fast-forward SLA countdowns and simulate lifecycle events in real time.
            </p>
          </div>

          <button
            onClick={onClose}
            className="self-end sm:self-center px-3 py-1.5 bg-white hover:bg-slate-100 text-[#172B3A] border border-[#D9E2EA] rounded-lg text-xs font-mono font-bold transition-colors shadow-sm"
          >
            Close Controller &times;
          </button>
        </div>

        {/* Action Status Bar */}
        {actionStepResult && (
          <div className="bg-emerald-50 border-b border-emerald-200 text-emerald-800 px-4 py-2 text-xs font-mono flex items-center justify-between">
            <span> {actionStepResult}</span>
            <button onClick={() => setActionStepResult(null)} className="text-[#526575] hover:text-[#172B3A] font-bold">&times;</button>
          </div>
        )}

        {/* Content Body */}
        <div className="p-4 sm:p-6 overflow-y-auto space-y-6 text-xs font-mono">
          {/* SCENARIO SELECTION CARDS */}
          <div>
            <label className="text-[11px] text-[#718394] uppercase font-bold block mb-2">
              Step 1: Select Demonstration Scenario
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-5 gap-2">
              {[
                { id: 'NORMAL', label: '1. NORMAL', badge: 'BDI ~10', desc: 'Routine Cold Work', color: 'border-emerald-200 text-emerald-800' },
                { id: 'MINOR_PRECURSOR', label: '2. MINOR PRECURSOR', badge: 'BDI ~28', desc: 'Tag / Minor Deficit', color: 'border-amber-200 text-amber-800' },
                { id: 'MULTI_FACTOR_CONVERGENCE', label: '3. MULTI-FACTOR', badge: 'BDI ~58', desc: 'Gas + Temp + Vent', color: 'border-orange-200 text-orange-800' },
                { id: 'HIGH_SIF_PRECURSOR', label: '4. HIGH SIF', badge: 'BDI ~74', desc: 'Hot Work + Bypass', color: 'border-rose-200 text-rose-800' },
                { id: 'CRITICAL_SIF_PRECURSOR', label: '5. CRITICAL SIF', badge: 'BDI ~88', desc: 'Toxic H2S + Hold', color: 'border-purple-200 text-purple-900 font-bold' },
              ].map((sc) => (
                <button
                  key={sc.id}
                  onClick={() => {
                    setSelectedScenario(sc.id);
                    handleLoadScenario(sc.id);
                  }}
                  disabled={loading}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    selectedScenario === sc.id
                      ? 'bg-[#EEF3F7] border-[#1769AA] shadow-sm scale-102 ring-1 ring-[#1769AA]'
                      : 'bg-[#F4F7FA] border-[#D9E2EA] hover:border-[#1769AA]/40'
                  }`}
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-bold text-[11px] text-[#172B3A]">{sc.label}</span>
                  </div>
                  <div className={`text-[10px] font-bold ${sc.color}`}>{sc.badge}</div>
                  <div className="text-[10px] font-sans text-[#526575] mt-1">{sc.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* SIMULATION CONTROLS & TIME TRAVEL */}
          {executionResult && (
            <div className="bg-white border border-[#D9E2EA] rounded-2xl p-4 space-y-4 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#D9E2EA] pb-3">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold text-[#1769AA] uppercase"> Simulation Controls:</span>
                  <span className="text-[#526575] text-[11px]">
                    Action: <strong className="text-[#172B3A]">{executionResult.action_id}</strong>
                    {executionResult.hold_id && <span> • Hold: <strong className="text-rose-700">{executionResult.hold_id}</strong></span>}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {onOpenReport && (
                    <button
                      onClick={() => onOpenReport(executionResult.report_id)}
                      className="px-3 py-1.5 bg-[#1769AA] hover:bg-[#123B5D] text-white rounded-lg text-xs font-bold transition-all shadow-sm"
                    >
                       Inspect In Report Modal
                    </button>
                  )}
                </div>
              </div>

              {/* Fast Forward & Step Buttons */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="space-y-1.5">
                  <label className="text-[10px] text-[#718394] uppercase block font-bold">Fast-Forward Time</label>
                  <div className="grid grid-cols-3 gap-1.5">
                    <button
                      onClick={() => handleTimeTravel(15)}
                      disabled={loading}
                      className="py-1.5 px-2 rounded-lg bg-[#F4F7FA] hover:bg-[#EEF3F7] border border-[#D9E2EA] text-[#172B3A] text-[11px] font-bold transition-colors"
                    >
                      +15m
                    </button>
                    <button
                      onClick={() => handleTimeTravel(30)}
                      disabled={loading}
                      className="py-1.5 px-2 rounded-lg bg-[#F4F7FA] hover:bg-[#EEF3F7] border border-[#D9E2EA] text-[#172B3A] text-[11px] font-bold transition-colors"
                    >
                      +30m
                    </button>
                    <button
                      onClick={() => handleTimeTravel(60)}
                      disabled={loading}
                      className="py-1.5 px-2 rounded-lg bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-800 text-[11px] font-bold transition-colors"
                    >
                      +60m
                    </button>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] text-[#718394] uppercase block font-bold">SLA Escalation</label>
                  <button
                    onClick={() => handleSimulateStep('TRIGGER_BREACH')}
                    disabled={loading}
                    className="w-full py-2 px-3 rounded-lg bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-800 font-bold transition-colors"
                  >
                     Trigger SLA Breach & Escalate
                  </button>
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] text-[#718394] uppercase block font-bold">Field Response</label>
                  <div className="grid grid-cols-2 gap-1.5">
                    <button
                      onClick={() => handleSimulateStep('ACKNOWLEDGE')}
                      disabled={loading}
                      className="py-1.5 px-2 rounded-lg bg-blue-50 hover:bg-blue-100 border border-blue-200 text-blue-800 font-bold transition-colors"
                    >
                      Acknowledge
                    </button>
                    <button
                      onClick={() => handleSimulateStep('CONTAIN')}
                      disabled={loading}
                      className="py-1.5 px-2 rounded-lg bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-800 font-bold transition-colors"
                    >
                      Contain
                    </button>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] text-[#718394] uppercase block font-bold">Verification & Closure</label>
                  <div className="grid grid-cols-2 gap-1.5">
                    <button
                      onClick={() => handleSimulateStep('VERIFY')}
                      disabled={loading}
                      className="py-1.5 px-2 rounded-lg bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-800 font-bold transition-colors"
                    >
                      Verify
                    </button>
                    <button
                      onClick={() => handleSimulateStep('CLOSE')}
                      disabled={loading}
                      className="py-1.5 px-2 rounded-lg bg-purple-50 hover:bg-purple-100 border border-purple-200 text-purple-900 font-bold transition-colors"
                    >
                      Close & Release
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TABS: PIPELINE FLOW / EMAIL PREVIEW / AUDIT TRAIL */}
          {executionResult && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b border-[#D9E2EA] pb-2">
                <button
                  onClick={() => setActiveTab('pipeline')}
                  className={`px-4 py-1.5 rounded-lg transition-all ${
                    activeTab === 'pipeline' ? 'bg-[#1769AA] text-white font-bold shadow-sm' : 'text-[#526575] hover:text-[#172B3A]'
                  }`}
                >
                   9-Step Pipeline Progression
                </button>
                <button
                  onClick={() => setActiveTab('email')}
                  className={`px-4 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                    activeTab === 'email' ? 'bg-[#1769AA] text-white font-bold shadow-sm' : 'text-[#526575] hover:text-[#172B3A]'
                  }`}
                >
                  Formatted Email Preview
                </button>
                <button
                  onClick={() => setActiveTab('audit')}
                  className={`px-4 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                    activeTab === 'audit' ? 'bg-[#1769AA] text-white font-bold shadow-sm' : 'text-[#526575] hover:text-[#172B3A]'
                  }`}
                >
                  Scenario Audit Timeline
                </button>
              </div>

              {/* TAB 1: PIPELINE STEPS */}
              {activeTab === 'pipeline' && (
                <div className="space-y-2">
                  {executionResult.pipeline_steps.map((step) => (
                    <div
                      key={step.step_number}
                      className={`p-3 rounded-xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 transition-all ${
                        step.status === 'ACTIVE'
                          ? 'bg-[#EEF3F7] border-[#1769AA] shadow-sm'
                          : 'bg-[#F4F7FA] border-[#D9E2EA]'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${
                          step.status === 'COMPLETED' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-blue-50 text-[#1769AA] border border-blue-200 animate-pulse'
                        }`}>
                          {step.step_number}
                        </span>
                        <div>
                          <span className="font-bold text-[#172B3A]">{step.step_title}</span>
                          <p className="text-[11px] text-[#526575] font-sans">{step.summary}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-[10px] text-[#718394]">{step.timestamp}</span>
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                          step.status === 'COMPLETED' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-blue-50 text-[#1769AA] border border-blue-200'
                        }`}>
                          {step.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* TAB 2: EMAIL PREVIEW */}
              {activeTab === 'email' && executionResult.email_preview && (
                <div className="bg-[#F4F7FA] rounded-xl p-4 border border-[#D9E2EA] space-y-4 font-sans text-[#172B3A]">
                  <div className="border-b border-[#D9E2EA] pb-2 text-xs font-mono">
                    <div className="text-[#526575]">SUBJECT: <strong className="text-[#1769AA]">{executionResult.email_preview.subject}</strong></div>
                    <div className="text-[#718394] text-[11px] mt-1">RECIPIENT: {executionResult.email_preview.assigned_role} • DISPATCH: Simulated Mock</div>
                  </div>
                  <div
                    className="prose max-w-none text-xs text-[#172B3A]"
                    dangerouslySetInnerHTML={{ __html: executionResult.email_preview.body_html }}
                  />
                </div>
              )}

              {/* TAB 3: AUDIT TIMELINE */}
              {activeTab === 'audit' && (
                <AuditTimelineView reportId={executionResult.report_id} />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
