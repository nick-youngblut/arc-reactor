import { create } from 'zustand';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
  toolCalls?: Array<{ name: string; status: 'pending' | 'running' | 'completed' | 'error'; payload?: unknown }>;
}

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  threadId: string | null;
  error: string | null;
  addMessage: (message: ChatMessage) => void;
  updateLastMessage: (updates: Partial<ChatMessage>) => void;
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
      messages[messages.length - 1] = { ...messages[messages.length - 1], ...updates };
      return { messages };
    }),
  clearMessages: () => set({ messages: [] }),
  setError: (error) => set({ error }),
  setLoading: (loading) => set({ isLoading: loading }),
  setThreadId: (threadId) => set({ threadId })
}));
