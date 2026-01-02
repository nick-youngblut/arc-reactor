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
    <div className="space-y-3">
      <div className="group relative overflow-hidden rounded-2xl border border-arc-gray-100 bg-element/60 p-4 shadow-sm backdrop-blur-md transition-all duration-300 focus-within:border-arc-blue/30 focus-within:shadow-md focus-within:ring-1 focus-within:ring-arc-blue/10 dark:border-arc-gray-800">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(event) => onChange(event.target.value.slice(0, maxChars))}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          placeholder="Ask Arc Reactor to build a samplesheet, validate inputs, or launch a pipeline run."
          className="min-h-[44px] w-full resize-none border-0 bg-transparent text-sm font-medium text-content outline-none placeholder:text-arc-gray-400"
          rows={1}
        />
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
      <p className="px-2 text-[10px] font-bold uppercase tracking-widest text-arc-gray-400 opacity-60">
        Press <span className="text-arc-blue">Enter</span> to send, <span className="text-arc-blue">Shift+Enter</span> for newline.
      </p>
    </div>
  );
}
