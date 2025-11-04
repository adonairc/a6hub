import React, { useEffect, useState } from 'react';
import { modulesAPI } from '@/lib/api';
import { Box, Code, FileText, Cpu, PenTool, RefreshCw, Search, ChevronRight } from 'lucide-react';
import toast from 'react-hot-toast';

interface Module {
  id: number;
  name: string;
  module_type: string;
  description: string | null;
  file_id: number;
  filename: string;
  filepath: string;
  metadata: any;
}

interface ModulesSectionProps {
  projectId: number;
}

const moduleTypeIcons: Record<string, { icon: any; label: string; color: string }> = {
  verilog_module: { icon: Cpu, label: 'Verilog Module', color: 'text-blue-600' },
  verilog_package: { icon: Box, label: 'SV Package', color: 'text-purple-600' },
  python_class: { icon: Code, label: 'Python Class', color: 'text-green-600' },
  python_function: { icon: PenTool, label: 'Python Function', color: 'text-yellow-600' },
  spice_subcircuit: { icon: Cpu, label: 'SPICE Subcircuit', color: 'text-orange-600' },
};

export default function ModulesSection({ projectId }: ModulesSectionProps) {
  const [modules, setModules] = useState<Module[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [expandedModule, setExpandedModule] = useState<number | null>(null);

  useEffect(() => {
    loadModules();
  }, [projectId]);

  const loadModules = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (selectedType !== 'all') {
        params.module_type = selectedType;
      }
      if (searchTerm) {
        params.search = searchTerm;
      }

      const response = await modulesAPI.listModules(projectId, params);
      setModules(response.data);
    } catch (error: any) {
      console.error('Error loading modules:', error);
      toast.error('Failed to load modules');
    } finally {
      setLoading(false);
    }
  };

  const handleReparse = async () => {
    try {
      toast.loading('Re-parsing project files...');
      await modulesAPI.reparseProject(projectId);
      toast.dismiss();
      toast.success('Files re-parsed successfully');
      loadModules();
    } catch (error: any) {
      toast.dismiss();
      toast.error('Failed to re-parse files');
    }
  };

  const filteredModules = modules.filter((module) => {
    const matchesSearch = searchTerm === '' || module.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = selectedType === 'all' || module.module_type === selectedType;
    return matchesSearch && matchesType;
  });

  const modulesByFile = filteredModules.reduce((acc, module) => {
    if (!acc[module.filename]) {
      acc[module.filename] = [];
    }
    acc[module.filename].push(module);
    return acc;
  }, {} as Record<string, Module[]>);

  const getModuleIcon = (moduleType: string) => {
    const config = moduleTypeIcons[moduleType] || moduleTypeIcons.verilog_module;
    const Icon = config.icon;
    return <Icon className={`w-4 h-4 ${config.color}`} />;
  };

  const renderModuleMetadata = (module: Module) => {
    if (!module.metadata) return null;

    // Verilog module metadata
    if (module.module_type === 'verilog_module' && module.metadata.ports) {
      return (
        <div className="mt-2 space-y-1 text-xs">
          <div className="font-semibold text-gray-700">Ports:</div>
          <div className="grid grid-cols-2 gap-1">
            {module.metadata.ports.slice(0, 6).map((port: any, idx: number) => (
              <div key={idx} className="text-gray-600">
                <span className="font-mono text-xs">
                  {port.direction === 'input' && <span className="text-blue-600">←</span>}
                  {port.direction === 'output' && <span className="text-green-600">→</span>}
                  {port.direction === 'inout' && <span className="text-purple-600">↔</span>}
                  {' '}{port.name}
                  {port.range && ` ${port.range}`}
                </span>
              </div>
            ))}
            {module.metadata.ports.length > 6 && (
              <div className="text-gray-500">+{module.metadata.ports.length - 6} more...</div>
            )}
          </div>
        </div>
      );
    }

    // Python class metadata
    if (module.module_type === 'python_class' && module.metadata.methods) {
      return (
        <div className="mt-2 space-y-1 text-xs">
          <div className="font-semibold text-gray-700">Methods:</div>
          <div className="flex flex-wrap gap-1">
            {module.metadata.methods.slice(0, 5).map((method: any, idx: number) => (
              <span key={idx} className="px-2 py-0.5 bg-gray-100 rounded text-gray-700 font-mono text-xs">
                {method.name}()
              </span>
            ))}
            {module.metadata.methods.length > 5 && (
              <span className="px-2 py-0.5 text-gray-500">+{module.metadata.methods.length - 5} more</span>
            )}
          </div>
        </div>
      );
    }

    return null;
  };

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 p-6">
        <div className="text-center text-gray-500">Loading modules...</div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Box className="w-5 h-5 text-gray-700" />
            <h2 className="text-lg font-semibold">Design Modules</h2>
            <span className="text-sm text-gray-500">({filteredModules.length})</span>
          </div>
          <button
            onClick={handleReparse}
            className="flex items-center gap-1 px-3 py-1.5 text-sm border border-gray-300 hover:bg-gray-50 rounded"
            title="Re-parse all files"
          >
            <RefreshCw className="w-4 h-4" />
            Re-parse
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search modules..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded text-sm"
            />
          </div>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="border border-gray-300 rounded px-3 py-2 text-sm"
          >
            <option value="all">All Types</option>
            <option value="verilog_module">Verilog Modules</option>
            <option value="python_class">Python Classes</option>
            <option value="python_function">Python Functions</option>
          </select>
        </div>
      </div>

      {/* Modules List */}
      <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
        {Object.keys(modulesByFile).length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Box className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p className="mb-2">No modules found</p>
            <p className="text-sm">Modules are automatically extracted from .v, .sv, and .py files</p>
          </div>
        ) : (
          Object.entries(modulesByFile).map(([filename, fileModules]) => (
            <div key={filename} className="p-4 hover:bg-gray-50">
              <div className="flex items-center gap-2 mb-2 text-sm text-gray-600">
                <FileText className="w-4 h-4" />
                <span className="font-medium">{filename}</span>
                <span className="text-xs text-gray-400">({fileModules.length} module{fileModules.length > 1 ? 's' : ''})</span>
              </div>

              <div className="space-y-2 ml-6">
                {fileModules.map((module) => (
                  <div
                    key={module.id}
                    className="border border-gray-200 rounded p-3 hover:border-gray-300 cursor-pointer"
                    onClick={() => setExpandedModule(expandedModule === module.id ? null : module.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-2 flex-1">
                        {getModuleIcon(module.module_type)}
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-semibold">{module.name}</span>
                            <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                              {moduleTypeIcons[module.module_type]?.label || module.module_type}
                            </span>
                          </div>
                          {module.description && (
                            <p className="text-xs text-gray-600 mt-1">{module.description}</p>
                          )}
                          {expandedModule === module.id && renderModuleMetadata(module)}
                        </div>
                      </div>
                      <ChevronRight
                        className={`w-4 h-4 text-gray-400 transition-transform ${
                          expandedModule === module.id ? 'rotate-90' : ''
                        }`}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
