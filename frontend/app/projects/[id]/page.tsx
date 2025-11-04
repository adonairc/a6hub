'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { filesAPI } from '@/lib/api';
import Editor from '@monaco-editor/react';
import { FileCode, Plus, Save } from 'lucide-react';
import toast from 'react-hot-toast';
import { useToolbar } from './layout';
import ModulesSection from '@/components/ModulesSection';

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

export default function DesignPage() {
  const params = useParams();
  const projectId = parseInt(params.id as string);
  const { setToolbarActions } = useToolbar();

  const [files, setFiles] = useState<ProjectFile[]>([]);
  const [activeFile, setActiveFile] = useState<ProjectFileWithContent | null>(null);
  const [editorContent, setEditorContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showNewFileModal, setShowNewFileModal] = useState(false);

  useEffect(() => {
    loadFiles();
  }, [projectId]);

  // Set toolbar actions
  useEffect(() => {
    setToolbarActions(
      <button
        onClick={saveFile}
        disabled={!activeFile || saving}
        className="btn-secondary flex items-center gap-2 disabled:opacity-50"
      >
        <Save className="w-4 h-4" />
        {saving ? 'Saving...' : 'Save'}
      </button>
    );
  }, [activeFile, saving, setToolbarActions]);

  const loadFiles = async () => {
    try {
      const response = await filesAPI.list(projectId);
      setFiles(response.data);
    } catch (error) {
      console.error('Failed to load files:', error);
    } finally {
      setLoading(false);
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

  const deleteFile = async (fileId: number) => {
    if (!confirm('Are you sure you want to delete this file?')) return;

    try {
      await filesAPI.delete(projectId, fileId);
      await loadFiles();
      if (activeFile?.id === fileId) {
        setActiveFile(null);
        setEditorContent('');
      }
      toast.success('File deleted');
    } catch (error) {
      toast.error('Failed to delete file');
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-gray-500">Loading files...</div>
      </div>
    );
  }

  return (
    <div className="h-full flex overflow-hidden">
        {/* File tree and Modules */}
        <div className="w-80 border-r border-gray-200 bg-white overflow-auto flex flex-col">
          {/* Files Section */}
          <div className="border-b border-gray-200">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="font-semibold">Files</h3>
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
                  <br />
                  <button
                    onClick={() => setShowNewFileModal(true)}
                    className="text-blue-600 hover:underline mt-2"
                  >
                    Create your first file
                  </button>
                </div>
              ) : (
                files.map((file) => (
                  <div
                    key={file.id}
                    className={`group px-3 py-2 rounded flex items-center justify-between hover:bg-gray-100 ${
                      activeFile?.id === file.id ? 'bg-gray-100' : ''
                    }`}
                  >
                    <button
                      onClick={() => openFile(file)}
                      className="flex items-center gap-2 flex-1 text-left"
                    >
                      <FileCode className="w-4 h-4 flex-shrink-0" />
                      <span className="truncate text-sm">{file.filename}</span>
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Modules Section */}
          <div className="flex-1 overflow-hidden">
            <ModulesSection projectId={projectId} />
          </div>
        </div>

          
        {/* Editor */}
        <div className="flex-1 flex flex-col bg-white">
          {activeFile ? (
            <>
              {/* File info bar */}
              <div className="px-4 py-2 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileCode className="w-4 h-4 text-gray-600" />
                  <span className="text-sm font-medium">{activeFile.filename}</span>
                  <span className="text-xs text-gray-500">({activeFile.filepath})</span>
                </div>
                <div className="text-xs text-gray-500">
                  {editorContent.split('\n').length} lines
                </div>
              </div>

              {/* Monaco Editor */}
              <div className="flex-1">
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
                    automaticLayout: true,
                  }}
                />
              </div>
            </>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500">
              <div className="text-center">
                <FileCode className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p className="mb-2">Select a file to edit</p>
                <button
                  onClick={() => setShowNewFileModal(true)}
                  className="text-blue-600 hover:underline text-sm"
                >
                  or create a new file
                </button>
              </div>
            </div>
          )}
        </div>
          {/* New file modal */}
      {showNewFileModal && (
        <NewFileModal onClose={() => setShowNewFileModal(false)} onCreate={createFile} />
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
