'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import { useChatStore } from '@/stores/chatStore';
import { useWorkspaceStore } from '@/stores/workspaceStore';

const MAX_RECONNECTS = 5;
const RECONNECT_DELAY_MS = 2000;

function buildWebSocketUrl() {
  if (typeof window === 'undefined') return null;
  const envUrl = process.env.NEXT_PUBLIC_CHAT_WS_URL;
  if (envUrl) return envUrl;
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${protocol}://${window.location.host}/api/chat/ws`;
}

function safeJsonParse<T>(value: string): T | null {
  try {
    return JSON.parse(value) as T;
  } catch {
    return null;
  }
}

export function useAgentChat() {
  const [input, setInput] = useState('');
  const wsRef = useRef<WebSocket | null>(null);
  const bufferRef = useRef('');
  const reconnectAttempts = useRef(0);
  const manualClose = useRef(false);
  const toolNameMap = useRef<Record<string, string>>({});

  const messages = useChatStore((state) => state.messages);
  const isLoading = useChatStore((state) => state.isLoading);
  const error = useChatStore((state) => state.error);
  const addMessage = useChatStore((state) => state.addMessage);
  const updateLastMessage = useChatStore((state) => state.updateLastMessage);
  const setLoading = useChatStore((state) => state.setLoading);
  const setError = useChatStore((state) => state.setError);
  const threadId = useChatStore((state) => state.threadId);
  const setThreadId = useChatStore((state) => state.setThreadId);
  const clearMessages = useChatStore((state) => state.clearMessages);

  const setSamplesheet = useWorkspaceStore((state) => state.setSamplesheet);
  const setConfig = useWorkspaceStore((state) => state.setConfig);

  const updateToolInvocation = useCallback(
    (toolCallId: string, updates: Partial<{ state: string; result: unknown; args: Record<string, unknown>; toolName: string }>) => {
      updateLastMessage((prev) => {
        const existing = prev.toolInvocations ?? [];
        const next = existing.some((item) => item.toolCallId === toolCallId)
          ? existing.map((item) =>
              item.toolCallId === toolCallId
                ? {
                    ...item,
                    ...updates,
                    state: (updates.state ?? item.state) as 'pending' | 'running' | 'completed' | 'error'
                  }
                : item
            )
          : [
              ...existing,
              {
                toolCallId,
                toolName: updates.toolName ?? 'tool',
                args: updates.args ?? {},
                state: (updates.state ?? 'running') as 'pending' | 'running' | 'completed' | 'error',
                result: updates.result
              }
            ];

        return { toolInvocations: next };
      });
    },
    [updateLastMessage]
  );

  const handleStreamLine = useCallback(
    (line: string) => {
      if (!line) return;
      const trimmed = line.startsWith('data:') ? line.replace(/^data:\s*/, '') : line;
      const code = trimmed[0];
      if (!code || trimmed[1] !== ':') return;
      const payload = trimmed.slice(2);

      if (code === '0') {
        const text = safeJsonParse<string>(payload) ?? payload.replace(/^"|"$/g, '');
        updateLastMessage((prev) => ({
          content: `${prev.content ?? ''}${text}`,
          isStreaming: true
        }));
      }

      if (code === '9') {
        const data = safeJsonParse<{ toolCallId: string; toolName: string; args: Record<string, unknown> }>(payload);
        if (data) {
          toolNameMap.current[data.toolCallId] = data.toolName;
          updateToolInvocation(data.toolCallId, {
            toolName: data.toolName,
            args: data.args,
            state: 'running'
          });
        }
      }

      if (code === 'a') {
        const data = safeJsonParse<{ toolCallId: string; result: unknown }>(payload);
        if (data) {
          updateToolInvocation(data.toolCallId, {
            state: 'completed',
            result: data.result
          });
          const toolName = toolNameMap.current[data.toolCallId] ?? '';
          if (toolName.includes('samplesheet') && typeof data.result === 'string') {
            setSamplesheet(data.result);
          }
          if (toolName.includes('config') && typeof data.result === 'string') {
            setConfig(data.result);
          }
        }
      }

      if (code === 'd' || code === 'e') {
        updateLastMessage({ isStreaming: false });
        setLoading(false);
      }

      if (code === 'f') {
        const data = safeJsonParse<{ messageId: string }>(payload);
        if (data?.messageId) setThreadId(data.messageId);
      }
    },
    [setConfig, setLoading, setSamplesheet, setThreadId, updateLastMessage, updateToolInvocation]
  );

  const handleStreamChunk = useCallback(
    (chunk: string) => {
      bufferRef.current += chunk;
      let newlineIndex = bufferRef.current.indexOf('\n');
      while (newlineIndex !== -1) {
        const line = bufferRef.current.slice(0, newlineIndex).trim();
        bufferRef.current = bufferRef.current.slice(newlineIndex + 1);
        handleStreamLine(line);
        newlineIndex = bufferRef.current.indexOf('\n');
      }
    },
    [handleStreamLine]
  );

  const connect = useCallback(() => {
    const url = buildWebSocketUrl();
    if (!url) return;

    const socket = new WebSocket(url);
    wsRef.current = socket;

    socket.onopen = () => {
      reconnectAttempts.current = 0;
      setError(null);
    };

    socket.onmessage = (event) => {
      const payload = typeof event.data === 'string' ? event.data : '';
      if (!payload) return;
      const json = safeJsonParse<{ type?: string; message?: string }>(payload);
      if (json?.type === 'error') {
        setError(json.message || 'Unknown error');
        setLoading(false);
        return;
      }
      if (json?.type === 'connected') return;
      handleStreamChunk(payload);
    };

    socket.onerror = () => {
      setError('Chat connection error');
    };

    socket.onclose = () => {
      if (manualClose.current) return;
      if (reconnectAttempts.current >= MAX_RECONNECTS) {
        setError('Unable to reconnect to chat stream');
        return;
      }
      reconnectAttempts.current += 1;
      setTimeout(() => connect(), RECONNECT_DELAY_MS);
    };
  }, [handleStreamChunk, setError, setLoading]);

  useEffect(() => {
    connect();
    return () => {
      manualClose.current = true;
      wsRef.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback(
    (message: string) => {
      if (!message.trim()) return;
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        setError('Chat connection is not available.');
        return;
      }

      const userMessage = {
        id: crypto.randomUUID(),
        role: 'user' as const,
        content: message,
        createdAt: new Date().toISOString()
      };
      const assistantMessage = {
        id: crypto.randomUUID(),
        role: 'assistant' as const,
        content: '',
        createdAt: new Date().toISOString(),
        isStreaming: true
      };

      addMessage(userMessage);
      addMessage(assistantMessage);
      setLoading(true);

      wsRef.current.send(
        JSON.stringify({
          type: 'message',
          content: message,
          thread_id: threadId
        })
      );
    },
    [addMessage, setError, setLoading, threadId]
  );

  const stop = useCallback(() => {
    manualClose.current = true;
    wsRef.current?.close();
    setLoading(false);
  }, [setLoading]);

  return {
    messages,
    input,
    setInput,
    sendMessage,
    isLoading,
    error,
    clearMessages,
    stop
  };
}
