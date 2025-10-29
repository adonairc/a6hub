'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { projectsAPI } from '@/lib/api';
import { FolderOpen, Plus, Clock, Lock, Globe } from 'lucide-react';
import toast from 'react-hot-toast';

interface Project {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  visibility: string;
  created_at: string;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await projectsAPI.list({ limit: 10 });
      setProjects(response.data);
    } catch (error) {
      toast.error('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Welcome back, {user?.username}</h1>
        <p className="text-gray-600">Manage your chip design projects</p>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-3 gap-6 mb-12">
        <Link
          href="/projects/new"
          className="card hover:border-black transition-colors cursor-pointer group"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-black text-white flex items-center justify-center group-hover:bg-gray-800 transition-colors">
              <Plus className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-semibold">New Project</h3>
          </div>
          <p className="text-gray-600">Start a new chip design project</p>
        </Link>

        <Link
          href="/projects"
          className="card hover:border-black transition-colors cursor-pointer group"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 border border-black flex items-center justify-center group-hover:bg-black group-hover:text-white transition-colors">
              <FolderOpen className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-semibold">Browse Projects</h3>
          </div>
          <p className="text-gray-600">View all your projects</p>
        </Link>

        <Link
          href="/projects?filter=public"
          className="card hover:border-black transition-colors cursor-pointer group"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 border border-black flex items-center justify-center group-hover:bg-black group-hover:text-white transition-colors">
              <Globe className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-semibold">Explore Public</h3>
          </div>
          <p className="text-gray-600">Discover community projects</p>
        </Link>
      </div>

      {/* Recent Projects */}
      <div>
        <h2 className="text-2xl font-bold mb-6">Recent Projects</h2>
        
        {loading ? (
          <div className="text-gray-500">Loading projects...</div>
        ) : projects.length === 0 ? (
          <div className="card text-center py-12">
            <FolderOpen className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-xl font-semibold mb-2">No projects yet</h3>
            <p className="text-gray-600 mb-6">Create your first project to get started</p>
            <Link href="/projects/new" className="btn-primary inline-flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Create Project
            </Link>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <Link
                key={project.id}
                href={`/projects/${project.id}`}
                className="card hover:border-black transition-colors group"
              >
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-xl font-semibold group-hover:underline">{project.name}</h3>
                  {project.visibility === 'private' ? (
                    <Lock className="w-4 h-4 text-gray-400" />
                  ) : (
                    <Globe className="w-4 h-4 text-gray-400" />
                  )}
                </div>
                
                {project.description && (
                  <p className="text-gray-600 mb-4 line-clamp-2">{project.description}</p>
                )}
                
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Clock className="w-4 h-4" />
                  <span>{new Date(project.created_at).toLocaleDateString()}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
