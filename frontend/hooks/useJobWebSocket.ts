/**
 * React hook for WebSocket connection to job updates
 * Provides real-time build progress, logs, and status updates
 */
import { useEffect, useRef, useState, useCallback } from 'react';

export interface JobUpdate {
  type: 'connected' | 'status' | 'progress' | 'log' | 'step' | 'complete' | 'error' | 'pong';
  data: {
    job_id?: number;
    status?: string;
    progress?: number;
    current_step?: string;
    completed_steps?: string[];
    log_line?: string;
    step_name?: string;
    step_label?: string;
    message?: string;
    error_message?: string;
  };
  timestamp?: string;
}

interface UseJobWebSocketOptions {
  jobId: number;
  onStatusChange?: (status: string) => void;
  onProgressUpdate?: (progress: number, step: string, completedSteps: string[]) => void;
  onLogUpdate?: (logLine: string) => void;
  onStepChange?: (stepName: string, stepLabel: string) => void;
  onComplete?: (status: string, message?: string) => void;
  onError?: (errorMessage: string) => void;
  enabled?: boolean;
}

export function useJobWebSocket(options: UseJobWebSocketOptions) {
  const {
    jobId,
    onStatusChange,
    onProgressUpdate,
    onLogUpdate,
    onStepChange,
    onComplete,
    onError,
    enabled = true,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000; // 3 seconds

  const connect = useCallback(() => {
    if (!enabled || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      // Get token from localStorage
      const token = localStorage.getItem('token');
      if (!token) {
        setConnectionError('No authentication token found');
        return;
      }

      // Determine WebSocket URL
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = process.env.NEXT_PUBLIC_API_URL?.replace(/^https?:\/\//, '') || 'localhost:8000';
      const wsUrl = `${wsProtocol}//${wsHost}/api/v1/ws/jobs/${jobId}/updates?token=${token}`;

      console.log(`[WebSocket] Connecting to ${wsUrl}`);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log(`[WebSocket] Connected to job ${jobId}`);
        setIsConnected(true);
        setConnectionError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const update: JobUpdate = JSON.parse(event.data);
          console.log(`[WebSocket] Received ${update.type}:`, update.data);

          switch (update.type) {
            case 'connected':
              // Initial connection message
              break;

            case 'status':
              if (update.data.status && onStatusChange) {
                onStatusChange(update.data.status);
              }
              break;

            case 'progress':
              if (onProgressUpdate && update.data.progress !== undefined) {
                onProgressUpdate(
                  update.data.progress,
                  update.data.current_step || '',
                  update.data.completed_steps || []
                );
              }
              break;

            case 'log':
              if (update.data.log_line && onLogUpdate) {
                onLogUpdate(update.data.log_line);
              }
              break;

            case 'step':
              if (update.data.step_name && onStepChange) {
                onStepChange(
                  update.data.step_name,
                  update.data.step_label || update.data.step_name
                );
              }
              break;

            case 'complete':
              if (update.data.status && onComplete) {
                onComplete(update.data.status, update.data.message);
              }
              break;

            case 'error':
              if (update.data.error_message && onError) {
                onError(update.data.error_message);
              }
              break;

            case 'pong':
              // Keep-alive response
              break;
          }
        } catch (error) {
          console.error('[WebSocket] Error parsing message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
        setConnectionError('WebSocket connection error');
      };

      ws.onclose = (event) => {
        console.log(`[WebSocket] Closed: code=${event.code}, reason=${event.reason}`);
        setIsConnected(false);
        wsRef.current = null;

        // Attempt reconnection if not a normal closure
        if (event.code !== 1000 && enabled && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          console.log(`[WebSocket] Reconnecting (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay * reconnectAttemptsRef.current);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setConnectionError('Failed to reconnect after multiple attempts');
        }
      };

    } catch (error) {
      console.error('[WebSocket] Connection error:', error);
      setConnectionError(error instanceof Error ? error.message : 'Unknown error');
    }
  }, [jobId, enabled, onStatusChange, onProgressUpdate, onLogUpdate, onStepChange, onComplete, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send('ping');
    }
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  // Keep-alive ping every 30 seconds
  useEffect(() => {
    if (!isConnected) return;

    const pingInterval = setInterval(() => {
      sendPing();
    }, 30000);

    return () => clearInterval(pingInterval);
  }, [isConnected, sendPing]);

  return {
    isConnected,
    connectionError,
    reconnect: connect,
    disconnect,
  };
}
