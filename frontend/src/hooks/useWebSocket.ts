import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '../stores/authStore';
import { useRequestStore } from '../stores/requestStore';
import type { WebSocketMessage, NewRequestMessage, RequestCancelledMessage } from '../stores/requestStore';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8082/ws';
const RECONNECT_INTERVAL = 3000;
const MAX_RECONNECT_ATTEMPTS = 5;

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const reconnectAttemptsRef = useRef(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const { token, isAuthenticated } = useAuthStore();
  const { addRequest, removeRequest } = useRequestStore();

  const connect = useCallback(() => {
    if (!token || !isAuthenticated) {
      console.log('Not connecting - no token or not authenticated');
      return;
    }

    // Don't create a new connection if one is already open or connecting
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      console.log('WebSocket already connected or connecting, skipping...');
      return;
    }

    console.log('Connecting to WebSocket...');
    const ws = new WebSocket(`${WS_URL}?token=${token}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      reconnectAttemptsRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        console.log('WebSocket message:', message);

        switch (message.type) {
          case 'new_request': {
            const newRequestMsg = message as NewRequestMessage;
            addRequest(newRequestMsg.data);
            console.log('New request added:', newRequestMsg.data.request_id);
            break;
          }

          case 'request_cancelled': {
            const cancelledMsg = message as RequestCancelledMessage;
            removeRequest(cancelledMsg.data.request_id);
            console.log('Request cancelled:', cancelledMsg.data.request_id);
            break;
          }

          case 'stats_update': {
            console.log('Stats update:', message.data);
            break;
          }

          case 'error': {
            console.error('WebSocket error message:', message.data);
            break;
          }

          default:
            console.log('Unknown message type:', message.type);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);

      // Auto-reconnect with exponential backoff
      if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = RECONNECT_INTERVAL * Math.pow(1.5, reconnectAttemptsRef.current);
        console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1}/${MAX_RECONNECT_ATTEMPTS})...`);

        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptsRef.current += 1;
          connect();
        }, delay);
      } else {
        console.error('Max reconnect attempts reached');
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;
  }, [token, isAuthenticated, addRequest, removeRequest]);

  const send = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      console.log('Sent WebSocket message:', message);
    } else {
      console.error('WebSocket is not connected');
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated && token) {
      connect();
    } else {
      // Clean up if no longer authenticated
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
        wsRef.current.close();
        wsRef.current = null;
      }
    }

    return () => {
      // Only clean up on unmount, not on every re-render
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, token]);

  return { isConnected, send };
}
