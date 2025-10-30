'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { jobsAPI, filesAPI } from '@/lib/api';
import { Play, CheckCircle, XCircle, Clock, Loader, FileText, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';

interface Job {
  id: number;
  job_type: string;
  status: string;
  created_at: string;
  completed_at: string | null;
}

interface SimulationConfig {
  simulator: 'verilator' | 'icarus';
  testbench: string;
  timescale: string;
  dump_waves: boolean;
}

export default function SimulationPage() {
  const params = useParams();
  const projectId = parseInt(params.id as string);

  const [jobs, setJobs] = useState<Job[]>([]);
  const [files, setFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [logs, setLogs] = useState<string>('');

  const [config, setConfig] = useState<SimulationConfig>({
    simulator: 'verilator',
    testbench: 'testbench.v',
    timescale: '1ns/1ps',
    dump_waves: true,
  });

  useEffect(() => {
    loadJobs();
    loadFiles();
  }, [projectId]);

  const loadJobs = async () => {
    try {
      const response = await jobsAPI.list(projectId);
      const simJobs = response.data.filter((job: Job) => job.job_type === 'simulation');
      setJobs(simJobs);
    } catch (error) {
      console.error('Failed to load jobs:', error);
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

  const runSimulation = async () => {
    setRunning(true);
    try {
      await jobsAPI.create(projectId, {
        job_type: 'simulation',
        config: config,
      });
      toast.success('Simulation started');
      await loadJobs();
    } catch (error) {
      toast.error('Failed to start simulation');
    } finally {
      setRunning(false);
    }
  };

  const viewJobLogs = async (job: Job) => {
    setSelectedJob(job);
    try {
      const response = await jobsAPI.getLogs(projectId, job.id);
      setLogs(response.data.logs || 'No logs available');
    } catch (error) {
      toast.error('Failed to load logs');
      setLogs('Failed to load logs');
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="h-full bg-gray-50 overflow-auto">
      {/* Toolbar */}
      <div className="border-b border-gray-200 bg-white px-6 py-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Simulation</h2>
          <button
            onClick={runSimulation}
            disabled={running}
            className="btn-primary flex items-center gap-2"
          >
            {running ? (
              <>
                <Loader className="w-4 h-4 animate-spin" />
                Starting...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Run Simulation
              </>
            )}
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Configuration */}
          <div className="lg:col-span-2 space-y-6">
            {/* Simulator Configuration */}
            <div className="bg-white border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4">Simulator Configuration</h3>

              <div className="space-y-4">
                {/* Simulator Selection */}
                <div>
                  <label className="block text-sm font-medium mb-2">Simulator</label>
                  <select
                    className="input"
                    value={config.simulator}
                    onChange={(e) => setConfig({ ...config, simulator: e.target.value as 'verilator' | 'icarus' })}
                  >
                    <option value="verilator">Verilator (Fast, for synthesis)</option>
                    <option value="icarus">Icarus Verilog (Full featured)</option>
                  </select>
                </div>

                {/* Testbench File */}
                <div>
                  <label className="block text-sm font-medium mb-2">Testbench File</label>
                  <select
                    className="input"
                    value={config.testbench}
                    onChange={(e) => setConfig({ ...config, testbench: e.target.value })}
                  >
                    <option value="">Select testbench...</option>
                    {files
                      .filter((f) => f.filename.endsWith('.v') || f.filename.endsWith('.sv'))
                      .map((file) => (
                        <option key={file.id} value={file.filename}>
                          {file.filename}
                        </option>
                      ))}
                  </select>
                </div>

                {/* Timescale */}
                <div>
                  <label className="block text-sm font-medium mb-2">Timescale</label>
                  <input
                    type="text"
                    className="input"
                    value={config.timescale}
                    onChange={(e) => setConfig({ ...config, timescale: e.target.value })}
                    placeholder="1ns/1ps"
                  />
                </div>

                {/* Dump Waves */}
                <div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={config.dump_waves}
                      onChange={(e) => setConfig({ ...config, dump_waves: e.target.checked })}
                    />
                    <span className="text-sm">Dump waveforms (VCD)</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Simulation History */}
            <div className="bg-white border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4">Simulation History</h3>

              {jobs.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <AlertCircle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>No simulations run yet</p>
                  <p className="text-sm mt-1">Configure and run your first simulation above</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {jobs.map((job) => (
                    <div
                      key={job.id}
                      className="border border-gray-200 p-4 rounded hover:bg-gray-50 cursor-pointer"
                      onClick={() => viewJobLogs(job)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <StatusBadge status={job.status} />
                          <div>
                            <div className="font-medium">Simulation #{job.id}</div>
                            <div className="text-xs text-gray-500">
                              {new Date(job.created_at).toLocaleString()}
                            </div>
                          </div>
                        </div>
                        <button
                          className="text-sm text-blue-600 hover:underline"
                          onClick={(e) => {
                            e.stopPropagation();
                            viewJobLogs(job);
                          }}
                        >
                          View Logs
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Info */}
            <div className="bg-blue-50 border border-blue-200 p-6">
              <h3 className="font-semibold text-blue-900 mb-2">Simulation Tools</h3>
              <div className="text-sm text-blue-800 space-y-2">
                <p>
                  <strong>Verilator:</strong> Fast cycle-accurate simulator, best for RTL verification
                </p>
                <p>
                  <strong>Icarus Verilog:</strong> Full-featured event-driven simulator with better Verilog support
                </p>
              </div>
            </div>

            {/* Recent Results */}
            {selectedJob && (
              <div className="bg-white border border-gray-200 p-6">
                <h3 className="font-semibold mb-3">Job #{selectedJob.id}</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Status:</span>
                    <StatusBadge status={selectedJob.status} />
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Started:</span>
                    <span>{new Date(selectedJob.created_at).toLocaleString()}</span>
                  </div>
                  {selectedJob.completed_at && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Completed:</span>
                      <span>{new Date(selectedJob.completed_at).toLocaleString()}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Logs Modal */}
        {selectedJob && logs && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white w-full max-w-4xl max-h-[80vh] flex flex-col border border-gray-300">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-lg font-semibold">Simulation Logs - Job #{selectedJob.id}</h3>
                <button
                  onClick={() => {
                    setSelectedJob(null);
                    setLogs('');
                  }}
                  className="text-gray-600 hover:text-black"
                >
                  ✕
                </button>
              </div>
              <div className="flex-1 overflow-auto p-6">
                <pre className="text-xs font-mono bg-gray-900 text-green-400 p-4 rounded overflow-auto">
                  {logs}
                </pre>
              </div>
              <div className="px-6 py-4 border-t border-gray-200">
                <button
                  onClick={() => {
                    setSelectedJob(null);
                    setLogs('');
                  }}
                  className="btn-secondary"
                >
                  Close
                </button>
              </div>
            </div>
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
