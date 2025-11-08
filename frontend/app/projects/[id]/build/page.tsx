'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { buildsAPI } from '@/lib/api';
import { Play, CheckCircle, XCircle, Clock, Loader, Terminal } from 'lucide-react';
import toast from 'react-hot-toast';
import { useBuildWebSocket } from '@/hooks/useBuildWebSocket';
import { BuildProgressMessage } from '@/lib/websocket';

interface LibreLaneFlowConfig {
  design_name: string;
  verilog_files: string[];
  pdk: string;
  clock_period: string;
  clock_port: string;
  pl_target_density: string;
  fp_core_util: number;
  fp_aspect_ratio: number;
  synth_strategy: string;
  synth_max_fanout: number;
  run_drc: boolean;
  run_lvs: boolean;
  use_docker: boolean;
  docker_image: string;
}

interface BuildPreset {
  name: string;
  description: string;
  config: LibreLaneFlowConfig;
}

interface BuildStatus {
  job_id: number;
  status: string;
  current_step?: string;
  logs?: string;
}

const PDK_OPTIONS = [
  { value: 'sky130_fd_sc_hd', label: 'Sky130 HD - High Density' },
  { value: 'sky130_fd_sc_hs', label: 'Sky130 HS - High Speed' },
  { value: 'sky130_fd_sc_ms', label: 'Sky130 MS - Medium Speed' },
  { value: 'sky130_fd_sc_ls', label: 'Sky130 LS - Low Speed' },
  { value: 'gf180mcuC', label: 'GF180MCU' },
];

export default function BuildPage() {
  const params = useParams();
  const projectId = parseInt(params.id as string);

  const [config, setConfig] = useState<LibreLaneFlowConfig | null>(null);
  const [presets, setPresets] = useState<Record<string, BuildPreset>>({});
  const [buildStatus, setBuildStatus] = useState<BuildStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [building, setBuilding] = useState(false);
  const [activeTab, setActiveTab] = useState<'basic' | 'advanced'>('basic');
  const [buildLogs, setBuildLogs] = useState<string[]>([]);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [showLogs, setShowLogs] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // WebSocket connection for real-time updates
  const { isConnected, lastMessage } = useBuildWebSocket({
    jobId: buildStatus?.job_id || null,
    enabled: buildStatus?.status === 'running',
    onMessage: handleBuildMessage,
  });

  useEffect(() => {
    loadBuildConfig();
    loadPresets();
    loadBuildStatus();
  }, [projectId]);

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (showLogs && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [buildLogs, showLogs]);

  function handleBuildMessage(message: BuildProgressMessage) {
    switch (message.type) {
      case 'connected':
        console.log('WebSocket connected');
        break;

      case 'status':
        if (message.status) {
          setBuildStatus((prev) => prev ? { ...prev, status: message.status! } : null);
        }
        if (message.step) {
          setCurrentStep(message.step);
        }
        break;

      case 'log':
        if (message.message) {
          setBuildLogs((prev) => [...prev, message.message!]);
        }
        break;

      case 'complete':
        setBuildStatus((prev) => prev ? { ...prev, status: 'completed' } : null);
        setCurrentStep('Build completed');
        toast.success('Build completed successfully!');
        // Show logs panel
        setShowLogs(true);
        break;

      case 'error':
        setBuildStatus((prev) => prev ? { ...prev, status: 'failed' } : null);
        setCurrentStep('Build failed');
        toast.error(message.message || 'Build failed');
        // Show logs panel
        setShowLogs(true);
        break;
    }
  }

  const loadBuildConfig = async () => {
    try {
      const response = await buildsAPI.getConfig(projectId);
      setConfig(response.data);
    } catch (error) {
      console.error('Failed to load build config:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPresets = async () => {
    try {
      const response = await buildsAPI.getPresets();
      setPresets(response.data);
    } catch (error) {
      console.error('Failed to load presets:', error);
    }
  };

  const loadBuildStatus = async () => {
    try {
      const response = await buildsAPI.getStatus(projectId);
      setBuildStatus(response.data);
    } catch (error) {
      // No previous builds
      setBuildStatus(null);
    }
  };

  const applyPreset = (presetKey: string) => {
    const preset = presets[presetKey];
    if (preset && config) {
      setConfig({ ...config, ...preset.config });
      toast.success(`Applied ${preset.name} preset`);
    }
  };

  const startBuild = async () => {
    if (!config) return;

    setBuilding(true);
    setBuildLogs([]);
    setCurrentStep('');
    setShowLogs(true);

    try {
      await buildsAPI.startBuild(projectId, { config });
      toast.success('Build started! Watch the progress below.');
      await loadBuildStatus();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to start build');
    } finally {
      setBuilding(false);
    }
  };

  const updateConfig = (updates: Partial<LibreLaneFlowConfig>) => {
    if (config) {
      setConfig({ ...config, ...updates });
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!config) {
    return null;
  }

  return (
    <div className="h-full bg-gray-50 overflow-auto">
      {/* Toolbar */}
      <div className="border-b border-gray-200 bg-white px-6 py-3 sticky top-0 z-10">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">ASIC Build Configuration</h2>
          <button
            onClick={startBuild}
            disabled={building}
            className="btn-primary flex items-center gap-2"
          >
            {building ? (
              <>
                <Loader className="w-4 h-4 animate-spin" />
                Starting Build...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Start Build
              </>
            )}
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        {/* Live Build Logs */}
        {showLogs && buildStatus && (
          <div className="mb-6 bg-gray-900 border border-gray-700 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-green-400" />
                <span className="text-sm font-medium text-gray-200">Build Logs - Job #{buildStatus.job_id}</span>
                {isConnected && (
                  <span className="flex items-center gap-1 text-xs text-green-400">
                    <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                    Live
                  </span>
                )}
              </div>
              <button
                onClick={() => setShowLogs(false)}
                className="text-xs text-gray-400 hover:text-white"
              >
                Hide
              </button>
            </div>
            <div className="h-96 overflow-y-auto p-4 font-mono text-xs text-gray-300">
              {currentStep && (
                <div className="text-blue-400 mb-2">→ {currentStep}</div>
              )}
              {buildLogs.map((log, index) => (
                <div key={index} className="whitespace-pre-wrap">
                  {log}
                </div>
              ))}
              {buildLogs.length === 0 && (
                <div className="text-gray-500">Waiting for build output...</div>
              )}
              <div ref={logsEndRef} />
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main configuration panel */}
          <div className="lg:col-span-2 space-y-6">
            {/* Presets */}
            <div className="bg-white border border-gray-200 p-6">
              <h2 className="text-lg font-semibold mb-4">Quick Start Presets</h2>
              <div className="grid grid-cols-3 gap-3">
                {Object.entries(presets).map(([key, preset]) => (
                  <button
                    key={key}
                    onClick={() => applyPreset(key)}
                    className="p-4 border border-gray-300 hover:border-black hover:bg-gray-50 text-left transition-colors"
                  >
                    <div className="font-semibold mb-1">{preset.name}</div>
                    <div className="text-xs text-gray-600">{preset.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Configuration tabs */}
            <div className="bg-white border border-gray-200">
              <div className="border-b border-gray-200">
                <div className="flex">
                  <button
                    onClick={() => setActiveTab('basic')}
                    className={`px-6 py-3 font-medium ${
                      activeTab === 'basic'
                        ? 'border-b-2 border-black text-black'
                        : 'text-gray-600 hover:text-black'
                    }`}
                  >
                    Basic Settings
                  </button>
                  <button
                    onClick={() => setActiveTab('advanced')}
                    className={`px-6 py-3 font-medium ${
                      activeTab === 'advanced'
                        ? 'border-b-2 border-black text-black'
                        : 'text-gray-600 hover:text-black'
                    }`}
                  >
                    Advanced Settings
                  </button>
                </div>
              </div>

              <div className="p-6">
                {activeTab === 'basic' ? (
                  <div className="space-y-4">
                    {/* Design name */}
                    <div>
                      <label className="block text-sm font-medium mb-2">Design Name</label>
                      <input
                        type="text"
                        className="input"
                        value={config.design_name}
                        onChange={(e) => updateConfig({ design_name: e.target.value })}
                      />
                    </div>

                    {/* PDK Selection */}
                    <div>
                      <label className="block text-sm font-medium mb-2">Process Design Kit (PDK)</label>
                      <select
                        className="input"
                        value={config.pdk}
                        onChange={(e) => updateConfig({ pdk: e.target.value })}
                      >
                        {PDK_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Clock configuration */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">Clock Period (ns)</label>
                        <input
                          type="number"
                          className="input"
                          value={config.clock_period}
                          onChange={(e) => updateConfig({ clock_period: e.target.value })}
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          Frequency: {(1000 / parseFloat(config.clock_period)).toFixed(0)} MHz
                        </p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-2">Clock Port Name</label>
                        <input
                          type="text"
                          className="input"
                          value={config.clock_port}
                          onChange={(e) => updateConfig({ clock_port: e.target.value })}
                        />
                      </div>
                    </div>

                    {/* Placement density */}
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Placement Density: {(parseFloat(config.pl_target_density) * 100).toFixed(0)}%
                      </label>
                      <input
                        type="range"
                        min="0.3"
                        max="0.9"
                        step="0.1"
                        className="w-full"
                        value={config.pl_target_density}
                        onChange={(e) => updateConfig({ pl_target_density: e.target.value })}
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>Lower (faster)</span>
                        <span>Higher (denser)</span>
                      </div>
                    </div>

                    {/* Core utilization */}
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Core Utilization: {config.fp_core_util}%
                      </label>
                      <input
                        type="range"
                        min="30"
                        max="80"
                        step="5"
                        className="w-full"
                        value={config.fp_core_util}
                        onChange={(e) => updateConfig({ fp_core_util: parseInt(e.target.value) })}
                      />
                    </div>

                    {/* Verification options */}
                    <div className="space-y-2">
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={config.run_drc}
                          onChange={(e) => updateConfig({ run_drc: e.target.checked })}
                        />
                        <span className="text-sm">Run Design Rule Check (DRC)</span>
                      </label>
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={config.run_lvs}
                          onChange={(e) => updateConfig({ run_lvs: e.target.checked })}
                        />
                        <span className="text-sm">Run Layout vs Schematic (LVS)</span>
                      </label>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Advanced settings */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">Synthesis Strategy</label>
                        <input
                          type="text"
                          className="input"
                          value={config.synth_strategy}
                          onChange={(e) => updateConfig({ synth_strategy: e.target.value })}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-2">Max Fanout</label>
                        <input
                          type="number"
                          className="input"
                          value={config.synth_max_fanout}
                          onChange={(e) => updateConfig({ synth_max_fanout: parseInt(e.target.value) })}
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">Aspect Ratio</label>
                      <input
                        type="number"
                        step="0.1"
                        className="input"
                        value={config.fp_aspect_ratio}
                        onChange={(e) => updateConfig({ fp_aspect_ratio: parseFloat(e.target.value) })}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">Docker Image</label>
                      <input
                        type="text"
                        className="input"
                        value={config.docker_image}
                        onChange={(e) => updateConfig({ docker_image: e.target.value })}
                      />
                    </div>

                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={config.use_docker}
                        onChange={(e) => updateConfig({ use_docker: e.target.checked })}
                      />
                      <span className="text-sm">Use Docker (recommended)</span>
                    </label>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar - Build status */}
          <div className="space-y-6">
            {/* Current status */}
            {buildStatus && (
              <div className="bg-white border border-gray-200 p-6">
                <h2 className="text-lg font-semibold mb-4">Latest Build Status</h2>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Status</span>
                    <StatusBadge status={buildStatus.status} />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Job ID</span>
                    <span className="text-sm font-mono">#{buildStatus.job_id}</span>
                  </div>
                  {isConnected && buildStatus.status === 'running' && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Connection</span>
                      <span className="flex items-center gap-1 text-xs text-green-600">
                        <span className="w-2 h-2 bg-green-600 rounded-full animate-pulse"></span>
                        Live
                      </span>
                    </div>
                  )}
                  {currentStep && buildStatus.status === 'running' && (
                    <div className="mt-4 p-3 bg-blue-50 border border-blue-200">
                      <div className="text-xs text-blue-600 mb-1">Current Step</div>
                      <div className="text-sm font-medium text-blue-900">{currentStep}</div>
                    </div>
                  )}
                  {!showLogs && buildLogs.length > 0 && (
                    <button
                      onClick={() => setShowLogs(true)}
                      className="btn-secondary w-full text-center mt-4"
                    >
                      Show Build Logs
                    </button>
                  )}
                  <Link
                    href={`/projects/${projectId}/jobs/${buildStatus.job_id}`}
                    className="btn-secondary w-full text-center mt-4"
                  >
                    View Job Details
                  </Link>
                </div>
              </div>
            )}

            {/* Help */}
            <div className="bg-blue-50 border border-blue-200 p-6">
              <h3 className="font-semibold text-blue-900 mb-2">LibreLane ASIC Flow</h3>
              <p className="text-sm text-blue-800 mb-3">
                LibreLane automates the complete ASIC design flow from RTL to GDSII using open-source
                tools.
              </p>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Synthesis (Yosys)</li>
                <li>• Place & Route (OpenROAD)</li>
                <li>• DRC/LVS (Magic/Netgen)</li>
                <li>• GDSII Generation</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const statusConfig = {
    pending: { icon: Clock, color: 'text-gray-600', bg: 'bg-gray-100', label: 'Pending' },
    running: { icon: Loader, color: 'text-blue-600', bg: 'bg-blue-100', label: 'Running' },
    completed: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100', label: 'Completed' },
    failed: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-100', label: 'Failed' },
    cancelled: { icon: XCircle, color: 'text-gray-600', bg: 'bg-gray-100', label: 'Cancelled' },
  };

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 ${config.bg} ${config.color} text-xs font-medium`}>
      <Icon className="w-3 h-3" />
      {config.label}
    </span>
  );
}
