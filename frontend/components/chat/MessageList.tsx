'use client';

import { useEffect, useRef, useState } from 'react';

import { ChatMessage } from '@/stores/chatStore';

import { MessageBubble } from './MessageBubble';


interface MessageListProps {
  messages: ChatMessage[];
  onSelectPrompt: (prompt: string) => void;
}

export function MessageList({ messages, onSelectPrompt }: MessageListProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [showPrompts, setShowPrompts] = useState(true);
  const [isFading, setIsFading] = useState(false);

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.scrollTop = containerRef.current.scrollHeight;
  }, [messages]);

  useEffect(() => {
    if (messages.length === 0) {
      setShowPrompts(true);
      setIsFading(false);
      return;
    }
    setIsFading(true);
    const timeout = setTimeout(() => {
      setShowPrompts(false);
      setIsFading(false);
    }, 250);
    return () => clearTimeout(timeout);
  }, [messages.length]);

  return (
    <div className="flex h-full flex-col">
      <div ref={containerRef} className="flex-1 space-y-4 overflow-y-auto pr-2">
        {showPrompts ? (
          <div
            className={`flex h-full flex-col items-center justify-center gap-6 p-6 transition-opacity duration-200 ${isFading ? 'opacity-0' : 'opacity-100'
              }`}
          >
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <MessageBubble message={message} />
            </div>
          ))
        )}
      </div>
    </div>
  );
}
