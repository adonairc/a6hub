'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { projectsAPI } from '@/lib/api';
import { FolderOpen, Plus, Lock, Globe, Search } from 'lucide-react';
import toast from 'react-hot-toast';

interface Project {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  visibility: string;
  created_at: string;
  owner_id: number;
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [publicProjects, setPublicProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'my' | 'public'>('my');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const [myProjectsRes, publicProjectsRes] = await Promise.all([
        projectsAPI.list({ limit: 50 }),
        projectsAPI.listPublic({ limit: 50 }),
      ]);
      setProjects(myProjectsRes.data);
      setPublicProjects(publicProjectsRes.data);
    } catch (error) {
      toast.error('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const displayProjects = activeTab === 'my' ? projects : publicProjects;
  const filteredProjects = displayProjects.filter((p) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="min-h-screen bg-white">
      <div className="border-b border-gray-200">
        <div className="container mx-auto px-8 py-6">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-bold">Projects</h1>
            <Link href="/projects/new" className="btn-primary flex items-center gap-2">
              <Plus className="w-4 h-4" />
              New Project
            </Link>
          </div>

          {/* Tabs */}
          <div className="flex gap-6 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('my')}
              className={`pb-3 px-1 font-medium transition-colors relative ${
                activeTab === 'my' ? 'text-black' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              My Projects ({projects.length})
              {activeTab === 'my' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-black" />
              )}
            </button>
            <button
              onClick={() => setActiveTab('public')}
              className={`pb-3 px-1 font-medium transition-colors relative ${
                activeTab === 'public' ? 'text-black' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Public Projects ({publicProjects.length})
              {activeTab === 'public' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-black" />
              )}
            </button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-8 py-8">
        {/* Search */}
        <div className="mb-8">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search projects..."
              className="input pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Projects Grid */}
        {loading ? (
          <div className="text-gray-500">Loading projects...</div>
        ) : filteredProjects.length === 0 ? (
          <div className="card text-center py-12">
            <FolderOpen className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-xl font-semibold mb-2">
              {searchQuery ? 'No projects found' : 'No projects yet'}
            </h3>
            <p className="text-gray-600 mb-6">
              {searchQuery
                ? 'Try adjusting your search'
                : activeTab === 'my'
                ? 'Create your first project to get started'
                : 'No public projects available'}
            </p>
            {activeTab === 'my' && !searchQuery && (
              <Link href="/projects/new" className="btn-primary inline-flex items-center gap-2">
                <Plus className="w-4 h-4" />
                Create Project
              </Link>
            )}
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map((project) => (
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

                <div className="text-sm text-gray-500">
                  {new Date(project.created_at).toLocaleDateString()}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
