'use client';

import { useState } from 'react';

import type { RunSummary, RunStatus } from '@/lib/api';
import { RunStatusBadge } from '@/components/runs/RunStatusBadge';
import { RunOverview } from '@/components/runs/RunOverview';
import { RunFiles } from '@/components/runs/RunFiles';
import { RunParameters } from '@/components/runs/RunParameters';

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'logs', label: 'Logs' },
  { id: 'files', label: 'Files' },
  { id: 'parameters', label: 'Parameters' }
] as const;

type TabId = (typeof tabs)[number]['id'];

interface RunDetailProps {
  run: RunSummary;
  statusOverride?: RunStatus | null;
}

export function RunDetail({ run, statusOverride }: RunDetailProps) {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [copied, setCopied] = useState(false);
  const status = statusOverride ?? run.status;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(run.id);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <section className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-arc-gray-400">
            Run detail
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold text-content">{run.id}</h1>
            <button
              type="button"
              onClick={handleCopy}
              className="rounded-full border border-arc-gray-200/70 px-3 py-1 text-xs font-semibold text-arc-gray-600 hover:bg-arc-gray-100 dark:border-arc-gray-800/70 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800"
            >
              {copied ? 'Copied' : 'Copy'}
            </button>
            <RunStatusBadge status={status} />
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-full border border-arc-gray-200/70 px-4 py-2 text-xs font-semibold text-arc-gray-600 hover:bg-arc-gray-100 dark:border-arc-gray-800/70 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800"
          >
            Re-run
          </button>
          <button
            type="button"
            className="rounded-full border border-arc-gray-200/70 px-4 py-2 text-xs font-semibold text-arc-gray-600 hover:bg-arc-gray-100 dark:border-arc-gray-800/70 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800"
          >
            Recover
          </button>
          {status === 'running' || status === 'submitted' ? (
            <button
              type="button"
              className="rounded-full border border-arc-error/40 px-4 py-2 text-xs font-semibold text-arc-error"
            >
              Cancel
            </button>
          ) : null}
        </div>
      </header>

      <div className="flex flex-wrap gap-2 rounded-full border border-arc-gray-200/70 bg-white/70 p-1 text-xs font-semibold text-arc-gray-500 dark:border-arc-gray-800/70 dark:bg-slate-900/70">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`rounded-full px-4 py-2 transition ${
              activeTab === tab.id
                ? 'bg-arc-blue text-white shadow-sm'
                : 'text-arc-gray-500 hover:bg-arc-gray-100 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="min-h-[360px]">
        {activeTab === 'overview' ? <RunOverview run={run} /> : null}
        {activeTab === 'files' ? <RunFiles run={run} /> : null}
        {activeTab === 'parameters' ? <RunParameters run={run} /> : null}
        {activeTab === 'logs' ? (
          <div className="rounded-2xl border border-dashed border-arc-gray-200/80 bg-white/60 p-8 text-center text-sm text-arc-gray-500 dark:border-arc-gray-800/80 dark:bg-slate-900/60 dark:text-arc-gray-300">
            Log viewer arrives in Phase 4.5.
          </div>
        ) : null}
      </div>
    </section>
  );
}
