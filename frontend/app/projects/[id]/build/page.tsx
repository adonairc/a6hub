'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { buildsAPI, modulesAPI } from '@/lib/api';
import { Play, CheckCircle, XCircle, Clock, Loader, Wifi, WifiOff } from 'lucide-react';
import toast from 'react-hot-toast';
import { useToolbar } from '../layout';
import BuildProgress from '@/components/BuildProgress';
import LogViewer from '@/components/LogViewer';
import { useJobWebSocket } from '@/hooks/useJobWebSocket';

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
  current_step?: string | null;
  progress_data?: {
    current_step: string;
    progress_percent?: number;
    completed_steps?: string[];
    steps_info?: Array<{
      name: string;
      label: string;
      description: string;
    }>;
  } | null;
  logs?: string;
}

const PDK_OPTIONS = [

  { value: 'sky130A', label: 'Sky130A' },
  { value: 'gf180mcuD', label: 'GF180MCU' },
];


export default function BuildPage() {
  const params = useParams();
  const projectId = parseInt(params.id as string);
  const { setToolbarActions } = useToolbar();

  const [config, setConfig] = useState<LibreLaneFlowConfig | null>(null);
  const [presets, setPresets] = useState<Record<string, BuildPreset>>({});
  const [buildStatus, setBuildStatus] = useState<BuildStatus | null>(null);
  const [modules, setModules] = useState([])
  const [loading, setLoading] = useState(true);
  const [building, setBuilding] = useState(false);
  const [activeTab, setActiveTab] = useState<'basic' | 'advanced'>('basic');

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

  const loadModules = async () => {
    try {
      const response = await modulesAPI.listModules(projectId);
      setModules(response.data);
    } catch (error) {
      setModules([])
    }
  }

  useEffect(() => {
    loadBuildConfig();
    loadModules();
    loadPresets();
    loadBuildStatus();
  }, [projectId]);

  // WebSocket connection for real-time build updates
  const { isConnected, connectionError } = useJobWebSocket({
    jobId: buildStatus?.job_id,
    enabled: !!buildStatus && buildStatus.status === 'running',

    onStatusChange: (status) => {
      setBuildStatus((prev) => prev ? { ...prev, status } : null);
    },

    onProgressUpdate: (progress, step, completedSteps) => {
      setBuildStatus((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          current_step: step,
          progress_data: {
            current_step: step,
            progress_percent: progress,
            completed_steps: completedSteps,
            steps_info: prev.progress_data?.steps_info || []
          }
        };
      });
    },

    onLogUpdate: (logLine) => {
      setBuildStatus((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          logs: (prev.logs || '') + logLine
        };
      });
    },

    onStepChange: (stepName, stepLabel) => {
      console.log(`Build step: ${stepLabel}`);
    },

    onComplete: (status, message) => {
      setBuildStatus((prev) => prev ? { ...prev, status } : null);
      if (status === 'completed') {
        toast.success('Build completed successfully!');
      } else if (status === 'failed') {
        toast.error('Build failed');
      }
      // Reload full status to get final results
      loadBuildStatus();
    },

    onError: (errorMessage) => {
      toast.error(errorMessage);
    }
  });

  const startBuild = useCallback(async () => {
    if (!config) return;

    setBuilding(true);
    try {
      await buildsAPI.startBuild(projectId, { config });
      toast.success('Build started! Check the status below.');
      console.log("config = ",config)
      await loadBuildStatus();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to start build');
    } finally {
      setBuilding(false);
    }
  }, [config, projectId]);

  const applyPreset = (presetKey: string) => {
    const preset = presets[presetKey];
    if (preset && config) {
      setConfig({ ...config, ...preset.config });
      toast.success(`Applied ${preset.name} preset`);
    }
  };

  // Set toolbar actions
  useEffect(() => {
    setToolbarActions(
      <button
        onClick={startBuild}
        disabled={building || !config}
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
    );
  }, [startBuild, building, config, setToolbarActions]);

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
      <div className="max-w-7xl mx-auto p-6">
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
                    {/* Top Module */}
                    <div>
                      <label className="block text-sm font-medium mb-2">Top Module</label>
                      {/* <input
                        type="text"
                        className="input"
                        value={config.design_name}
                        onChange={(e) => updateConfig({ design_name: e.target.value })}
                      /> */}
                      <select
                        className="input"
                        value={config.design_name}
                        onChange={(e) => updateConfig({ design_name: e.target.value })}
                      >
                        (modules && {modules.map((module) => (
                          <option key={module.name} value={module.name}>
                            {module.name}
                          </option>
                        ))})
                      </select>
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

          {/* Sidebar - Build Progress */}
          <div className="space-y-6">
            {buildStatus ? (
              <>
                {/* WebSocket Connection Status */}
                {buildStatus.status === 'running' && (
                  <div className={`flex items-center gap-2 px-4 py-2 text-sm ${
                    isConnected
                      ? 'bg-green-50 text-green-700 border border-green-200'
                      : 'bg-yellow-50 text-yellow-700 border border-yellow-200'
                  }`}>
                    {isConnected ? (
                      <>
                        <Wifi className="w-4 h-4" />
                        <span>Live updates connected</span>
                      </>
                    ) : connectionError ? (
                      <>
                        <WifiOff className="w-4 h-4" />
                        <span>Reconnecting...</span>
                      </>
                    ) : (
                      <>
                        <Loader className="w-4 h-4 animate-spin" />
                        <span>Connecting to live updates...</span>
                      </>
                    )}
                  </div>
                )}

                {/* Build Progress Component */}
                <BuildProgress
                  status={buildStatus.status}
                  currentStep={buildStatus.current_step}
                  progressData={buildStatus.progress_data}
                />

                {/* Job Info Card */}
                <div className="bg-white border border-gray-200 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Job ID</span>
                    <span className="text-sm font-mono">#{buildStatus.job_id}</span>
                  </div>
                  <Link
                    href={`/projects/${projectId}/jobs/${buildStatus.job_id}`}
                    className="mt-4 btn-secondary w-full text-center text-sm"
                  >
                    View Job Details
                  </Link>
                </div>
              </>
            ) : (
              <div className="bg-white border border-gray-200 p-6 text-center text-gray-500">
                <p className="mb-2">No build yet</p>
                <p className="text-sm">Click &quot;Start Build&quot; to begin</p>
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

        {/* Logs Viewer - Full width section */}
        {buildStatus && buildStatus.logs && (
          <div className="mt-6">
            <LogViewer
              logs={buildStatus.logs}
              title={`Build Logs - Job #${buildStatus.job_id}`}
              autoScroll={buildStatus.status === 'running'}
              maxHeight="600px"
            />
          </div>
        )}
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
