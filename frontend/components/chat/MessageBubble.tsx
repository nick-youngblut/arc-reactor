'use client';

import { useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';

import { ChatMessage } from '@/stores/chatStore';

import { StreamingMessage } from './StreamingMessage';
import { ToolIndicator } from './ToolIndicator';

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  const [toolsCollapsed, setToolsCollapsed] = useState(true);

  const toolSummary = useMemo(() => {
    if (!message.toolInvocations || message.toolInvocations.length === 0) return null;

    const states = message.toolInvocations.reduce((acc, invocation) => {
      acc[invocation.state] = (acc[invocation.state] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      total: message.toolInvocations.length,
      states
    };
  }, [message.toolInvocations]);

  return (
    <div className={`flex w-full flex-col gap-1.5 ${isUser ? 'items-end' : 'items-start'}`}>
      <div
        className={`rounded-3xl px-5 py-3.5 shadow-sm transition-all duration-300 hover:shadow-md ${isUser
          ? 'w-[92%] bg-arc-blue text-white rounded-tr-none'
          : 'w-[92%] bg-white border border-arc-gray-100 text-arc-night dark:bg-arc-night dark:border-arc-gray-800 dark:text-white rounded-tl-none'
          }`}
      >
        {message.toolInvocations && message.toolInvocations.length > 0 && (
          <div className="mb-4">
            <div className={`overflow-hidden rounded-2xl border border-arc-blue/20 bg-arc-blue/5 transition-all dark:border-arc-blue/30 dark:bg-arc-blue/10 ${!toolsCollapsed ? 'shadow-sm' : ''}`}>
              <button
                type="button"
                onClick={() => setToolsCollapsed(!toolsCollapsed)}
                className="flex w-full items-center justify-between px-4 py-3 text-left text-xs transition-all hover:bg-arc-blue/10"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-5 w-5 items-center justify-center rounded-md bg-arc-blue/10 text-arc-blue">
                    <svg className={`h-3 w-3 transition-transform duration-300 ${toolsCollapsed ? 'rotate-0' : 'rotate-90'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                  <span className="font-bold text-arc-gray-700 dark:text-arc-gray-100">
                    {toolSummary?.total} Tool{toolSummary?.total !== 1 ? 's' : ''} Called
                  </span>
                  {toolSummary && (
                    <div className="flex items-center gap-1">
                      {Object.entries(toolSummary.states).map(([state, count]) => (
                        <span
                          key={state}
                          className={`inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-tight ${state === 'completed' ? 'text-arc-evergreen bg-arc-evergreen/10' :
                            state === 'error' ? 'text-arc-clay bg-arc-clay/10' :
                              state === 'running' ? 'text-arc-marigold bg-arc-marigold/10' :
                                'text-arc-gray-500 bg-arc-gray-50'
                            }`}
                        >
                          {count}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-arc-gray-500">
                  {toolsCollapsed ? 'Show' : 'Hide'}
                </span>
              </button>

              {!toolsCollapsed && (
                <div className="relative space-y-1.5 p-2 pt-0">
                  {/* Subtle nesting line */}
                  <div className="absolute left-5 top-0 bottom-6 w-px bg-arc-blue/15 dark:bg-arc-blue/30" />
                  {message.toolInvocations.map((invocation) => (
                    <ToolIndicator key={invocation.toolCallId} invocation={invocation} isNested />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        <div className={`prose prose-sm max-w-none prose-p:my-1.5 prose-pre:bg-arc-gray-900/95 prose-pre:text-white prose-pre:rounded-xl ${isUser ? 'prose-invert text-white' : 'text-inherit'}`}>
          {message.isStreaming ? (
            <StreamingMessage text={message.content} isStreaming />
          ) : (
            <ReactMarkdown>{message.content || ' '}</ReactMarkdown>
          )}
        </div>
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
