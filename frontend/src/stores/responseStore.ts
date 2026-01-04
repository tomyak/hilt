import { create } from 'zustand';
import type { ResponseDraft, ResponseMode, ToolCall } from './requestStore';

interface ResponseState {
  drafts: Map<string, ResponseDraft>;
  modes: Map<string, ResponseMode>;

  setDraft: (requestId: string, content: string) => void;
  setMode: (requestId: string, mode: ResponseMode) => void;
  addToolCall: (requestId: string, toolCall: ToolCall) => void;
  removeToolCall: (requestId: string, toolCallId: string) => void;
  updateToolCall: (requestId: string, toolCallId: string, toolCall: ToolCall) => void;
  getDraft: (requestId: string) => ResponseDraft | undefined;
  getMode: (requestId: string) => ResponseMode;
  clearDraft: (requestId: string) => void;
}

export const useResponseStore = create<ResponseState>((set, get) => ({
  drafts: new Map(),
  modes: new Map(),

  setDraft: (requestId, content) =>
    set((state) => {
      const currentDraft = state.drafts.get(requestId) || { content: '', toolCalls: [] };
      const newDrafts = new Map(state.drafts);
      newDrafts.set(requestId, { ...currentDraft, content });
      return { drafts: newDrafts };
    }),

  setMode: (requestId, mode) =>
    set((state) => {
      const newModes = new Map(state.modes);
      newModes.set(requestId, mode);
      return { modes: newModes };
    }),

  addToolCall: (requestId, toolCall) =>
    set((state) => {
      const currentDraft = state.drafts.get(requestId) || { content: '', toolCalls: [] };
      const newDrafts = new Map(state.drafts);
      newDrafts.set(requestId, {
        ...currentDraft,
        toolCalls: [...currentDraft.toolCalls, toolCall],
      });
      return { drafts: newDrafts };
    }),

  removeToolCall: (requestId, toolCallId) =>
    set((state) => {
      const currentDraft = state.drafts.get(requestId);
      if (!currentDraft) return {};

      const newDrafts = new Map(state.drafts);
      newDrafts.set(requestId, {
        ...currentDraft,
        toolCalls: currentDraft.toolCalls.filter((tc) => tc.id !== toolCallId),
      });
      return { drafts: newDrafts };
    }),

  updateToolCall: (requestId, toolCallId, toolCall) =>
    set((state) => {
      const currentDraft = state.drafts.get(requestId);
      if (!currentDraft) return {};

      const newDrafts = new Map(state.drafts);
      newDrafts.set(requestId, {
        ...currentDraft,
        toolCalls: currentDraft.toolCalls.map((tc) => (tc.id === toolCallId ? toolCall : tc)),
      });
      return { drafts: newDrafts };
    }),

  getDraft: (requestId) => {
    return get().drafts.get(requestId);
  },

  getMode: (requestId) => {
    return get().modes.get(requestId) || 'batch';
  },

  clearDraft: (requestId) =>
    set((state) => {
      const newDrafts = new Map(state.drafts);
      const newModes = new Map(state.modes);
      newDrafts.delete(requestId);
      newModes.delete(requestId);
      return { drafts: newDrafts, modes: newModes };
    }),
}));
