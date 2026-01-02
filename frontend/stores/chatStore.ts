import { create } from 'zustand';

export interface ToolInvocation {
  toolCallId: string;
  toolName: string;
  args: Record<string, unknown>;
  state: 'pending' | 'running' | 'completed' | 'error';
  result?: unknown;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
  isStreaming?: boolean;
  toolInvocations?: ToolInvocation[];
}

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  threadId: string | null;
  error: string | null;
  addMessage: (message: ChatMessage) => void;
  updateLastMessage: (
    updates: Partial<ChatMessage> | ((current: ChatMessage) => Partial<ChatMessage>)
  ) => void;
  clearMessages: () => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
  setThreadId: (threadId: string | null) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isLoading: false,
  threadId: null,
  error: null,
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  updateLastMessage: (updates) =>
    set((state) => {
      if (state.messages.length === 0) return state;
      const messages = [...state.messages];
      const current = messages[messages.length - 1];
      const nextUpdates = typeof updates === 'function' ? updates(current) : updates;
      messages[messages.length - 1] = { ...current, ...nextUpdates };
      return { messages };
    }),
  clearMessages: () => set({ messages: [] }),
  setError: (error) => set({ error }),
  setLoading: (loading) => set({ isLoading: loading }),
  setThreadId: (threadId) => set({ threadId })
}));
