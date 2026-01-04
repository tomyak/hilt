import { create } from 'zustand';

export interface Message {
  role: string;
  content: string;
}

export interface ToolFunction {
  name: string;
  description: string;
  parameters: Record<string, any>;
}

export interface Tool {
  type: "function";
  function: ToolFunction;
}

export interface ToolCall {
  id: string;
  type: "function";
  function: {
    name: string;
    arguments: string;
  };
}

export interface LLMRequest {
  request_id: string;
  provider: "openai" | "anthropic" | "gemini";
  model: string;
  messages: Message[];
  system?: string;
  tools?: Tool[];
  parameters: Record<string, any>;
  timestamp: string;
  timeout_at: string;
}

export interface LLMResponse {
  request_id: string;
  content: string;
  tool_calls?: ToolCall[];
  finish_reason: "stop" | "tool_calls" | "length";
}

export interface ResponseDraft {
  content: string;
  toolCalls: ToolCall[];
}

export type ResponseMode = "streaming" | "batch";

export interface WebSocketMessage {
  type: string;
  data: any;
}

export interface NewRequestMessage extends WebSocketMessage {
  type: "new_request";
  data: LLMRequest;
}

export interface RequestCancelledMessage extends WebSocketMessage {
  type: "request_cancelled";
  data: {
    request_id: string;
    reason: string;
  };
}

export interface StatsUpdateMessage extends WebSocketMessage {
  type: "stats_update";
  data: {
    pending_requests: number;
    active_requests: number;
    streaming_requests: number;
    active_connections: number;
  };
}

export interface ErrorMessage extends WebSocketMessage {
  type: "error";
  data: {
    error_code: string;
    message: string;
    request_id?: string;
  };
}

interface RequestState {
  requests: Map<string, LLMRequest>;
  selectedRequestId: string | null;

  addRequest: (request: LLMRequest) => void;
  removeRequest: (requestId: string) => void;
  selectRequest: (requestId: string | null) => void;
  getRequest: (requestId: string) => LLMRequest | undefined;
  getPendingRequests: () => LLMRequest[];
  clearCompleted: () => void;
}

export const useRequestStore = create<RequestState>((set, get) => ({
  requests: new Map(),
  selectedRequestId: null,

  addRequest: (request) =>
    set((state) => {
      const newRequests = new Map(state.requests);
      newRequests.set(request.request_id, request);
      return { requests: newRequests };
    }),

  removeRequest: (requestId) =>
    set((state) => {
      const newRequests = new Map(state.requests);
      newRequests.delete(requestId);
      return {
        requests: newRequests,
        selectedRequestId: state.selectedRequestId === requestId ? null : state.selectedRequestId,
      };
    }),

  selectRequest: (requestId) =>
    set({ selectedRequestId: requestId }),

  getRequest: (requestId) => {
    return get().requests.get(requestId);
  },

  getPendingRequests: () => {
    return Array.from(get().requests.values()).sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  },

  clearCompleted: () =>
    set((state) => {
      // For now, we don't track completion status, so this just clears all
      return { requests: new Map(), selectedRequestId: null };
    }),
}));
