'use client';

import { useAgentChat } from '@/hooks/useAgentChat';

import { ChatInput } from './ChatInput';
import { MessageList } from './MessageList';

export function ChatPanel() {
  const { messages, input, setInput, sendMessage, isLoading, clearMessages } = useAgentChat();

  const handleSubmit = () => {
    if (!input.trim()) return;
    sendMessage(input.trim());
    setInput('');
  };

  return (
    <section className="flex h-full flex-col gap-4">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-arc-gray-400">
            Chat
          </p>
          <h2 className="text-lg font-semibold text-content">Arc Assistant</h2>
        </div>
        <button
          type="button"
          className="rounded-full border border-arc-gray-200/70 px-3 py-1.5 text-xs font-semibold text-arc-gray-600 transition hover:bg-arc-gray-100 dark:border-arc-gray-800/70 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800"
          onClick={() => {
            clearMessages();
            setInput('');
          }}
        >
          Clear
        </button>
      </header>

      <div className="flex-1">
        <MessageList messages={messages} onSelectPrompt={setInput} />
      </div>

      {isLoading ? (
        <div className="flex items-center gap-2 text-xs text-arc-gray-500 dark:text-arc-gray-300">
          <span className="h-2 w-2 animate-pulse rounded-full bg-arc-blue" />
          Arc Assistant is responding...
        </div>
      ) : null}
      <ChatInput input={input} isLoading={isLoading} onChange={setInput} onSubmit={handleSubmit} />
    </section>
  );
}
