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
