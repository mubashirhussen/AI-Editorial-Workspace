import React, { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { projectService } from '../../services/projectService';
import { ToastProvider, useToast } from '../common/Toast';
import { Modal } from '../common/Modal';
import { Input } from '../common/Input';
import { Textarea } from '../common/Textarea';
import { Button } from '../common/Button';

const DashboardLayoutContent: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  
  const navigate = useNavigate();
  const { success, error } = useToast();

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    try {
      setIsCreating(true);
      const proj = await projectService.createProject({
        title: newTitle.trim(),
        description: newDesc.trim() || undefined,
      });
      setIsModalOpen(false);
      setNewTitle('');
      setNewDesc('');
      success(`Project "${proj.title}" created successfully!`);
      navigate(`/research/${proj.id}`);
    } catch (err: any) {
      error(err.message || 'Failed to create project');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 overflow-hidden font-sans">
      {/* Desktop Sidebar */}
      <div className="hidden md:flex">
        <Sidebar 
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        />
      </div>

      {/* Mobile Navigation Drawer */}
      {isMobileNavOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div 
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs transition-opacity" 
            onClick={() => setIsMobileNavOpen(false)} 
          />
          <div className="relative flex flex-col w-64 max-w-xs bg-slate-900 shadow-2xl z-10 animate-in slide-in-from-left duration-200">
            <Sidebar 
              isCollapsed={false}
              onCloseMobile={() => setIsMobileNavOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Main Workspace Column */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header 
          onNewProject={() => setIsModalOpen(true)} 
          onToggleMobileNav={() => setIsMobileNavOpen(!isMobileNavOpen)}
        />
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>

      {/* Global New Research Project Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Initialize Research Project"
        description="Set up an investigation workspace to ingest, analyze, and synthesize evidence from multiple sources."
        maxWidth="md"
      >
        <form onSubmit={handleCreateProject} className="space-y-4">
          <Input
            label="Project Title"
            placeholder="e.g. OpenAI o3 & DeepSeek-R1 Competitive Benchmark"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            required
            autoFocus
          />

          <Textarea
            label="Editorial Context & Scope (Optional)"
            placeholder="Key questions: Are open-weights models closing the reasoning capability gap for production software agents?"
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            rows={3}
          />

          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isCreating}
              disabled={!newTitle.trim()}
            >
              Initialize Workspace
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export const DashboardLayout: React.FC = () => {
  return (
    <ToastProvider>
      <DashboardLayoutContent />
    </ToastProvider>
  );
};
