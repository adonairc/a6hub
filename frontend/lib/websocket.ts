/**
 * WebSocket utility for real-time build progress updates
 */

export interface BuildProgressMessage {
  job_id: number;
  type: 'connected' | 'status' | 'progress' | 'log' | 'complete' | 'error';
  status?: string;
  step?: string;
  message?: string;
  progress?: number;
  timestamp?: string;
  artifacts_path?: string;
}

export type BuildProgressCallback = (message: BuildProgressMessage) => void;

export class BuildWebSocket {
  private ws: WebSocket | null = null;
  private callbacks: Set<BuildProgressCallback> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private shouldReconnect = true;

  constructor(
    private jobId: number,
    private token: string,
    private baseUrl: string = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
  ) {}

  connect() {
    try {
      const url = `${this.baseUrl}/ws/builds/${this.jobId}?token=${encodeURIComponent(this.token)}`;
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log(`WebSocket connected for job ${this.jobId}`);
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const message: BuildProgressMessage = JSON.parse(event.data);
          this.callbacks.forEach((callback) => callback(message));
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log(`WebSocket closed for job ${this.jobId}`);
        this.ws = null;

        // Attempt to reconnect
        if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
          console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
          setTimeout(() => this.connect(), delay);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.callbacks.clear();
  }

  onMessage(callback: BuildProgressCallback) {
    this.callbacks.add(callback);
    return () => {
      this.callbacks.delete(callback);
    };
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}
