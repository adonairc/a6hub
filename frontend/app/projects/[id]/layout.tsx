'use client';

import { useEffect, useState, createContext, useContext, ReactNode } from 'react';
import { useParams, usePathname } from 'next/navigation';
import Link from 'next/link';
import { projectsAPI } from '@/lib/api';
import { ArrowLeft, Lock, Globe } from 'lucide-react';
import toast from 'react-hot-toast';

interface Project {
  id: number;
  name: string;
  description: string | null;
  visibility: string;
  created_at: string;
}

interface ToolbarContextType {
  setToolbarActions: (actions: ReactNode) => void;
}

const ToolbarContext = createContext<ToolbarContextType | undefined>(undefined);

export function useToolbar() {
  const context = useContext(ToolbarContext);
  if (!context) {
    throw new Error('useToolbar must be used within ProjectLayout');
  }
  return context;
}

export default function ProjectLayout({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const pathname = usePathname();
  const projectId = parseInt(params.id as string);

  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [toolbarActions, setToolbarActions] = useState<ReactNode>(null);

  useEffect(() => {
    loadProject();
  }, [projectId]);

  // Reset toolbar actions when pathname changes
  useEffect(() => {
    setToolbarActions(null);
  }, [pathname]);

  const loadProject = async () => {
    try {
      const response = await projectsAPI.get(projectId);
      setProject(response.data);
    } catch (error) {
      toast.error('Failed to load project');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  if (!project) {
    return null;
  }

  // Determine active tab based on pathname
  const getActiveTab = () => {
    if (pathname.endsWith('/simulation')) return 'simulation';
    if (pathname.endsWith('/build')) return 'build';
    if (pathname.endsWith('/settings')) return 'settings';
    return 'design';
  };

  const activeTab = getActiveTab();

  return (
    <ToolbarContext.Provider value={{ setToolbarActions }}>
      <div className="h-screen flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 bg-white px-6 py-4">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-black mb-3"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to dashboard
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{project.name}</h1>
            {project.visibility === 'private' ? (
              <Lock className="w-5 h-5 text-gray-400" />
            ) : (
              <Globe className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>

        {/* Tabs + Toolbar Actions */}
        <div className="bg-white border-b border-gray-200">
          <div className="px-6 flex items-center justify-between">
            {/* Tabs */}
            <div className="text-sm font-medium text-gray-500">
              <ul className="flex flex-wrap -mb-px">
                <li className="me-2">
                  <Link
                    href={`/projects/${projectId}`}
                    className={`inline-block px-4 py-3 border-b-2 rounded-t-lg ${
                      activeTab === 'design'
                        ? 'text-black border-black'
                        : 'border-transparent hover:text-gray-600 hover:border-gray-300'
                    }`}
                  >
                    Editor
                  </Link>
                </li>
                <li className="me-2">
                  <Link
                    href={`/projects/${projectId}/simulation`}
                    className={`inline-block px-4 py-3 border-b-2 rounded-t-lg ${
                      activeTab === 'simulation'
                        ? 'text-black border-black'
                        : 'border-transparent hover:text-gray-600 hover:border-gray-300'
                    }`}
                  >
                    Simulation
                  </Link>
                </li>
                <li className="me-2">
                  <Link
                    href={`/projects/${projectId}/build`}
                    className={`inline-block px-4 py-3 border-b-2 rounded-t-lg ${
                      activeTab === 'build'
                        ? 'text-black border-black'
                        : 'border-transparent hover:text-gray-600 hover:border-gray-300'
                    }`}
                  >
                    Build
                  </Link>
                </li>
                <li className="me-2">
                  <Link
                    href={`/projects/${projectId}/settings`}
                    className={`inline-block px-4 py-3 border-b-2 rounded-t-lg ${
                      activeTab === 'settings'
                        ? 'text-black border-black'
                        : 'border-transparent hover:text-gray-600 hover:border-gray-300'
                    }`}
                  >
                    Settings
                  </Link>
                </li>
              </ul>
            </div>

            {/* Toolbar Actions from child pages */}
            {toolbarActions && (
              <div className="flex items-center gap-2 py-2">{toolbarActions}</div>
            )}
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-hidden">{children}</div>
      </div>
    </ToolbarContext.Provider>
  );
}
