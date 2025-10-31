'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { Home, FolderOpen, Settings, LogOut, Plus } from 'lucide-react';
import { projectsAPI } from '@/lib/api';
import toast from 'react-hot-toast';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);


  useEffect(() => {
    if (!loading && !user) {
      router.push('/auth/login');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-black text-white flex flex-col">
        <div className="p-6 border-b border-gray-800">
          <Link href="/dashboard" className="text-2xl font-bold">
            a6hub
          </Link>
        </div>

        <nav className="flex-1 p-4">
          <Link
            href="/dashboard"
            className="flex items-center gap-3 px-4 py-3 rounded hover:bg-gray-900 transition-colors mb-2"
          >
            <Home className="w-5 h-5" />
            <span>Dashboard</span>
          </Link>

          <div className="my-6">
            <button
              onClick={() => setShowNewProjectModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-white text-black rounded hover:bg-gray-100 transition-colors justify-center font-medium w-full"
            >
              <Plus className="w-4 h-4" />
              <span>New Project</span>
            </button>
          </div>
        </nav>

        <div className="p-4 border-t border-gray-800">
          <div className="mb-4 px-4 py-2">
            <div className="text-sm text-gray-400">Signed in as</div>
            <div className="font-medium truncate">{user.username}</div>
          </div>
          <Link
            href="/settings"
            className="flex items-center gap-3 px-4 py-3 rounded hover:bg-gray-900 transition-colors mb-2"
          >
            <Settings className="w-5 h-5" />
            <span>Settings</span>
          </Link>
          <button
            onClick={logout}
            className="flex items-center gap-3 px-4 py-3 rounded hover:bg-gray-900 transition-colors w-full text-left"
          >
            <LogOut className="w-5 h-5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 bg-white overflow-auto">
        {children}
        {showNewProjectModal && (
        <NewProjectModal onClose={() => setShowNewProjectModal(false)} />
      )}
      </main>
       
      
    </div>
    
  );
}


function NewProjectModal({
  onClose
}: {
  onClose: () => void;
}) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    visibility: 'private',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await projectsAPI.create(formData);
      toast.success('Project created successfully!');
      onClose();
      router.push(`/projects/${response.data.id}`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white w-full max-w-2xl max-h-[90vh] overflow-y-auto border-2 border-black"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="border-b border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">Create New Project</h1>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-black text-2xl font-bold leading-none"
            >
              ×
            </button>
          </div>
        </div>

        <div className="p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium mb-2">
                Project Name *
              </label>
              <input
                id="name"
                type="text"
                required
                className="input"
                placeholder="my-riscv-cpu"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
              <p className="text-sm text-gray-500 mt-1">
                Choose a descriptive name for your chip design
              </p>
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium mb-2">
                Description
              </label>
              <textarea
                id="description"
                rows={4}
                className="input resize-none"
                placeholder="A simple RISC-V CPU implementation..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-3">
                Visibility *
              </label>
              <div className="space-y-3">
                <label className="flex items-start gap-3 p-4 border border-gray-300 rounded cursor-pointer hover:border-black transition-colors">
                  <input
                    type="radio"
                    name="visibility"
                    value="private"
                    checked={formData.visibility === 'private'}
                    onChange={(e) => setFormData({ ...formData, visibility: e.target.value })}
                    className="mt-1"
                  />
                  <div>
                    <div className="font-medium">Private</div>
                    <div className="text-sm text-gray-600">
                      Only you can see and access this project
                    </div>
                  </div>
                </label>

                <label className="flex items-start gap-3 p-4 border border-gray-300 rounded cursor-pointer hover:border-black transition-colors">
                  <input
                    type="radio"
                    name="visibility"
                    value="public"
                    checked={formData.visibility === 'public'}
                    onChange={(e) => setFormData({ ...formData, visibility: e.target.value })}
                    className="mt-1"
                  />
                  <div>
                    <div className="font-medium">Public</div>
                    <div className="text-sm text-gray-600">
                      Anyone can view this project
                    </div>
                  </div>
                </label>
              </div>
            </div>

            <div className="flex gap-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="btn-primary px-8 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Project'}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="btn-secondary px-8"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
