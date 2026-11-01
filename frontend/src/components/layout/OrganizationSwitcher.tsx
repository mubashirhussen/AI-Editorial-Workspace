import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, 
  ChevronDown, 
  Check, 
  Plus, 
  Users, 
  ShieldCheck, 
  LogOut,
  Sparkles 
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const OrganizationSwitcher: React.FC = () => {
  const { activeOrg, organizations, switchOrganization, role, user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [showNewModal, setShowNewModal] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  const handleSelectOrg = async (orgId: string) => {
    await switchOrganization(orgId);
    setIsOpen(false);
  };

  const getRoleBadgeStyle = (r?: string) => {
    switch (r) {
      case 'OWNER':
        return 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/50 dark:text-purple-300';
      case 'ADMIN':
        return 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/50 dark:text-blue-300';
      case 'EDITOR':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300';
      case 'REVIEWER':
        return 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/50 dark:text-amber-300';
      case 'VIEWER':
      default:
        return 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-300';
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-all text-left shadow-2xs"
      >
        <div className="w-6 h-6 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center font-bold text-xs shrink-0">
          <Building2 className="w-3.5 h-3.5" />
        </div>
        <div className="flex flex-col truncate max-w-[130px] sm:max-w-[160px]">
          <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
            {activeOrg?.name || 'Workspace'}
          </span>
          <span className="text-[10px] text-slate-400 uppercase font-mono tracking-wider">
            {role || 'OWNER'}
          </span>
        </div>
        <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-1 shrink-0" />
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)} 
          />
          <div className="absolute left-0 mt-2 w-64 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl z-50 p-2 space-y-1 animate-in fade-in zoom-in-95 duration-100">
            <div className="px-2.5 py-1.5 border-b border-slate-100 dark:border-slate-800 mb-1">
              <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                Workspaces ({organizations.length})
              </div>
              {user && (
                <div className="text-xs text-slate-600 dark:text-slate-300 truncate mt-0.5 font-medium">
                  {user.email}
                </div>
              )}
            </div>

            <div className="max-h-52 overflow-y-auto space-y-0.5">
              {organizations.map((org) => {
                const isSelected = org.id === activeOrg?.id;
                return (
                  <button
                    key={org.id}
                    onClick={() => handleSelectOrg(org.id)}
                    className={`w-full flex items-center justify-between px-2.5 py-2 rounded-xl text-left text-xs transition-colors ${
                      isSelected 
                        ? 'bg-indigo-50/70 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 font-semibold' 
                        : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800'
                    }`}
                  >
                    <div className="truncate pr-2">
                      <div className="truncate">{org.name}</div>
                      <div className="text-[10px] text-slate-400">{org.slug}</div>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-medium border ${getRoleBadgeStyle(org.role)}`}>
                        {org.role || 'MEMBER'}
                      </span>
                      {isSelected && <Check className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />}
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="pt-1 border-t border-slate-100 dark:border-slate-800 space-y-0.5">
              <button
                onClick={() => {
                  setIsOpen(false);
                  navigate('/organization');
                }}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-xl text-xs text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
              >
                <Users className="w-3.5 h-3.5 text-slate-400" />
                <span>Members & Access Control</span>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

