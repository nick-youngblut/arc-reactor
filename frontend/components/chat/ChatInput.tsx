'use client';

import { useEffect, useRef } from 'react';

interface ChatInputProps {
  input: string;
  isLoading: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

export function ChatInput({ input, isLoading, onChange, onSubmit }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const maxChars = 1200;

  useEffect(() => {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = '0px';
    textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
  }, [input]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if (!isLoading) onSubmit();
    }
  };

  return (
    <div className="space-y-2">
      <div className="rounded-2xl border border-arc-gray-200/70 bg-white p-3 shadow-sm dark:border-arc-gray-800/70 dark:bg-slate-900">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(event) => onChange(event.target.value.slice(0, maxChars))}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          placeholder="Ask Arc Reactor to build a samplesheet or validate inputs..."
          className="min-h-[44px] w-full resize-none border-0 bg-transparent text-sm text-arc-gray-700 outline-none placeholder:text-arc-gray-400 dark:text-arc-gray-100"
          rows={1}
        />
        <div className="mt-3 flex items-center justify-between">
          <p className="text-xs text-arc-gray-400">
            {input.length}/{maxChars}
          </p>
          <button
            type="button"
            onClick={onSubmit}
            disabled={isLoading || input.trim().length === 0}
            className="rounded-full bg-arc-blue px-4 py-2 text-xs font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? 'Sending…' : 'Send'}
          </button>
        </div>
      </div>
      <p className="text-xs text-arc-gray-400">
        Press Enter to send, Shift+Enter for a newline.
      </p>
    </div>
  );
}
