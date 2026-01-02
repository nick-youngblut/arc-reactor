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
    <section className="flex h-full flex-col gap-5 p-6">
      <header className="flex items-center justify-between border-b border-arc-gray-100 pb-4 dark:border-arc-gray-800">
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <div className="h-2 w-2 rounded-full bg-arc-blue animate-pulse"></div>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-arc-gray-400">
              Arc Assistant
            </p>
          </div>
          <h2 className="text-xl font-extrabold tracking-tight text-arc-night dark:text-white">AI Agent Chat</h2>
        </div>
        <button
          type="button"
          className="rounded-xl border border-arc-gray-200/50 bg-white/50 px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider text-arc-gray-500 transition-all hover:bg-arc-gray-50 hover:text-arc-clay dark:border-arc-gray-800/50 dark:bg-night/50 dark:text-arc-gray-400 dark:hover:bg-night"
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
