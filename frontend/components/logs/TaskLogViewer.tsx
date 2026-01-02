'use client';

import { useState } from 'react';

import { LogLine, type LogLevel } from '@/components/logs/LogLine';

const mockLogLines: Array<{ id: string; timestamp: string; level: LogLevel; message: string }> =
  Array.from({ length: 40 }).map((_, index) => ({
    id: `task-log-${index}`,
    timestamp: `2024-12-30 10:${String(index).padStart(2, '0')}:12`,
    level: index % 8 === 0 ? 'WARN' : 'INFO',
    message: `Task output line ${index + 1}`
  }));

interface TaskLogViewerProps {
  taskId: string | null;
}

export function TaskLogViewer({ taskId }: TaskLogViewerProps) {
  const [activeTab, setActiveTab] = useState<'stdout' | 'stderr'>('stdout');

  if (!taskId) {
    return (
      <div className="flex h-full items-center justify-center rounded-2xl border border-dashed border-arc-gray-200/80 bg-white/60 text-sm text-arc-gray-500 dark:border-arc-gray-800/80 dark:bg-slate-900/60 dark:text-arc-gray-300">
        Select a task to view its logs.
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="rounded-2xl border border-arc-gray-200/70 bg-white/70 p-4 text-xs text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-gray-400">
          Task {taskId}
        </p>
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          <div>
            <p className="text-[10px] text-arc-gray-400">Process</p>
            <p className="font-semibold text-arc-gray-700 dark:text-arc-gray-100">STAR</p>
          </div>
          <div>
            <p className="text-[10px] text-arc-gray-400">Status</p>
            <p className="font-semibold text-arc-blue">Running</p>
          </div>
          <div>
            <p className="text-[10px] text-arc-gray-400">Duration</p>
            <p className="font-semibold">12m</p>
          </div>
          <div>
            <p className="text-[10px] text-arc-gray-400">Resources</p>
            <p className="font-semibold">8 CPU · 32 GB</p>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 text-xs font-semibold">
        {(['stdout', 'stderr'] as const).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={`rounded-full px-3 py-1.5 ${
              activeTab === tab
                ? 'bg-arc-blue text-white'
                : 'border border-arc-gray-200/70 text-arc-gray-600 dark:border-arc-gray-800/70 dark:text-arc-gray-200'
            }`}
          >
            {tab.toUpperCase()}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto rounded-2xl border border-arc-gray-200/70 bg-white/70 p-3 dark:border-arc-gray-800/70 dark:bg-slate-900/70">
        {mockLogLines.map((line) => (
          <LogLine key={line.id} timestamp={line.timestamp} level={line.level} message={line.message} />
        ))}
      </div>
    </div>
  );
}
