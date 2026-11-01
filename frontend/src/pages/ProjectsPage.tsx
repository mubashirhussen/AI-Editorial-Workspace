import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderKanban, Trash2, ArrowRight, Plus, Search, Calendar, FileText } from 'lucide-react';
import { researchApi } from '../services/researchApi';
import { Project } from '../types';
import { useToast } from '../components/common/Toast';
import { ConfirmDialog } from '../components/common/ConfirmDialog';

export const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [deleteProjectId, setDeleteProjectId] = useState<string | null>(null);
  const navigate = useNavigate();
  const { success, error } = useToast();

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const res = await researchApi.getProjects();
      setProjects(res.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
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

  const filteredProjects = projects.filter((p) =>
    p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Saved Projects</h2>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-mono font-medium">
              {projects.length} Total
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Access, manage, and resume multi-source research investigations and editorial production pipelines.
          </p>
        </div>

        <div className="relative w-72">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-xs pl-9 pr-3 py-2 bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          />
        </div>
      </div>

      {loading ? (
        <div className="py-20 text-center text-xs text-slate-400">Loading project library...</div>
      ) : filteredProjects.length === 0 ? (
        <div className="py-20 text-center space-y-3 bg-white rounded-2xl border border-dashed border-slate-200 p-8">
          <FolderKanban className="w-10 h-10 text-slate-400 mx-auto" />
          <h4 className="text-sm font-semibold text-slate-800">No Projects Found</h4>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Create a new research project to begin collecting sources and synthesizing evidence.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProjects.map((p) => (
            <div
              key={p.id}
              onClick={() => navigate(`/research?projectId=${p.id}`)}
              className="bg-white p-5 rounded-2xl border border-slate-200/80 hover:border-blue-400 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between group"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700">
                    {p.status}
                  </span>
                  <button
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

                <div>
                  <h3 className="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-1">
                    {p.title}
                  </h3>
                  {p.description && (
                    <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                      {p.description}
                    </p>
                  )}
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                <div className="flex items-center gap-3">
                  <span>{p.sources?.length || 0} sources</span>
                  <span>•</span>
                  <span>{p.briefs?.length > 0 ? 'Brief ready' : 'No brief'}</span>
                </div>
                <div className="text-blue-600 font-medium flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                  <span>Open</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {/* Confirmation Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deleteProjectId)}
        title="Delete Project"
        message="Are you sure you want to permanently delete this research project and all associated sources? This action cannot be undone."
        confirmLabel="Delete Project"
        isDestructive={true}
        onConfirm={confirmDeleteProject}
        onCancel={() => setDeleteProjectId(null)}
      />
    </div>
  );
};

