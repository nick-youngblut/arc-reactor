'use client';

import ReactMarkdown from 'react-markdown';

import { ChatMessage } from '@/stores/chatStore';

import { StreamingMessage } from './StreamingMessage';
import { ToolIndicator } from './ToolIndicator';

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex flex-col gap-1.5 ${isUser ? 'items-end' : 'items-start'}`}>
      <div
        className={`rounded-3xl px-5 py-3.5 shadow-sm transition-all duration-300 hover:shadow-md ${isUser
          ? 'max-w-[80%] bg-arc-blue text-white rounded-tr-none'
          : 'max-w-[85%] bg-white border border-arc-gray-100 text-arc-night dark:bg-arc-night dark:border-arc-gray-800 dark:text-white rounded-tl-none'
          }`}
      >
        <div className={`prose prose-sm max-w-none prose-p:my-1.5 prose-pre:bg-arc-gray-900/95 prose-pre:text-white prose-pre:rounded-xl ${isUser ? 'prose-invert text-white' : 'text-inherit'}`}>
          {message.isStreaming ? (
            <StreamingMessage text={message.content} isStreaming />
          ) : (
            <ReactMarkdown>{message.content || ' '}</ReactMarkdown>
          )}
        </div>

        {message.toolInvocations && message.toolInvocations.length > 0 && (
          <div className="mt-4 space-y-2 border-t border-arc-gray-100/20 pt-3 dark:border-white/10">
            {message.toolInvocations.map((invocation) => (
              <ToolIndicator key={invocation.toolCallId} invocation={invocation} />
            ))}
          </div>
        )}
      </div>
      <p className="px-2 text-[10px] font-bold uppercase tracking-widest text-arc-gray-400 opacity-60">
        {isUser ? 'You' : 'Arc Assistant'} • {new Date(message.createdAt).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit'
        })}
      </p>
    </div>
  );
}
