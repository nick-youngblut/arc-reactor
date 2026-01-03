'use client';

import { useQuery } from '@tanstack/react-query';

import { fetchTaskSummary, type TaskSummary } from '@/lib/api';

interface TaskProgressProps {
  runId: string;
  isActive: boolean;
}

const getProgress = (summary: TaskSummary) => {
  if (!summary.total) return 0;
  const done = summary.completed + summary.cached;
  return Math.round((done / summary.total) * 100);
};

export function TaskProgress({ runId, isActive }: TaskProgressProps) {
  const { data: summary, isLoading } = useQuery({
    queryKey: ['runs', runId, 'tasks', 'summary'],
    queryFn: () => fetchTaskSummary(runId),
    enabled: !!runId,
    refetchInterval: isActive ? 2000 : false
  });

  if (isLoading || !summary) {
    return (
      <div className="h-20 animate-pulse rounded-2xl border border-arc-gray-200/70 bg-white/70 dark:border-arc-gray-800/70 dark:bg-slate-900/70" />
    );
  }

  const { total, completed, running, failed, cached } = summary;
  const progress = getProgress(summary);
  const completedPct = total ? (completed / total) * 100 : 0;
  const cachedPct = total ? (cached / total) * 100 : 0;
  const runningPct = total ? (running / total) * 100 : 0;
  const failedPct = total ? (failed / total) * 100 : 0;

  return (
    <div className="rounded-2xl border border-arc-gray-200/70 bg-white/70 p-4 text-sm text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-gray-400">
          Task progress
        </span>
        <span className="text-xs font-semibold text-arc-gray-500 dark:text-arc-gray-300">
          {completed + cached} / {total} ({progress}%)
        </span>
      </div>

      <div className="mt-3 h-2 overflow-hidden rounded-full bg-arc-gray-100 dark:bg-arc-gray-800">
        <div className="flex h-full">
          <div className="bg-arc-evergreen transition-all" style={{ width: `${completedPct}%` }} />
          <div className="bg-arc-blue transition-all" style={{ width: `${cachedPct}%` }} />
          <div className="bg-arc-marigold transition-all" style={{ width: `${runningPct}%` }} />
          <div className="bg-arc-clay transition-all" style={{ width: `${failedPct}%` }} />
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-3 text-xs text-arc-gray-500 dark:text-arc-gray-300">
        <span className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-arc-evergreen" />
          Completed: {completed}
        </span>
        <span className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-arc-blue" />
          Cached: {cached}
        </span>
        <span className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-arc-marigold" />
          Running: {running}
        </span>
        {failed > 0 ? (
          <span className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-arc-clay" />
            Failed: {failed}
          </span>
        ) : null}
      </div>
    </div>
  );
}
