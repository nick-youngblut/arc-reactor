'use client';

import Link from 'next/link';

import type { RunSummary } from '@/lib/api';
import { RunStatusBadge } from '@/components/runs/RunStatusBadge';

const formatDate = (value?: string) => {
  if (!value) return '—';
  const date = new Date(value);
  return date.toLocaleString();
};

interface RunCardProps {
  run: RunSummary;
}

export function RunCard({ run }: RunCardProps) {
  return (
    <div className="arc-surface flex flex-col gap-4 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-gray-400">
            Run
          </p>
          <p className="text-sm font-semibold text-arc-gray-700 dark:text-arc-gray-100">
            {run.id}
          </p>
        </div>
        <RunStatusBadge status={run.status} />
      </div>

      <div className="text-xs text-arc-gray-500 dark:text-arc-gray-300">
        <p>
          Pipeline: <span className="font-semibold text-arc-gray-700 dark:text-arc-gray-100">{run.pipeline}</span>
        </p>
        <p>Version: {run.version ?? '—'}</p>
        <p>Samples: {run.sampleCount ?? '—'}</p>
        <p>Created: {formatDate(run.createdAt)}</p>
      </div>

      <div className="flex flex-wrap gap-2">
        <Link
          href={`/runs/${run.id}`}
          className="rounded-full border border-arc-gray-200/70 px-3 py-1.5 text-xs font-semibold text-arc-gray-600 transition hover:bg-arc-gray-100 dark:border-arc-gray-700 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800"
        >
          View details
        </Link>
        {run.status === 'running' || run.status === 'submitted' ? (
          <button
            type="button"
            className="rounded-full border border-arc-error/40 px-3 py-1.5 text-xs font-semibold text-arc-error"
          >
            Cancel
          </button>
        ) : null}
      </div>
    </div>
  );
}
