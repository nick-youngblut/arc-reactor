'use client';

import type { RunSummary } from '@/lib/api';

const formatDate = (value?: string) => {
  if (!value) return '—';
  const date = new Date(value);
  return date.toLocaleString();
};

const formatDuration = (run: RunSummary) => {
  if (!run.startedAt) return '—';
  const start = new Date(run.startedAt).getTime();
  const end = run.completedAt ? new Date(run.completedAt).getTime() : Date.now();
  const durationMs = Math.max(0, end - start);
  const minutes = Math.floor(durationMs / 60000);
  const hours = Math.floor(minutes / 60);
  if (!minutes) return `${Math.floor(durationMs / 1000)}s`;
  if (hours) return `${hours}h ${minutes % 60}m`;
  return `${minutes}m`;
};

interface RunOverviewProps {
  run: RunSummary;
}

export function RunOverview({ run }: RunOverviewProps) {
  return (
    <div className="grid gap-6 lg:grid-cols-[2fr_1.2fr]">
      <div className="space-y-4">
        <div className="rounded-2xl border border-arc-gray-200/70 bg-white/70 p-4 text-sm text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-gray-400">
            Run metadata
          </p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <div>
              <p className="text-xs text-arc-gray-400">Pipeline</p>
              <p className="font-semibold text-arc-gray-700 dark:text-arc-gray-100">
                {run.pipeline}
              </p>
            </div>
            <div>
              <p className="text-xs text-arc-gray-400">Version</p>
              <p className="font-semibold text-arc-gray-700 dark:text-arc-gray-100">
                {run.version ?? '—'}
              </p>
            </div>
            <div>
              <p className="text-xs text-arc-gray-400">Submitted by</p>
              <p className="font-semibold text-arc-gray-700 dark:text-arc-gray-100">—</p>
            </div>
            <div>
              <p className="text-xs text-arc-gray-400">Samples</p>
              <p className="font-semibold text-arc-gray-700 dark:text-arc-gray-100">
                {run.sampleCount ?? '—'}
              </p>
            </div>
            <div>
              <p className="text-xs text-arc-gray-400">Created</p>
              <p className="font-semibold text-arc-gray-700 dark:text-arc-gray-100">
                {formatDate(run.createdAt)}
              </p>
            </div>
            <div>
              <p className="text-xs text-arc-gray-400">Started</p>
              <p className="font-semibold text-arc-gray-700 dark:text-arc-gray-100">
                {formatDate(run.startedAt)}
              </p>
            </div>
            <div>
              <p className="text-xs text-arc-gray-400">Completed</p>
              <p className="font-semibold text-arc-gray-700 dark:text-arc-gray-100">
                {formatDate(run.completedAt)}
              </p>
            </div>
            <div>
              <p className="text-xs text-arc-gray-400">Duration</p>
              <p className="font-semibold text-arc-gray-700 dark:text-arc-gray-100">
                {formatDuration(run)}
              </p>
            </div>
          </div>
        </div>

        {run.status === 'failed' ? (
          <div className="rounded-2xl border border-arc-error/30 bg-arc-error/5 p-4 text-sm text-arc-gray-700 dark:text-arc-gray-100">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-error">
              Error summary
            </p>
            <p className="mt-3 font-medium">Pipeline exited with an error.</p>
            <div className="mt-2 text-xs text-arc-gray-500 dark:text-arc-gray-300">
              <p>Failed task: —</p>
              <p>Exit code: —</p>
            </div>
          </div>
        ) : null}
      </div>

      <div className="space-y-4">
        <div className="rounded-2xl border border-arc-gray-200/70 bg-white/70 p-4 text-sm text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-gray-400">
            Source information
          </p>
          <div className="mt-3 space-y-2 text-xs text-arc-gray-500 dark:text-arc-gray-300">
            <p>NGS runs: —</p>
            <p>Project: —</p>
          </div>
        </div>

        <div className="rounded-2xl border border-arc-gray-200/70 bg-white/70 p-4 text-sm text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-gray-400">
            Metrics
          </p>
          <div className="mt-3 space-y-2 text-xs text-arc-gray-500 dark:text-arc-gray-300">
            <p>Total runtime: {formatDuration(run)}</p>
            <p>Tasks completed: —</p>
            <p>CPU / memory usage: —</p>
          </div>
        </div>
      </div>
    </div>
  );
}
