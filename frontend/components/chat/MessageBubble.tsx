'use client';

import ReactMarkdown from 'react-markdown';

import { ChatMessage } from '@/stores/chatStore';

import { StreamingMessage } from './StreamingMessage';
import { ToolIndicator } from './ToolIndicator';

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  const bubbleStyles = isUser
    ? 'ml-auto bg-arc-blue text-white'
    : 'mr-auto bg-white text-arc-gray-700 dark:bg-slate-900 dark:text-arc-gray-100';

  return (
    <div className={`max-w-[85%] space-y-2 rounded-2xl px-4 py-3 shadow-sm ${bubbleStyles}`}>
      <div className="prose prose-sm max-w-none text-inherit prose-p:my-2 prose-pre:bg-arc-gray-900/90 prose-pre:text-arc-gray-100">
        {message.isStreaming ? (
          <StreamingMessage text={message.content} isStreaming />
        ) : (
          <ReactMarkdown>{message.content || ' '}</ReactMarkdown>
        )}
      </div>
      {message.toolInvocations && message.toolInvocations.length > 0 ? (
        <div className="space-y-2">
          {message.toolInvocations.map((invocation) => (
            <ToolIndicator key={invocation.toolCallId} invocation={invocation} />
          ))}
        </div>
      ) : null}
      <p className="text-[10px] uppercase tracking-[0.2em] text-arc-gray-400">
        {new Date(message.createdAt).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit'
        })}
      </p>
    </div>
  );
}
