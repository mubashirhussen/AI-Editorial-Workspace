import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Search, Moon, Sun, Menu, AlertCircle, CheckCircle2 } from 'lucide-react';
import { checkHealth, HealthStatus } from '../../services/healthService';
import { OrganizationSwitcher } from './OrganizationSwitcher';
import { UserProfileMenu } from './UserProfileMenu';

interface HeaderProps {
  currentProjectTitle?: string;
  onNewProject?: () => void;
  onToggleMobileNav?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ currentProjectTitle, onToggleMobileNav }) => {
  const [isDark, setIsDark] = useState(false);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    const fetchHealth = async () => {
      try {
        const data = await checkHealth();
        if (isMounted) {
          setHealth(data);
          setIsBackendHealthy(data.status === 'healthy' && data.database === 'connected');
        }
      } catch (err) {
        if (isMounted) {
          setIsBackendHealthy(false);
        }
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const toggleTheme = () => {
    setIsDark(!isDark);
    if (!isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  // Derive title from current route
  const getPageTitle = () => {
    const path = location.pathname;
    if (path === '/' || path.startsWith('/dashboard')) return 'Dashboard';
    if (path.startsWith('/research')) return 'Research Assistant';
    if (path.startsWith('/writing')) return 'Writing Assistant';
    if (path.startsWith('/editorial')) return 'Editorial Studio';
    if (path.startsWith('/projects')) return 'Research Projects';
    if (path.startsWith('/settings')) return 'Settings';
    return 'Editorial AI';
  };

  return (
    <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 md:px-6 flex items-center justify-between sticky top-0 z-20 transition-colors">
      {/* Left: Mobile Toggle & Breadcrumbs */}
      <div className="flex items-center gap-3">
        {onToggleMobileNav && (
          <button
            onClick={onToggleMobileNav}
            className="md:hidden p-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
            title="Toggle Menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        {/* Dynamic Breadcrumbs */}
        <div className="flex items-center gap-2 text-xs font-semibold">
          <span className="text-slate-400 dark:text-slate-500 hidden sm:inline">Workspace</span>
          <span className="text-slate-300 dark:text-slate-600 hidden sm:inline">/</span>
          <span className="text-slate-900 dark:text-white font-bold">{getPageTitle()}</span>
          {currentProjectTitle && (
            <>
              <span className="text-slate-300 dark:text-slate-600">/</span>
              <span className="text-blue-600 dark:text-blue-400 max-w-[140px] md:max-w-[200px] truncate">
                {currentProjectTitle}
              </span>
            </>
          )}
        </div>

        {/* Live Backend Connection Status Indicator */}
        <div 
          className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border cursor-pointer transition-colors ml-2"
          onClick={() => navigate('/settings')}
          title={isBackendHealthy ? `Backend connected (DB: ${health?.database || 'connected'})` : 'Backend unavailable - Click to inspect Settings'}
        >
          {isBackendHealthy === null ? (
            <>
              <div className="w-2 h-2 rounded-full bg-slate-300 animate-ping" />
              <span className="text-slate-500">Checking backend...</span>
            </>
          ) : isBackendHealthy ? (
            <>
              <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-xs shadow-emerald-500/50" />
              <span className="text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 px-1 py-0.5 rounded">
                Backend connected
              </span>
            </>
          ) : (
            <>
              <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
              <span className="text-rose-700 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/60 px-1 py-0.5 rounded">
                Backend unavailable
              </span>
            </>
          )}
        </div>
      </div>

      {/* Right: Quick Search & Theme Switcher */}
      <div className="flex items-center gap-3">
        <OrganizationSwitcher />

        <div className="relative w-48 sm:w-64 hidden lg:block">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search workspace..."
            className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-700 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
          />
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
          title="Toggle Theme"
        >
          {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
        </button>

        {/* User Profile on the top-right corner */}
        <UserProfileMenu />
      </div>
    </header>
  );
};
