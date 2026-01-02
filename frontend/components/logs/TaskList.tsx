'use client';

import { useState } from 'react';

interface TaskItem {
  id: string;
  name: string;
  process: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  duration: string;
}

const taskData: TaskItem[] = [
  { id: '1', name: 'INPUT_CHECK', process: 'INPUT_CHECK', status: 'completed', duration: '2m' },
  { id: '2', name: 'FASTQC_01', process: 'FASTQC', status: 'completed', duration: '4m' },
  { id: '3', name: 'FASTQC_02', process: 'FASTQC', status: 'completed', duration: '5m' },
  { id: '4', name: 'STAR_01', process: 'STAR', status: 'running', duration: '12m' },
  { id: '5', name: 'COUNTS_01', process: 'COUNTS', status: 'queued', duration: '—' }
];

const statusIcon: Record<TaskItem['status'], string> = {
  queued: '○',
  running: '●',
  completed: '✓',
  failed: '✗'
};

interface TaskListProps {
  activeTaskId: string | null;
  onSelect: (taskId: string) => void;
}

export function TaskList({ activeTaskId, onSelect }: TaskListProps) {
  const grouped = taskData.reduce<Record<string, TaskItem[]>>((acc, task) => {
    acc[task.process] = acc[task.process] ?? [];
    acc[task.process].push(task);
    return acc;
  }, {});
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

  return (
    <div className="space-y-4">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-gray-400">Tasks</p>
      <div className="space-y-3">
        {Object.entries(grouped).map(([process, tasks]) => (
          <div key={process} className="rounded-2xl border border-arc-gray-200/70 bg-white/70 p-3 dark:border-arc-gray-800/70 dark:bg-slate-900/70">
            <button
              type="button"
              className="flex w-full items-center justify-between text-xs font-semibold text-arc-gray-700 dark:text-arc-gray-100"
              onClick={() => setCollapsed((prev) => ({ ...prev, [process]: !prev[process] }))}
            >
              <span>{process}</span>
              <span>{collapsed[process] ? '+' : '−'}</span>
            </button>
            {!collapsed[process] ? (
              <ul className="mt-3 space-y-2 text-xs text-arc-gray-500 dark:text-arc-gray-300">
                {tasks.map((task) => (
                  <li key={task.id}>
                    <button
                      type="button"
                      onClick={() => onSelect(task.id)}
                      className={`flex w-full items-center justify-between rounded-xl px-2 py-1 text-left transition ${
                        activeTaskId === task.id
                          ? 'bg-arc-blue/10 text-arc-blue'
                          : 'hover:bg-arc-gray-100/80 dark:hover:bg-slate-800/60'
                      }`}
                    >
                      <span className="flex items-center gap-2">
                        <span>{statusIcon[task.status]}</span>
                        {task.name}
                      </span>
                      <span className="text-[10px] text-arc-gray-400">{task.duration}</span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
