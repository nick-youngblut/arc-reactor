'use client';

import { useEffect, useRef, useState } from 'react';

const placeholders = [
  'Find my samples from last week',
  'Search for SspArc0050',
  'Run scRNA-seq analysis',
  'Show available pipelines'
];



interface ChatInputProps {
  input: string;
  isLoading: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isExpanded?: boolean;
}

export function ChatInput({ input, isLoading, onChange, onSubmit, isExpanded = false }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const maxChars = 1200;

  useEffect(() => {
    if (!textareaRef.current) return;
    if (isExpanded) {
      textareaRef.current.style.height = '100%';
      return;
    }
    textareaRef.current.style.height = '0px';
    const scrollHeight = textareaRef.current.scrollHeight;
    // Ensure height accommodates the placeholder list if empty
    const minHeight = input ? 44 : 24 + (placeholders.length + 1) * 20;
    textareaRef.current.style.height = `${Math.max(scrollHeight, minHeight)}px`;
  }, [input]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if (!isLoading) onSubmit();
    }
  };

  return (
    <div className={`space-y-3 ${isExpanded ? 'flex flex-1 flex-col' : ''}`}>
      <div className={`group relative overflow-hidden rounded-2xl border border-arc-gray-100 bg-element/60 p-4 shadow-sm backdrop-blur-md transition-all duration-300 focus-within:border-arc-blue/30 focus-within:shadow-md focus-within:ring-1 focus-within:ring-arc-blue/10 dark:border-arc-gray-800 ${isExpanded ? 'flex flex-1 flex-col' : ''}`}>
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(event) => onChange(event.target.value.slice(0, maxChars))}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          className={`relative z-10 w-full resize-none border-0 bg-transparent text-sm font-medium text-content outline-none transition-all duration-200 ${isExpanded ? 'flex-1' : 'min-h-[44px]'}`}
          rows={1}
        />
        {!input && (
          <div className="pointer-events-none absolute inset-0 p-4 text-sm text-arc-gray-400">
            <p className="font-medium mb-1 opacity-70">Try asking:</p>
            {placeholders.map((p) => (
              <p key={p} className="pl-2 leading-relaxed opacity-50">• {p}</p>
            ))}
          </div>
        )}
        <div className="mt-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <p className={`text-[10px] font-bold uppercase tracking-widest ${input.length > maxChars * 0.9 ? 'text-arc-marigold' : 'text-arc-gray-400'}`}>
              {input.length} <span className="opacity-50">/</span> {maxChars}
            </p>
            {isLoading && (
              <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-arc-blue">
                <div className="h-1.5 w-1.5 rounded-full bg-arc-blue animate-ping"></div>
                Agent thinking...
              </div>
            )}
          </div>
          <button
            type="button"
            onClick={onSubmit}
            disabled={isLoading || input.trim().length === 0}
            className="arc-button-primary scale-90 origin-right transition-transform disabled:scale-95 disabled:opacity-30"
          >
            {isLoading ? 'Processing…' : 'Send'}
          </button>
        </div>
      </div>
      <p className={`px-2 text-[10px] font-bold uppercase tracking-widest text-arc-gray-400 opacity-60 ${isExpanded ? 'mt-auto' : ''}`}>
        Press <span className="text-arc-blue">Enter</span> to send, <span className="text-arc-blue">Shift+Enter</span> for newline.
      </p>
    </div>
  );
}
