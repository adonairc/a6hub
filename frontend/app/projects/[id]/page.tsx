'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { projectsAPI, filesAPI, jobsAPI } from '@/lib/api';
import Editor from '@monaco-editor/react';
import {
  ArrowLeft,
  FileCode,
  Plus,
  Play,
  Settings,
  Trash2,
  Save,
  Lock,
  Globe,
  Folder,
  FolderOpen,
} from 'lucide-react';
import toast from 'react-hot-toast';

interface Project {
  id: number;
  name: string;
  description: string | null;
  visibility: string;
  created_at: string;
}

interface ProjectFile {
  id: number;
  filename: string;
  filepath: string;
  size_bytes: number;
  created_at: string;
}

interface ProjectFileWithContent extends ProjectFile {
  content: string;
}

export default function ProjectPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = parseInt(params.id as string);

  const [project, setProject] = useState<Project | null>(null);
  const [files, setFiles] = useState<ProjectFile[]>([]);
  const [activeFile, setActiveFile] = useState<ProjectFileWithContent | null>(null);
  const [editorContent, setEditorContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showNewFileModal, setShowNewFileModal] = useState(false);

  useEffect(() => {
    loadProject();
    loadFiles();
  }, [projectId]);

  const loadProject = async () => {
    try {
      const response = await projectsAPI.get(projectId);
      setProject(response.data);
    } catch (error) {
      toast.error('Failed to load project');
      router.push('/projects');
    } finally {
      setLoading(false);
    }
  };

  const loadFiles = async () => {
    try {
      const response = await filesAPI.list(projectId);
      setFiles(response.data);
    } catch (error) {
      console.error('Failed to load files:', error);
    }
  };

  const openFile = async (file: ProjectFile) => {
    try {
      const response = await filesAPI.get(projectId, file.id);
      const fileWithContent = response.data;
      setActiveFile(fileWithContent);
      setEditorContent(fileWithContent.content || '');
    } catch (error) {
      toast.error('Failed to open file');
    }
  };

  const saveFile = async () => {
    if (!activeFile) return;

    setSaving(true);
    try {
      await filesAPI.update(projectId, activeFile.id, { content: editorContent });
      toast.success('File saved');
    } catch (error) {
      toast.error('Failed to save file');
    } finally {
      setSaving(false);
    }
  };

  const createFile = async (filename: string) => {
    try {
      const response = await filesAPI.create(projectId, {
        filename,
        filepath: `src/${filename}`,
        content: '// New file\n',
        mime_type: 'text/plain',
      });
      await loadFiles();
      await openFile(response.data);
      setShowNewFileModal(false);
      toast.success('File created');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create file');
    }
  };

  const runSimulation = async () => {
    try {
      await jobsAPI.create(projectId, {
        job_type: 'simulation',
        config: { simulator: 'verilator' },
      });
      toast.success('Simulation started');
    } catch (error) {
      toast.error('Failed to start simulation');
    }
  };

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  if (!project) {
    return null;
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white">
        <div className="px-6 py-4">
          <Link href="/projects" className="inline-flex items-center gap-2 text-gray-600 hover:text-black mb-3">
            <ArrowLeft className="w-4 h-4" />
            Back to projects
          </Link>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{project.name}</h1>
              {project.visibility === 'private' ? (
                <Lock className="w-5 h-5 text-gray-400" />
              ) : (
                <Globe className="w-5 h-5 text-gray-400" />
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={saveFile}
                disabled={!activeFile || saving}
                className="btn-secondary flex items-center gap-2 disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button
                onClick={runSimulation}
                className="btn-primary flex items-center gap-2"
              >
                <Play className="w-4 h-4" />
                Run Simulation
              </button>
            </div>
          </div>
        </div>
      </div>

     {/* Tabs */}
     <div className="border-b border-gray-200 bg-white">
<div className="text-sm font-medium text-center text-gray-500 border-b border-gray-200">
    <ul className="flex flex-wrap -mb-px">
       <li className="me-2">
            <Link href={`/projects/${projectId}`} className="inline-block p-4 text-black border-b-2 border-black rounded-t-lg active">Design</Link>
        </li>
        <li className="me-2">
            <a href="#" className="inline-block p-4 border-b-2 border-transparent rounded-t-lg hover:text-gray-600 hover:border-gray-300">Simulation</a>
        </li>
        <li className="me-2">
            <Link href={`/projects/${projectId}/build`} className="inline-block p-4 border-b-2 border-transparent rounded-t-lg hover:text-gray-600 hover:border-gray-300">Build</Link>
        </li>
        <li className="me-2">
            <a href="#" className="inline-block p-4 border-b-2 border-transparent rounded-t-lg hover:text-gray-600 hover:border-gray-300">Settings</a>
        </li>
    </ul>
</div>
     </div>
      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* File tree */}
        <div className="w-64 border-r border-gray-200 bg-white overflow-auto">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h3 className="font-semibold">Modules</h3>
            <button
              onClick={() => setShowNewFileModal(true)}
              className="p-1 hover:bg-gray-100 rounded"
              title="New file"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
          <div className="p-2">
            {files.length === 0 ? (
              <div className="text-sm text-gray-500 p-4 text-center">
                No files yet
              </div>
            ) : (
              files.map((file) => (
                <button
                  key={file.id}
                  onClick={() => openFile(file)}
                  className={`w-full text-left px-3 py-2 rounded flex items-center gap-2 hover:bg-gray-100 ${
                    activeFile?.id === file.id ? 'bg-gray-100' : ''
                  }`}
                >
                  <FileCode className="w-4 h-4 flex-shrink-0" />
                  <span className="truncate text-sm">{file.filename}</span>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Editor */}
        <div className="flex-1 bg-white">
          {activeFile ? (
            <Editor
              height="100%"
              defaultLanguage="verilog"
              theme="vs-dark"
              value={editorContent}
              onChange={(value) => setEditorContent(value || '')}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                wordWrap: 'on',
                scrollBeyondLastLine: false,
              }}
            />
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500">
              <div className="text-center">
                <FileCode className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p>Select a file to edit or create a new one</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* New file modal */}
      {showNewFileModal && (
        <NewFileModal
          onClose={() => setShowNewFileModal(false)}
          onCreate={createFile}
        />
      )}
    </div>
  );
}

function NewFileModal({
  onClose,
  onCreate,
}: {
  onClose: () => void;
  onCreate: (filename: string) => void;
}) {
  const [filename, setFilename] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (filename.trim()) {
      onCreate(filename.trim());
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white p-6 w-full max-w-md border border-gray-300">
        <h3 className="text-xl font-bold mb-4">New File</h3>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="filename.v"
            className="input mb-4"
            value={filename}
            onChange={(e) => setFilename(e.target.value)}
            autoFocus
          />
          <div className="flex gap-2">
            <button type="submit" className="btn-primary flex-1">
              Create
            </button>
            <button type="button" onClick={onClose} className="btn-secondary flex-1">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
