'use client';

import { useMemo, useState } from 'react';

import { ToolInvocation } from '@/stores/chatStore';

const statusConfig = {
  pending: { label: 'Running…', color: 'text-arc-marigold', bg: 'bg-arc-marigold/10', border: 'border-arc-marigold/20' },
  running: { label: 'Running…', color: 'text-arc-marigold', bg: 'bg-arc-marigold/10', border: 'border-arc-marigold/20' },
  completed: { label: 'Done', color: 'text-arc-evergreen', bg: 'bg-arc-evergreen/10', border: 'border-arc-evergreen/20' },
  error: { label: 'Failed', color: 'text-arc-clay', bg: 'bg-arc-clay/10', border: 'border-arc-clay/20' }
} as const;

const toolCategoryStyles: Record<string, string> = {
  benchling: 'border-arc-blue/20 text-arc-blue bg-arc-blue/5',
  pipelines: 'border-arc-twilight/20 text-arc-twilight bg-arc-twilight/5',
  runs: 'border-arc-marigold/20 text-arc-marigold bg-arc-marigold/5'
};

function getCategory(toolName: string) {
  if (toolName.includes('benchling')) return 'benchling';
  if (toolName.includes('pipeline')) return 'pipelines';
  if (toolName.includes('run')) return 'runs';
  return 'default';
}

export function ToolIndicator({ invocation }: { invocation: ToolInvocation }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const status = statusConfig[invocation.state];
  const category = getCategory(invocation.toolName);

  const formattedArgs = useMemo(() => JSON.stringify(invocation.args, null, 2), [invocation.args]);
  const formattedResult = useMemo(
    () => (invocation.result ? (typeof invocation.result === 'string' ? invocation.result : JSON.stringify(invocation.result, null, 2)) : null),
    [invocation.result]
  );

  return (
    <div className={`overflow-hidden rounded-2xl border bg-white/50 backdrop-blur-sm transition-all duration-300 ${isExpanded ? 'shadow-lg border-arc-blue/20 shadow-arc-blue/5 ring-1 ring-arc-blue/5' : 'border-arc-gray-100 dark:border-arc-gray-800 shadow-sm'} dark:bg-night/50`}>
      <button
        type="button"
        onClick={() => setIsExpanded((prev) => !prev)}
        disabled={invocation.state === 'pending' || invocation.state === 'running'}
        className="flex w-full items-center justify-between gap-3 p-3.5 text-left"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-5 w-5 items-center justify-center rounded-md bg-arc-blue/10 text-arc-blue">
            <svg className={`h-3 w-3 transition-transform duration-300 ${isExpanded ? 'rotate-90' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M9 5l7 7-7 7" />
            </svg>
          </div>
          <span
            className={`inline-flex items-center rounded-lg border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${toolCategoryStyles[category] ?? 'border-arc-gray-200 text-arc-gray-500 bg-arc-gray-50'
              }`}
          >
            {invocation.toolName}
          </span>
          <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 border ${status.bg} ${status.border}`}>
            <span className={`h-1.5 w-1.5 rounded-full ${status.color} bg-current animate-pulse`} />
            <span className={`text-[10px] font-bold uppercase tracking-tight ${status.color}`}>{status.label}</span>
          </span>
        </div>
        {invocation.state === 'running' && (
          <span className="text-[10px] font-bold text-arc-blue animate-pulse uppercase tracking-widest">Active</span>
        )}
      </button>

      {isExpanded && invocation.state !== 'pending' && invocation.state !== 'running' ? (
        <div className="mt-3 space-y-3 rounded-xl border border-arc-gray-200/70 bg-white/90 p-3 text-xs text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-950 dark:text-arc-gray-200">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-arc-gray-400">
              Args
            </p>
            <pre className="mt-2 whitespace-pre-wrap text-[11px] leading-relaxed">{formattedArgs}</pre>
          </div>
          {formattedResult ? (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-arc-gray-400">
                Result
              </p>
              <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap text-[11px] leading-relaxed">
                {formattedResult}
              </pre>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
