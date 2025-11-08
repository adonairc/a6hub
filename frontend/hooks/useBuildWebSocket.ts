import { useEffect, useRef, useState } from 'react';
import { BuildWebSocket, BuildProgressMessage } from '@/lib/websocket';

interface UseBuildWebSocketOptions {
  jobId: number | null;
  enabled?: boolean;
  onMessage?: (message: BuildProgressMessage) => void;
}

export function useBuildWebSocket({ jobId, enabled = true, onMessage }: UseBuildWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<BuildProgressMessage | null>(null);
  const wsRef = useRef<BuildWebSocket | null>(null);

  useEffect(() => {
    if (!jobId || !enabled) {
      return;
    }

    // Get token from localStorage
    const token = localStorage.getItem('token');
    if (!token) {
      console.warn('No authentication token found');
      return;
    }

    // Create WebSocket connection
    const ws = new BuildWebSocket(jobId, token);
    wsRef.current = ws;

    // Subscribe to messages
    const unsubscribe = ws.onMessage((message) => {
      setLastMessage(message);
      if (onMessage) {
        onMessage(message);
      }

      // Update connection status
      if (message.type === 'connected') {
        setIsConnected(true);
      }
    });

    // Connect
    ws.connect();

    // Cleanup on unmount
    return () => {
      unsubscribe();
      ws.disconnect();
      wsRef.current = null;
      setIsConnected(false);
    };
  }, [jobId, enabled, onMessage]);

  return {
    isConnected,
    lastMessage,
    sendMessage: (data: any) => wsRef.current?.send(data),
  };
}
