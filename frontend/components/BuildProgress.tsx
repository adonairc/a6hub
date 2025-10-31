import React from 'react';
import { CheckCircle, Circle, Loader, AlertCircle } from 'lucide-react';

interface BuildStep {
  name: string;
  label: string;
  description: string;
}

interface ProgressData {
  current_step: string;
  progress_percent?: number;
  completed_steps?: string[];
  steps_info?: BuildStep[];
}

interface BuildProgressProps {
  status: string;
  currentStep?: string | null;
  progressData?: ProgressData | null;
}

export default function BuildProgress({ status, currentStep, progressData }: BuildProgressProps) {
  // Default LibreLane steps if not provided by backend
  const defaultSteps: BuildStep[] = [
    { name: 'initialization', label: 'Initialization', description: 'Setting up build environment' },
    { name: 'synthesis', label: 'Synthesis', description: 'Converting RTL to gate-level netlist' },
    { name: 'floorplan', label: 'Floorplan', description: 'Planning chip layout' },
    { name: 'placement', label: 'Placement', description: 'Placing standard cells' },
    { name: 'cts', label: 'Clock Tree Synthesis', description: 'Building clock distribution network' },
    { name: 'routing', label: 'Routing', description: 'Routing signal connections' },
    { name: 'gdsii', label: 'GDSII Generation', description: 'Generating final layout' },
    { name: 'drc', label: 'DRC', description: 'Design Rule Check' },
    { name: 'lvs', label: 'LVS', description: 'Layout vs Schematic verification' },
    { name: 'completion', label: 'Completion', description: 'Finalizing build artifacts' },
  ];

  const steps = progressData?.steps_info || defaultSteps;
  const completedSteps = progressData?.completed_steps || [];
  const current = currentStep || progressData?.current_step || '';
  const progressPercent = progressData?.progress_percent || 0;

  const getStepStatus = (stepName: string) => {
    if (status === 'failed' && stepName === current) {
      return 'failed';
    }
    if (completedSteps.includes(stepName)) {
      return 'completed';
    }
    if (stepName === current && status === 'running') {
      return 'running';
    }
    return 'pending';
  };

  const getStepIcon = (stepStatus: string) => {
    switch (stepStatus) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'running':
        return <Loader className="w-5 h-5 text-blue-600 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Circle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStepColor = (stepStatus: string) => {
    switch (stepStatus) {
      case 'completed':
        return 'border-green-500 bg-green-50';
      case 'running':
        return 'border-blue-500 bg-blue-50';
      case 'failed':
        return 'border-red-500 bg-red-50';
      default:
        return 'border-gray-300 bg-white';
    }
  };

  return (
    <div className="bg-white border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">Build Progress</h2>
        {status === 'running' && (
          <div className="flex items-center gap-2 text-sm text-blue-600">
            <Loader className="w-4 h-4 animate-spin" />
            <span>{progressPercent}% Complete</span>
          </div>
        )}
        {status === 'completed' && (
          <div className="flex items-center gap-2 text-sm text-green-600">
            <CheckCircle className="w-4 h-4" />
            <span>Build Complete</span>
          </div>
        )}
        {status === 'failed' && (
          <div className="flex items-center gap-2 text-sm text-red-600">
            <AlertCircle className="w-4 h-4" />
            <span>Build Failed</span>
          </div>
        )}
      </div>

      {/* Progress bar */}
      {status === 'running' && (
        <div className="mb-6">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      )}

      {/* Steps list */}
      <div className="space-y-3">
        {steps.map((step, index) => {
          const stepStatus = getStepStatus(step.name);
          const isActive = stepStatus === 'running';

          return (
            <div
              key={step.name}
              className={`flex items-start gap-3 p-3 border rounded transition-all ${getStepColor(stepStatus)} ${
                isActive ? 'ring-2 ring-blue-500 ring-opacity-50' : ''
              }`}
            >
              <div className="flex-shrink-0 mt-0.5">{getStepIcon(stepStatus)}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-sm font-semibold text-gray-900">{step.label}</h3>
                  <span className="text-xs text-gray-500">
                    {index + 1}/{steps.length}
                  </span>
                </div>
                <p className="text-xs text-gray-600">{step.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
