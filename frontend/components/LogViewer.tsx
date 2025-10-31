import React, { useEffect, useRef } from 'react';
import { Terminal, Download, X } from 'lucide-react';

interface LogViewerProps {
  logs: string;
  title?: string;
  autoScroll?: boolean;
  maxHeight?: string;
}

export default function LogViewer({ logs, title = 'Build Logs', autoScroll = true, maxHeight = '500px' }: LogViewerProps) {
  const logEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const downloadLogs = () => {
    const element = document.createElement('a');
    const file = new Blob([logs], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `build-logs-${Date.now()}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const clearLogs = () => {
    // This would need to be implemented if you want to clear logs
    // For now, we just scroll to top
    if (containerRef.current) {
      containerRef.current.scrollTop = 0;
    }
  };

  // Format logs with ANSI color support (basic implementation)
  const formatLogs = (rawLogs: string) => {
    if (!rawLogs) return '';

    // Split into lines and wrap in spans for better formatting
    return rawLogs
      .split('\n')
      .map((line, index) => {
        // Highlight different log levels
        let className = '';
        if (line.includes('ERROR') || line.includes('FAILED') || line.includes('✗')) {
          className = 'text-red-600 font-semibold';
        } else if (line.includes('WARNING') || line.includes('⚠')) {
          className = 'text-yellow-600';
        } else if (line.includes('SUCCESS') || line.includes('✓') || line.includes('COMPLETE')) {
          className = 'text-green-600 font-semibold';
        } else if (line.includes('>>>') || line.includes('===')) {
          className = 'text-blue-600 font-bold';
        }

        return (
          <div key={index} className={`font-mono text-xs leading-relaxed ${className}`}>
            {line || '\u00A0'}
          </div>
        );
      });
  };

  return (
    <div className="bg-white border border-gray-200 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-gray-600" />
          <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={downloadLogs}
            className="p-1.5 hover:bg-gray-200 rounded transition-colors"
            title="Download logs"
          >
            <Download className="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Log content */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto bg-gray-900 p-4"
        style={{ maxHeight }}
      >
        {logs ? (
          <div className="text-gray-100">
            {formatLogs(logs)}
            <div ref={logEndRef} />
          </div>
        ) : (
          <div className="text-gray-500 text-sm text-center py-8">
            No logs available yet. Logs will appear here when the build starts.
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-gray-200 bg-gray-50 text-xs text-gray-600">
        {logs ? `${logs.split('\n').length} lines` : 'Waiting for logs...'}
      </div>
    </div>
  );
}
