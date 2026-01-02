'use client';

import { useMemo, useState } from 'react';

import { LogDownload } from '@/components/logs/LogDownload';
import { LogSearch } from '@/components/logs/LogSearch';
import { TaskList } from '@/components/logs/TaskList';
import { TaskLogViewer } from '@/components/logs/TaskLogViewer';
import { WorkflowLogViewer } from '@/components/logs/WorkflowLogViewer';
import type { LogLevel } from '@/components/logs/LogLine';

interface RunLogsProps {
  runId: string;
}

export function RunLogs({ runId }: RunLogsProps) {
  const [activeTab, setActiveTab] = useState<'workflow' | 'tasks'>('workflow');
  const [searchQuery, setSearchQuery] = useState('');
  const [severity, setSeverity] = useState<LogLevel | 'ALL'>('ALL');
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);

  const matchCount = useMemo(() => {
    if (!searchQuery) return 0;
    return 12;
  }, [searchQuery]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2 rounded-full border border-arc-gray-200/70 bg-white/70 p-1 text-xs font-semibold text-arc-gray-500 dark:border-arc-gray-800/70 dark:bg-slate-900/70">
          <button
            type="button"
            onClick={() => setActiveTab('workflow')}
            className={`rounded-full px-4 py-2 transition ${
              activeTab === 'workflow'
                ? 'bg-arc-blue text-white'
                : 'text-arc-gray-500 hover:bg-arc-gray-100 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800'
            }`}
          >
            Workflow Log
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('tasks')}
            className={`rounded-full px-4 py-2 transition ${
              activeTab === 'tasks'
                ? 'bg-arc-blue text-white'
                : 'text-arc-gray-500 hover:bg-arc-gray-100 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800'
            }`}
          >
            Task Logs
          </button>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <LogSearch
            query={searchQuery}
            matchCount={matchCount}
            onQueryChange={setSearchQuery}
            onNext={() => undefined}
            onPrev={() => undefined}
          />
          <select
            value={severity}
            onChange={(event) => setSeverity(event.target.value as LogLevel | 'ALL')}
            className="rounded-full border border-arc-gray-200/70 bg-white px-3 py-2 text-xs text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900 dark:text-arc-gray-100"
          >
            <option value="ALL">All severities</option>
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="ERROR">ERROR</option>
            <option value="DEBUG">DEBUG</option>
          </select>
          <LogDownload runId={runId} />
        </div>
      </div>

      {activeTab === 'workflow' ? (
        <WorkflowLogViewer searchQuery={searchQuery} severity={severity} />
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1fr_2fr]">
          <TaskList activeTaskId={activeTaskId} onSelect={setActiveTaskId} />
          <TaskLogViewer taskId={activeTaskId} />
        </div>
      )}
    </div>
  );
}
