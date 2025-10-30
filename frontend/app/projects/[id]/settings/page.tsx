'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { projectsAPI, filesAPI } from '@/lib/api';
import { Save, Trash2, AlertCircle, Globe, Lock } from 'lucide-react';
import toast from 'react-hot-toast';

interface Project {
  id: number;
  name: string;
  description: string | null;
  visibility: string;
  git_branch: string;
  created_at: string;
}

export default function SettingsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = parseInt(params.id as string);

  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  // Form fields
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [visibility, setVisibility] = useState('private');
  const [gitBranch, setGitBranch] = useState('main');

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const loadProject = async () => {
    try {
      const response = await projectsAPI.get(projectId);
      const proj = response.data;
      setProject(proj);
      setName(proj.name);
      setDescription(proj.description || '');
      setVisibility(proj.visibility);
      setGitBranch(proj.git_branch || 'main');
    } catch (error) {
      toast.error('Failed to load project');
      router.push('/projects');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      await projectsAPI.update(projectId, {
        name,
        description: description || null,
        visibility,
        git_branch: gitBranch,
      });
      toast.success('Settings saved');
      await loadProject();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const deleteProject = async () => {
    if (deleteConfirm !== project?.name) {
      toast.error('Project name does not match');
      return;
    }

    try {
      await projectsAPI.delete(projectId);
      toast.success('Project deleted');
      router.push('/projects');
    } catch (error) {
      toast.error('Failed to delete project');
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!project) {
    return null;
  }

  return (
    <div className="h-full bg-gray-50 overflow-auto">
      {/* Toolbar */}
      <div className="border-b border-gray-200 bg-white px-6 py-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Project Settings</h2>
          <button
            onClick={saveSettings}
            disabled={saving}
            className="btn-primary flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      <div className="max-w-4xl mx-auto p-6 space-y-6">
        {/* General Settings */}
        <div className="bg-white border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4">General</h3>

          <div className="space-y-4">
            {/* Project Name */}
            <div>
              <label className="block text-sm font-medium mb-2">Project Name</label>
              <input
                type="text"
                className="input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My Project"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium mb-2">Description</label>
              <textarea
                className="input"
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Project description..."
              />
            </div>

            {/* Visibility */}
            <div>
              <label className="block text-sm font-medium mb-2">Visibility</label>
              <div className="space-y-2">
                <label className="flex items-center gap-3 p-3 border border-gray-300 rounded cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="visibility"
                    value="private"
                    checked={visibility === 'private'}
                    onChange={(e) => setVisibility(e.target.value)}
                  />
                  <Lock className="w-5 h-5 text-gray-600" />
                  <div>
                    <div className="font-medium">Private</div>
                    <div className="text-xs text-gray-600">Only you can access this project</div>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-3 border border-gray-300 rounded cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="visibility"
                    value="public"
                    checked={visibility === 'public'}
                    onChange={(e) => setVisibility(e.target.value)}
                  />
                  <Globe className="w-5 h-5 text-gray-600" />
                  <div>
                    <div className="font-medium">Public</div>
                    <div className="text-xs text-gray-600">Anyone can view this project</div>
                  </div>
                </label>
              </div>
            </div>

            {/* Git Branch */}
            <div>
              <label className="block text-sm font-medium mb-2">Git Branch</label>
              <input
                type="text"
                className="input"
                value={gitBranch}
                onChange={(e) => setGitBranch(e.target.value)}
                placeholder="main"
              />
              <p className="text-xs text-gray-500 mt-1">Default branch for version control</p>
            </div>
          </div>
        </div>

        {/* Project Info */}
        <div className="bg-white border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4">Project Information</h3>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Project ID:</span>
              <span className="font-mono">{project.id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Created:</span>
              <span>{new Date(project.created_at).toLocaleDateString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Current Visibility:</span>
              <span className="flex items-center gap-1">
                {project.visibility === 'private' ? (
                  <>
                    <Lock className="w-4 h-4" />
                    Private
                  </>
                ) : (
                  <>
                    <Globe className="w-4 h-4" />
                    Public
                  </>
                )}
              </span>
            </div>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="bg-white border border-red-300 p-6">
          <h3 className="text-lg font-semibold text-red-600 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Danger Zone
          </h3>

          <div className="space-y-4">
            <div>
              <h4 className="font-medium mb-2">Delete Project</h4>
              <p className="text-sm text-gray-600 mb-3">
                Once you delete a project, there is no going back. This will permanently delete the
                project and all its files, jobs, and history.
              </p>
              <button
                onClick={() => setShowDeleteModal(true)}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Delete Project
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white w-full max-w-md border border-gray-300 p-6">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-red-600">
              <AlertCircle className="w-6 h-6" />
              Delete Project
            </h3>

            <p className="text-sm text-gray-700 mb-4">
              This action cannot be undone. This will permanently delete the{' '}
              <strong>{project.name}</strong> project, all files, jobs, and associated data.
            </p>

            <p className="text-sm text-gray-700 mb-2">
              Please type <strong>{project.name}</strong> to confirm:
            </p>

            <input
              type="text"
              className="input mb-4"
              value={deleteConfirm}
              onChange={(e) => setDeleteConfirm(e.target.value)}
              placeholder={project.name}
              autoFocus
            />

            <div className="flex gap-2">
              <button
                onClick={deleteProject}
                disabled={deleteConfirm !== project.name}
                className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-4 py-2 rounded flex items-center justify-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Delete Project
              </button>
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeleteConfirm('');
                }}
                className="flex-1 btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
