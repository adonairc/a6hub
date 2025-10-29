'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { Home, FolderOpen, Settings, LogOut, Plus } from 'lucide-react';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

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
          <Link
            href="/projects"
            className="flex items-center gap-3 px-4 py-3 rounded hover:bg-gray-900 transition-colors mb-2"
          >
            <FolderOpen className="w-5 h-5" />
            <span>Projects</span>
          </Link>
          
          <div className="my-6">
            <Link
              href="/projects/new"
              className="flex items-center gap-2 px-4 py-2 bg-white text-black rounded hover:bg-gray-100 transition-colors justify-center font-medium"
            >
              <Plus className="w-4 h-4" />
              New Project
            </Link>
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
      </main>
    </div>
  );
}
