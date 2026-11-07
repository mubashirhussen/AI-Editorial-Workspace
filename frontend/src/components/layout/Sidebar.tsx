import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Search, 
  PenTool, 
  Newspaper, 
  FolderKanban, 
  Settings,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Users,
  Activity
} from 'lucide-react';

interface SidebarProps {
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  isCollapsed = false, 
  onToggleCollapse,
  onCloseMobile 
}) => {
  const navItems = [
    { name: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
    { name: 'Research Assistant', to: '/research', icon: Search },
    { name: 'Writing Assistant', to: '/writing', icon: PenTool },
    { name: 'Editorial Studio', to: '/editorial', icon: Newspaper },
    { name: 'Research Projects', to: '/projects', icon: FolderKanban },
    { name: 'Organization', to: '/organization', icon: Users },
    { name: 'AI Observability', to: '/observability', icon: Activity },
    { name: 'Settings', to: '/settings', icon: Settings },
  ];

  return (
    <aside className={`h-full bg-slate-900 text-slate-300 flex flex-col shrink-0 border-r border-slate-800 select-none transition-all duration-200 ${
      isCollapsed ? 'w-20' : 'w-64'
    }`}>
      {/* Brand Header */}
      <div className={`h-16 flex items-center gap-3 border-b border-slate-800 ${
        isCollapsed ? 'justify-center px-2' : 'px-6'
      }`}>
        <div className="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/30 shrink-0">
          <Sparkles className="w-4 h-4" />
        </div>
        {!isCollapsed && (
          <div className="overflow-hidden truncate">
            <h1 className="font-bold text-white text-sm tracking-tight leading-none truncate">Editorial AI</h1>
            <p className="text-[10px] text-slate-400 mt-1 font-mono uppercase tracking-wider truncate">This Week in AI</p>
          </div>
        )}
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-6 space-y-1.5 overflow-y-auto">
        {!isCollapsed && (
          <div className="px-3 pb-2 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            Workspace Modules
          </div>
        )}
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onCloseMobile}
              title={isCollapsed ? item.name : undefined}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isCollapsed ? 'justify-center' : ''
                } ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-xs shadow-blue-600/30'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              {!isCollapsed && <span className="truncate">{item.name}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom Status Card & Collapse Toggle */}
      <div className="p-3 border-t border-slate-800 space-y-2">
        {!isCollapsed && (
          <div className="p-2.5 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shrink-0" />
            <div className="text-[11px] truncate">
              <div className="font-semibold text-slate-200 truncate">Fact-Check Engine</div>
              <div className="text-[10px] text-slate-400 truncate">Deterministic + LLM</div>
            </div>
          </div>
        )}

        {/* Desktop Collapse Toggle */}
        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className={`hidden md:flex items-center gap-2 w-full py-2 px-3 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 text-xs font-medium transition-colors ${
              isCollapsed ? 'justify-center' : ''
            }`}
          >
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <>
                <ChevronLeft className="w-4 h-4" />
                <span>Hide Sidebar</span>
              </>
            )}
          </button>
        )}
      </div>
    </aside>
  );
};
