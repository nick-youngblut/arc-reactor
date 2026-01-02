'use client';

import { useMemo, useState } from 'react';

import { ToolInvocation } from '@/stores/chatStore';

const statusConfig = {
  pending: { label: 'Running…', color: 'text-arc-warning', bg: 'bg-arc-warning/10' },
  running: { label: 'Running…', color: 'text-arc-warning', bg: 'bg-arc-warning/10' },
  completed: { label: 'Done', color: 'text-arc-success', bg: 'bg-arc-success/10' },
  error: { label: 'Failed', color: 'text-arc-error', bg: 'bg-arc-error/10' }
} as const;

const toolCategoryStyles: Record<string, string> = {
  benchling: 'border-arc-blue/30 text-arc-blue',
  pipelines: 'border-arc-secondary/30 text-arc-secondary',
  runs: 'border-arc-warning/30 text-arc-warning'
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
    () => (invocation.result ? JSON.stringify(invocation.result, null, 2) : null),
    [invocation.result]
  );

  return (
    <div className="rounded-2xl border border-arc-gray-200/70 bg-white/70 p-3 text-xs text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200">
      <button
        type="button"
        onClick={() => setIsExpanded((prev) => !prev)}
        disabled={invocation.state === 'pending' || invocation.state === 'running'}
        className="flex w-full items-center justify-between gap-3 text-left"
      >
        <div className="flex items-center gap-3">
          <span
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${
              toolCategoryStyles[category] ?? 'border-arc-gray-200 text-arc-gray-500'
            }`}
          >
            <span className="text-sm">{isExpanded ? '▼' : '▶'}</span>
            {invocation.toolName}
          </span>
          <span className={`inline-flex items-center gap-2 rounded-full px-2 py-1 ${status.bg}`}>
            <span className={`h-2 w-2 rounded-full ${status.color} bg-current`} />
            <span className={`text-xs font-semibold ${status.color}`}>{status.label}</span>
          </span>
        </div>
        {invocation.state === 'pending' || invocation.state === 'running' ? (
          <span className="text-[10px] text-arc-gray-400">In progress</span>
        ) : null}
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
