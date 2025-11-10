'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams } from 'next/navigation';
import { filesAPI } from '@/lib/api';
import Editor from '@monaco-editor/react';
import { FileCode, Plus, Save, Trash2, Upload, Edit2 } from 'lucide-react';
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
  const editorRef = useRef<any>(null);

  const [files, setFiles] = useState<ProjectFile[]>([]);
  const [activeFile, setActiveFile] = useState<ProjectFileWithContent | null>(null);
  const [editorContent, setEditorContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showNewFileModal, setShowNewFileModal] = useState(false);
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [fileToRename, setFileToRename] = useState<ProjectFile | null>(null);
  const [uploading, setUploading] = useState(false);
  const [showGdsViewer, setShowGdsViewer] = useState(false);
  const [gdsViewerHeight, setGdsViewerHeight] = useState(400);
  const [authToken, setAuthToken] = useState<string>('');
  const [isRunning, setIsRunning] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const resizeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadFiles();
    // Get auth token from localStorage
    const token = localStorage.getItem('token');
    if (token) {
      setAuthToken(token);
    }
  }, [projectId]);

  // Show GDS viewer when Python file is active
  useEffect(() => {
    if (activeFile && activeFile.filename.endsWith('.py')) {
      setShowGdsViewer(true);
    } else {
      setShowGdsViewer(false);
    }
  }, [activeFile]);

  // Use useCallback to prevent stale closures
  const saveFile = useCallback(async () => {
    if (!activeFile) return;

    setSaving(true);
    try {
      await filesAPI.update(projectId, activeFile.id, { content: editorContent });
      toast.success('File saved');
    } catch (error) {
      toast.error('Failed to save file');
      console.error('Save error:', error);
    } finally {
      setSaving(false);
    }
  }, [projectId, activeFile, editorContent]);

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
  }, [activeFile, saving, saveFile, setToolbarActions]);

  const loadFiles = async () => {
    try {
      const response = await filesAPI.list(projectId);
      const filesList = response.data;
      setFiles(filesList);

      // Auto-select top.v if it exists and no file is currently active
      if (!activeFile && filesList.length > 0) {
        const topVFile = filesList.find((f: ProjectFile) => f.filename === 'top.v');
        if (topVFile) {
          await openFile(topVFile);
        }
      }
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

  const deleteFile = async (fileId: number, filename: string) => {
    if (!confirm(`Are you sure you want to delete "${filename}"? This action cannot be undone.`)) return;

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

  const renameFile = async (fileId: number, newFilename: string) => {
    try {
      await filesAPI.update(projectId, fileId, { filename: newFilename });
      await loadFiles();
      if (activeFile?.id === fileId) {
        setActiveFile({ ...activeFile, filename: newFilename });
      }
      setShowRenameModal(false);
      setFileToRename(null);
      toast.success('File renamed');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to rename file');
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      await filesAPI.upload(projectId, file);
      await loadFiles();
      toast.success(`${file.name} uploaded successfully`);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleModuleClick = useCallback((fileId: number, startLine: number | null) => {
    // Find and open the file if not already open
    const file = files.find(f => f.id === fileId);
    if (!file) return;

    const navigateToLine = () => {
      if (startLine && editorRef.current) {
        // Navigate to the line in the editor
        editorRef.current.revealLineInCenter(startLine);
        editorRef.current.setPosition({ lineNumber: startLine, column: 1 });
        editorRef.current.focus();
      }
    };

    if (activeFile?.id !== fileId) {
      // Open file first, then navigate
      openFile(file).then(() => {
        setTimeout(navigateToLine, 100); // Small delay for editor to render
      });
    } else {
      // File already open, just navigate
      navigateToLine();
    }
  }, [files, activeFile, openFile]);

  const handleEditorMount = (editor: any) => {
    editorRef.current = editor;
  };

  // Handle GDS viewer resize
  const handleResizeMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    const startY = e.clientY;
    const startHeight = gdsViewerHeight;

    const handleMouseMove = (e: MouseEvent) => {
      const delta = startY - e.clientY;
      const newHeight = Math.max(200, Math.min(800, startHeight + delta));
      setGdsViewerHeight(newHeight);
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  // Get GDS filename from Python filename
  const getGdsFilename = (pythonFilename: string): string => {
    const baseName = pythonFilename.replace(/\.py$/, '');
    return `${baseName}.gds`;
  };

  // Run Python script to generate GDS
  const runPythonScript = async () => {
    if (!activeFile) return;

    setIsRunning(true);
    try {
      const response = await filesAPI.update(projectId, activeFile.id, {
        content: editorContent
      });

      // Trigger script execution
      const runResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/projects/${projectId}/files/${activeFile.id}/run`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`,
          },
        }
      );

      if (!runResponse.ok) {
        throw new Error('Failed to run script');
      }

      const result = await runResponse.json();
      toast.success('Script execution started! GDS file will be generated.');

      // Reload the GDS viewer after a delay
      setTimeout(() => {
        // Force iframe reload
        const iframe = document.querySelector('iframe[title="KLayout GDS Viewer"]') as HTMLIFrameElement;
        if (iframe) {
          iframe.src = iframe.src;
        }
      }, 3000);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to run script');
      console.error('Run error:', error);
    } finally {
      setIsRunning(false);
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
      {/* File tree - Left Column */}
      <div className="w-64 border-r border-gray-200 bg-white overflow-auto flex-shrink-0">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="font-semibold">Files</h3>
          <div className="flex gap-1">
            <button
              onClick={handleUploadClick}
              disabled={uploading}
              className="p-1 hover:bg-gray-100 rounded disabled:opacity-50"
              title="Upload file"
            >
              <Upload className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowNewFileModal(true)}
              className="p-1 hover:bg-gray-100 rounded"
              title="New file"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </div>
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileUpload}
          className="hidden"
          accept=".v,.sv,.vh,.verilog,.systemverilog"
        />
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
                className={`group px-3 py-2 rounded flex items-center gap-2 hover:bg-gray-100 ${
                  activeFile?.id === file.id ? 'bg-gray-100' : ''
                }`}
              >
                <button
                  onClick={() => openFile(file)}
                  className="flex items-center gap-2 flex-1 text-left min-w-0"
                >
                  <FileCode className="w-4 h-4 flex-shrink-0" />
                  <span className="truncate text-sm">{file.filename}</span>
                </button>
                <div className="opacity-0 group-hover:opacity-100 flex gap-1 transition-opacity">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setFileToRename(file);
                      setShowRenameModal(true);
                    }}
                    className="p-1 hover:bg-blue-100 rounded flex-shrink-0"
                    title="Rename file"
                  >
                    <Edit2 className="w-3 h-3 text-blue-600" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteFile(file.id, file.filename);
                    }}
                    className="p-1 hover:bg-red-100 rounded flex-shrink-0"
                    title="Delete file"
                  >
                    <Trash2 className="w-3 h-3 text-red-600" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Editor - Middle Column */}
      <div className="flex-1 flex flex-col bg-white overflow-hidden">
        {activeFile ? (
          <>
            {/* File info bar */}
            <div className="px-4 py-2 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-gray-600" />
                <span className="text-sm font-medium">{activeFile.filename}</span>
                <span className="text-xs text-gray-500">({activeFile.filepath})</span>
                {activeFile.filename.endsWith('.py') && (
                  <button
                    onClick={() => setShowGdsViewer(!showGdsViewer)}
                    className="ml-2 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    {showGdsViewer ? 'Hide' : 'Show'} GDS Viewer
                  </button>
                )}
              </div>
              <div className="text-xs text-gray-500">
                {editorContent.split('\n').length} lines
              </div>
            </div>

            {/* Monaco Editor */}
            <div className={showGdsViewer ? 'flex-1 flex flex-col overflow-hidden' : 'flex-1'}>
              <div className={showGdsViewer ? `flex-shrink-0` : 'h-full'} style={showGdsViewer ? { height: `calc(100% - ${gdsViewerHeight}px - 4px)` } : {}}>
                <Editor
                  height="100%"
                  defaultLanguage={activeFile.filename.endsWith('.py') ? 'python' : 'verilog'}
                  theme="vs-dark"
                  value={editorContent}
                  onChange={(value) => setEditorContent(value || '')}
                  onMount={handleEditorMount}
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

              {/* GDS Viewer - shown below editor for Python files */}
              {showGdsViewer && (
                <>
                  {/* Resize handle */}
                  <div
                    ref={resizeRef}
                    onMouseDown={handleResizeMouseDown}
                    className="h-1 bg-gray-200 hover:bg-blue-400 cursor-ns-resize flex items-center justify-center group"
                  >
                    <div className="w-12 h-0.5 bg-gray-400 group-hover:bg-blue-500 rounded"></div>
                  </div>

                  {/* GDS Viewer */}
                  <div className="flex-shrink-0 bg-gray-900 overflow-hidden" style={{ height: `${gdsViewerHeight}px` }}>
                    <div className="h-full flex flex-col">
                      <div className="px-4 py-2 bg-gray-800 border-b border-gray-700 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                          <span className="text-sm font-medium text-white">KLayout GDS Viewer</span>
                          <span className="text-xs text-gray-400">({getGdsFilename(activeFile.filename)})</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={runPythonScript}
                            disabled={isRunning}
                            className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                          >
                            {isRunning ? (
                              <>
                                <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                Running...
                              </>
                            ) : (
                              '▶ Run'
                            )}
                          </button>
                          <button
                            onClick={() => setShowGdsViewer(false)}
                            className="text-gray-400 hover:text-white text-sm"
                          >
                            Hide
                          </button>
                        </div>
                      </div>
                      <div className="flex-1 bg-white">
                        <iframe
                          src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/kweb/gds/${projectId}/${getGdsFilename(activeFile.filename)}?token=${encodeURIComponent(authToken)}`}
                          className="w-full h-full border-0"
                          title="KLayout GDS Viewer"
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}
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

      {/* Design Modules - Right Column */}
      <div className="w-96 border-l border-gray-200 bg-white overflow-auto flex-shrink-0">
        <ModulesSection
          projectId={projectId}
          onModuleClick={handleModuleClick}
          horizontal={false}
        />
      </div>

      {/* New file modal */}
      {showNewFileModal && (
        <NewFileModal onClose={() => setShowNewFileModal(false)} onCreate={createFile} />
      )}

      {/* Rename file modal */}
      {showRenameModal && fileToRename && (
        <RenameFileModal
          file={fileToRename}
          onClose={() => {
            setShowRenameModal(false);
            setFileToRename(null);
          }}
          onRename={renameFile}
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

function RenameFileModal({
  file,
  onClose,
  onRename,
}: {
  file: ProjectFile;
  onClose: () => void;
  onRename: (fileId: number, newFilename: string) => void;
}) {
  const [filename, setFilename] = useState(file.filename);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (filename.trim() && filename !== file.filename) {
      onRename(file.id, filename.trim());
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white p-6 w-full max-w-md border border-gray-300">
        <h3 className="text-xl font-bold mb-4">Rename File</h3>
        <form onSubmit={handleSubmit}>
          <div className="mb-2">
            <label className="block text-sm text-gray-600 mb-1">Current name: {file.filename}</label>
          </div>
          <input
            type="text"
            placeholder="New filename"
            className="input mb-4"
            value={filename}
            onChange={(e) => setFilename(e.target.value)}
            autoFocus
          />
          <div className="flex gap-2">
            <button type="submit" className="btn-primary flex-1">
              Rename
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
