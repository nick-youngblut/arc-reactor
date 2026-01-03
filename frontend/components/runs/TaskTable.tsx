'use client';

import { useQuery } from '@tanstack/react-query';

import { fetchTasks, type TaskItem } from '@/lib/api';
import { formatDuration } from '@/lib/utils';

interface TaskTableProps {
  runId: string;
  isActive: boolean;
}

const STATUS_COLORS: Record<string, string> = {
  COMPLETED: 'bg-arc-evergreen/15 text-arc-evergreen',
  CACHED: 'bg-arc-blue/10 text-arc-blue',
  RUNNING: 'bg-arc-marigold/15 text-arc-marigold',
  SUBMITTED: 'bg-arc-gray-100 text-arc-gray-600',
  FAILED: 'bg-arc-clay/15 text-arc-clay'
};

export function TaskTable({ runId, isActive }: TaskTableProps) {
  const { data: tasks, isLoading } = useQuery({
    queryKey: ['runs', runId, 'tasks'],
    queryFn: () => fetchTasks(runId),
    enabled: !!runId,
    refetchInterval: isActive ? 5000 : false
  });

  if (isLoading) {
    return (
      <div className="rounded-2xl border border-arc-gray-200/70 bg-white/70 p-4 text-sm text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200">
        <div className="animate-pulse">Loading tasks...</div>
      </div>
    );
  }

  if (!tasks || tasks.length === 0) {
    return (
      <div className="rounded-2xl border border-arc-gray-200/70 bg-white/70 p-4 text-sm text-arc-gray-500 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-300">
        No tasks yet
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-arc-gray-200/70 bg-white/70 text-sm text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200">
      <table className="min-w-full divide-y divide-arc-gray-200/70 dark:divide-arc-gray-800/70">
        <thead className="bg-arc-gray-50/70 text-xs uppercase tracking-[0.2em] text-arc-gray-400 dark:bg-arc-gray-900/40">
          <tr>
            <th className="px-4 py-3 text-left font-semibold">Name</th>
            <th className="px-4 py-3 text-left font-semibold">Status</th>
            <th className="px-4 py-3 text-left font-semibold">Duration</th>
            <th className="px-4 py-3 text-left font-semibold">Exit</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-arc-gray-200/70 dark:divide-arc-gray-800/70">
          {tasks.map((task: TaskItem) => (
            <tr key={task.id} className="hover:bg-arc-gray-50/60 dark:hover:bg-arc-gray-900/40">
              <td className="px-4 py-3 text-sm font-medium text-arc-gray-700 dark:text-arc-gray-100">
                {task.name}
              </td>
              <td className="px-4 py-3">
                <span
                  className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${STATUS_COLORS[task.status] || 'bg-arc-gray-100 text-arc-gray-600'}`}
                >
                  {task.status}
                </span>
              </td>
              <td className="px-4 py-3 text-xs text-arc-gray-500 dark:text-arc-gray-300">
                {formatDuration(task.duration_ms)}
              </td>
              <td className="px-4 py-3 text-xs text-arc-gray-500 dark:text-arc-gray-300">
                {task.exit_code ?? '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
