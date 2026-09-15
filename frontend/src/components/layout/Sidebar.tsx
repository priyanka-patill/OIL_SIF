import React from 'react';
import { UserRole } from '../../types/safety';
import {
  LayoutDashboard,
  FileText,
  ShieldAlert,
  Sliders,
  ShieldCheck,
  CheckSquare,
  BarChart3,
  Bot,
  Database,
  Settings,
  PlusCircle,
  Activity
} from 'lucide-react';

export type NavTab =
  | 'dashboard'
  | 'reports'
  | 'sif'
  | 'factors'
  | 'predictability'
  | 'actions'
  | 'chat'
  | 'analytics'
  | 'datasets'
  | 'settings';

interface SidebarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
  highRiskCount?: number;
  sifCount?: number;
  overdueCount?: number;
  activeRole?: UserRole;
  onOpenSubmitReport?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  sifCount = 0,
  overdueCount = 0,
  activeRole = 'Safety Officer',
  onOpenSubmitReport,
}) => {
  const navSections = [
    {
      title: 'HOME',
      items: [
        { id: 'dashboard' as NavTab, label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
      ]
    },
    {
      title: 'REPORTING',
      items: [
        { id: 'reports' as NavTab, label: 'Safety Reports', icon: <FileText className="w-4 h-4" /> },
      ]
    },
    {
      title: 'SAFETY INTELLIGENCE',
      items: [
        { id: 'sif' as NavTab, label: 'SIF Risk Intelligence', icon: <ShieldAlert className="w-4 h-4" />, badge: sifCount > 0 ? `${sifCount}` : undefined, badgeColor: 'bg-rose-500/30 text-white border-rose-300/40 font-bold' },
        { id: 'factors' as NavTab, label: 'Factor Intelligence', icon: <Sliders className="w-4 h-4" /> },
        { id: 'predictability' as NavTab, label: 'Preventive Intelligence', icon: <ShieldCheck className="w-4 h-4" /> },
      ]
    },
    {
      title: 'ACTIONS',
      items: [
        { id: 'actions' as NavTab, label: 'Action Center', icon: <CheckSquare className="w-4 h-4" />, badge: overdueCount > 0 ? `${overdueCount} Overdue` : undefined, badgeColor: 'bg-red-500/30 text-white border-red-300/40 font-bold' },
      ]
    },
    {
      title: 'ANALYSIS',
      items: [
        { id: 'analytics' as NavTab, label: 'Deep Analytics', icon: <BarChart3 className="w-4 h-4" /> },
        { id: 'chat' as NavTab, label: 'AI Safety Chat', icon: <Bot className="w-4 h-4" /> },
      ]
    },
    {
      title: 'DATA',
      items: [
        { id: 'datasets' as NavTab, label: 'Dataset Registry', icon: <Database className="w-4 h-4" /> },
      ]
    },
    {
      title: 'SETTINGS',
      items: [
        { id: 'settings' as NavTab, label: 'Settings & Escalations', icon: <Settings className="w-4 h-4" /> },
      ]
    }
  ];

  return (
    <aside className="w-64 bg-[#123B5D] border-r border-[#0E2E49] flex flex-col shrink-0 h-screen sticky top-0 select-none text-white shadow-xl">
      {/* Brand Header */}
      <div className="px-5 py-4 border-b border-white/10 flex items-center gap-3 bg-[#0F2F4A]">
        <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-[#1769AA] to-[#2589C7] flex items-center justify-center font-black text-white text-sm shadow-md shrink-0 ring-2 ring-white/10">
          OIL
        </div>
        <div>
          <div className="text-sm font-extrabold text-white tracking-tight">
            OIL Safety Intelligence
          </div>
          <div className="text-xs text-blue-200/80 font-semibold">
            Control Center Dashboard
          </div>
        </div>
      </div>

      {/* Role Badge & Prominent Submit Report Button */}
      <div className="px-4 pt-4 pb-2 space-y-3">
        <div className="bg-[#0F2F4A]/90 border border-white/10 rounded-xl px-3 py-2 flex items-center justify-between text-xs shadow-inner">
          <span className="text-blue-200/80 font-semibold">User Role</span>
          <span className="text-cyan-300 font-extrabold">{activeRole}</span>
        </div>

        {onOpenSubmitReport && (
          <button
            type="button"
            onClick={onOpenSubmitReport}
            className="w-full py-2.5 px-3 rounded-xl bg-[#2E8B57] hover:bg-[#256F46] text-white text-xs font-extrabold transition-all shadow-md flex items-center justify-center gap-2 tracking-wide uppercase"
          >
            <PlusCircle className="w-4 h-4" /> Submit Safety Report
          </button>
        )}
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-2 space-y-4 overflow-y-auto custom-scrollbar">
        {navSections.map((section, idx) => (
          <div key={idx} className="space-y-1">
            <div className="px-3 pb-1 pt-1 text-[10px] font-extrabold tracking-widest text-cyan-200/70 uppercase">
              {section.title}
            </div>
            {section.items.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs transition-all relative font-semibold ${
                    isActive
                      ? 'bg-[#1769AA] text-white shadow-md font-extrabold border-l-4 border-cyan-400 pl-2.5'
                      : 'text-blue-100/80 hover:text-white hover:bg-white/10 border-l-4 border-transparent pl-2.5'
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <span className="shrink-0 text-cyan-300/90">{item.icon}</span>
                    <span className="truncate tracking-tight">{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={`px-2 py-0.5 text-[10px] font-extrabold rounded-md border ${
                        item.badgeColor || 'bg-white/10 text-white border-white/20'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-white/10 bg-[#0F2F4A]">
        <div className="flex items-center justify-between text-xs">
          <span className="text-blue-200/80 font-semibold">System Status</span>
          <span className="text-emerald-400 font-extrabold flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            Online
          </span>
        </div>
      </div>
    </aside>
  );
};
