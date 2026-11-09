import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderKanban, Trash2, ArrowRight, Plus, Search, Calendar, FileText, Copy, Sparkles, Filter } from 'lucide-react';
import { researchApi } from '../services/researchApi';
import { Project } from '../types';
import { useToast } from '../components/common/Toast';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { Input } from '../components/common/Input';

export const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'COMPLETED' | 'DRAFT' | 'IN_PROGRESS'>('ALL');
  const [loading, setLoading] = useState(true);
  const [deleteProjectId, setDeleteProjectId] = useState<string | null>(null);
  
  // New Project Modal State
  const [isNewProjectOpen, setIsNewProjectOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const navigate = useNavigate();
  const { success, error, info } = useToast();

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const res = await researchApi.getProjects();
      setProjects(res.items);
    } catch (err: any) {
      console.error(err);
      error(err.message || 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    try {
      setIsCreating(true);
      const created = await researchApi.createProject({
        title: newTitle.trim(),
        description: newDescription.trim() || undefined,
      });
      success(`Project "${created.title}" initialized.`);
      setIsNewProjectOpen(false);
      setNewTitle('');
      setNewDescription('');
      await loadProjects();
      navigate(`/research?projectId=${created.id}`);
    } catch (err: any) {
      error(err.message || 'Failed to create project');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDuplicateProject = async (e: React.MouseEvent, project: Project) => {
    e.stopPropagation();
    try {
      const duplicated = await researchApi.createProject({
        title: `${project.title} (Copy)`,
        description: project.description ? `${project.description} [Duplicated]` : undefined,
      });
      success(`Duplicated project: ${duplicated.title}`);
      await loadProjects();
    } catch (err: any) {
      error(err.message || 'Failed to duplicate project');
    }
  };

  const confirmDeleteProject = async () => {
    if (!deleteProjectId) return;
    try {
      await researchApi.deleteProject(deleteProjectId);
      setProjects((prev) => prev.filter((p) => p.id !== deleteProjectId));
      success('Research project deleted successfully.');
    } catch (err: any) {
      error(err.message || 'Failed to delete project');
    } finally {
      setDeleteProjectId(null);
    }
  };

  const filteredProjects = projects.filter((p) => {
    const matchesSearch =
      p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesStatus =
      statusFilter === 'ALL' ||
      (statusFilter === 'COMPLETED' && p.status?.toLowerCase() === 'completed') ||
      (statusFilter === 'DRAFT' && p.status?.toLowerCase() === 'draft') ||
      (statusFilter === 'IN_PROGRESS' && (p.status?.toLowerCase() === 'in_progress' || p.status?.toLowerCase() === 'active'));

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">Saved Projects</h2>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono font-medium">
              {projects.length} Total
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Access, manage, and resume multi-source research investigations and editorial production pipelines.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative w-64">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full text-xs pl-9 pr-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>

          <Button
            onClick={() => setIsNewProjectOpen(true)}
            size="sm"
            variant="primary"
            leftIcon={<Plus className="w-3.5 h-3.5" />}
          >
            New Project
          </Button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 pb-2">
        {(['ALL', 'COMPLETED', 'DRAFT', 'IN_PROGRESS'] as const).map((st) => (
          <button
            key={st}
            type="button"
            onClick={() => setStatusFilter(st)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
              statusFilter === st
                ? 'bg-blue-600 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
            }`}
          >
            {st === 'ALL' ? 'All Projects' : st.replace('_', ' ')}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="py-20 text-center text-xs text-slate-400">Loading project library...</div>
      ) : filteredProjects.length === 0 ? (
        <div className="py-20 text-center space-y-4 bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 p-8">
          <FolderKanban className="w-10 h-10 text-slate-400 mx-auto" />
          <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">No Projects Found</h4>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
            {searchQuery ? 'No projects match your current search query.' : 'Create a new research project to begin collecting sources and synthesizing evidence.'}
          </p>
          <Button
            onClick={() => setIsNewProjectOpen(true)}
            size="sm"
            variant="primary"
            leftIcon={<Plus className="w-3.5 h-3.5" />}
          >
            Create First Project
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProjects.map((p) => (
            <div
              key={p.id}
              onClick={() => navigate(`/research?projectId=${p.id}`)}
              className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between group"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <span className={`text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded-full ${
                    p.status?.toLowerCase() === 'completed'
                      ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300'
                      : 'bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300'
                  }`}>
                    {p.status}
                  </span>
                  <div className="flex items-center gap-1 opacity-60 group-hover:opacity-100 transition-opacity">
                    <button
                      type="button"
                      onClick={(e) => handleDuplicateProject(e, p)}
                      className="text-slate-400 hover:text-blue-600 p-1 rounded transition-colors"
                      title="Duplicate project"
                    >
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setDeleteProjectId(p.id);
                      }}
                      className="text-slate-400 hover:text-red-600 p-1 rounded transition-colors"
                      title="Delete project"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors line-clamp-1">
                    {p.title}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                    {p.description || 'No description provided.'}
                  </p>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 dark:border-slate-800 mt-4 flex items-center justify-between text-[11px] text-slate-400">
                <div className="flex items-center gap-1.5 font-mono">
                  <FileText className="w-3.5 h-3.5 text-blue-500" />
                  <span>{p.sources?.length || 0} Sources</span>
                </div>
                <div className="flex items-center gap-1 text-blue-600 font-semibold group-hover:translate-x-1 transition-transform">
                  <span>Open Investigation</span>
                  <ArrowRight className="w-3 h-3" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* New Project Modal */}
      <Modal
        isOpen={isNewProjectOpen}
        onClose={() => setIsNewProjectOpen(false)}
        title="Initialize Research Project"
      >
        <form onSubmit={handleCreateProject} className="space-y-4">
          <Input
            label="Project Title"
            placeholder="e.g., Quantum Computing Benchmarks 2026"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            required
            autoFocus
          />
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Investigation Scope & Description
            </label>
            <textarea
              rows={3}
              placeholder="Brief summary of research goals, hypotheses, and required sources..."
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              className="w-full text-xs p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 resize-none"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsNewProjectOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isCreating}
            >
              Create Project
            </Button>
          </div>
        </form>
      </Modal>

      {/* Confirm Deletion Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deleteProjectId)}
        title="Delete Research Project"
        message="Are you sure you want to delete this project? All associated sources, evidence alignments, and research briefs will be permanently removed."
        confirmLabel="Delete Project"
        isDestructive
        onConfirm={confirmDeleteProject}
        onCancel={() => setDeleteProjectId(null)}
      />
    </div>
  );
};
