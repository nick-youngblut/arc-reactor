'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';

import { RunStatusBadge } from '@/components/runs/RunStatusBadge';
import { RunCard } from '@/components/runs/RunCard';
import { useRuns } from '@/hooks/useRuns';
import type { RunSummary, RunStatus } from '@/lib/api';

const statusOptions: Array<{ value: RunStatus | 'all'; label: string }> = [
  { value: 'all', label: 'All statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'submitted', label: 'Submitted' },
  { value: 'running', label: 'Running' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' }
];

type SortKey = 'pipeline' | 'status' | 'createdAt' | 'sampleCount' | 'duration';

type SortConfig = { key: SortKey; direction: 'asc' | 'desc' };

const formatDate = (value?: string) => {
  if (!value) return '—';
  const date = new Date(value);
  return date.toLocaleString();
};

const getDurationMs = (run: RunSummary) => {
  if (!run.startedAt) return 0;
  const start = new Date(run.startedAt).getTime();
  const end = run.completedAt ? new Date(run.completedAt).getTime() : Date.now();
  return Math.max(0, end - start);
};

const formatDuration = (run: RunSummary) => {
  const durationMs = getDurationMs(run);
  if (!durationMs) return '—';
  const minutes = Math.floor(durationMs / 60000);
  const seconds = Math.floor((durationMs % 60000) / 1000);
  if (minutes < 1) return `${seconds}s`;
  const hours = Math.floor(minutes / 60);
  if (hours) return `${hours}h ${minutes % 60}m`;
  return `${minutes}m`;
};

export function RunList() {
  const router = useRouter();
  const { runs, allRuns, isLoading, error, filters, setFilters, pagination, setPage, setPageSize } =
    useRuns();
  const [view, setView] = useState<'table' | 'cards'>('table');
  const [sort, setSort] = useState<SortConfig>({ key: 'createdAt', direction: 'desc' });

  const pipelines = useMemo(() => {
    const names = new Set(allRuns.map((run) => run.pipeline));
    return ['all', ...Array.from(names)] as Array<string>;
  }, [allRuns]);

  const sortedRuns = useMemo(() => {
    const sorted = [...runs];
    sorted.sort((a, b) => {
      const direction = sort.direction === 'asc' ? 1 : -1;
      switch (sort.key) {
        case 'pipeline':
          return a.pipeline.localeCompare(b.pipeline) * direction;
        case 'status':
          return a.status.localeCompare(b.status) * direction;
        case 'sampleCount':
          return ((a.sampleCount ?? 0) - (b.sampleCount ?? 0)) * direction;
        case 'duration':
          return (getDurationMs(a) - getDurationMs(b)) * direction;
        case 'createdAt':
        default: {
          const aDate = a.createdAt ? new Date(a.createdAt).getTime() : 0;
          const bDate = b.createdAt ? new Date(b.createdAt).getTime() : 0;
          return (aDate - bDate) * direction;
        }
      }
    });
    return sorted;
  }, [runs, sort]);

  const handleSort = (key: SortKey) => {
    setSort((prev) => {
      if (prev.key === key) {
        return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' };
      }
      return { key, direction: 'asc' };
    });
  };

  const emptyState = !isLoading && !error && sortedRuns.length === 0;

  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-arc-gray-400">
            Runs
          </p>
          <h2 className="text-xl font-semibold text-content">Recent runs</h2>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
              view === 'table'
                ? 'bg-arc-blue text-white'
                : 'border border-arc-gray-200/70 text-arc-gray-600 hover:bg-arc-gray-100 dark:border-arc-gray-800/70 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800'
            }`}
            onClick={() => setView('table')}
          >
            Table
          </button>
          <button
            type="button"
            className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
              view === 'cards'
                ? 'bg-arc-blue text-white'
                : 'border border-arc-gray-200/70 text-arc-gray-600 hover:bg-arc-gray-100 dark:border-arc-gray-800/70 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800'
            }`}
            onClick={() => setView('cards')}
          >
            Cards
          </button>
        </div>
      </div>

      <div className="grid gap-3 rounded-2xl border border-arc-gray-200/70 bg-white/70 p-4 text-xs text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200 md:grid-cols-[1.1fr_1.1fr_1fr_1fr_0.6fr]">
        <input
          type="search"
          placeholder="Search run ID or pipeline"
          className="rounded-full border border-arc-gray-200/70 bg-white px-3 py-2 text-xs text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900 dark:text-arc-gray-100"
          value={filters.search ?? ''}
          onChange={(event) => setFilters({ search: event.target.value })}
        />
        <select
          className="rounded-full border border-arc-gray-200/70 bg-white px-3 py-2 text-xs text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900 dark:text-arc-gray-100"
          value={filters.status ?? 'all'}
          onChange={(event) => setFilters({ status: event.target.value as RunStatus | 'all' })}
        >
          {statusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <select
          className="rounded-full border border-arc-gray-200/70 bg-white px-3 py-2 text-xs text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900 dark:text-arc-gray-100"
          value={filters.pipeline ?? 'all'}
          onChange={(event) => setFilters({ pipeline: event.target.value })}
        >
          {pipelines.map((pipeline) => (
            <option key={pipeline} value={pipeline}>
              {pipeline === 'all' ? 'All pipelines' : pipeline}
            </option>
          ))}
        </select>
        <input
          type="date"
          className="rounded-full border border-arc-gray-200/70 bg-white px-3 py-2 text-xs text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900 dark:text-arc-gray-100"
          value={filters.dateRange?.from ?? ''}
          onChange={(event) =>
            setFilters({ dateRange: { ...filters.dateRange, from: event.target.value } })
          }
        />
        <input
          type="date"
          className="rounded-full border border-arc-gray-200/70 bg-white px-3 py-2 text-xs text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900 dark:text-arc-gray-100"
          value={filters.dateRange?.to ?? ''}
          onChange={(event) =>
            setFilters({ dateRange: { ...filters.dateRange, to: event.target.value } })
          }
        />
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(4)].map((_, index) => (
            <div
              key={`skeleton-${index}`}
              className="h-16 animate-pulse rounded-2xl border border-arc-gray-200/70 bg-white/60 dark:border-arc-gray-800/70 dark:bg-slate-900/60"
            />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-2xl border border-arc-error/30 bg-arc-error/5 p-4 text-sm text-arc-gray-600">
          {error.message || 'Unable to load runs.'}
        </div>
      ) : emptyState ? (
        <div className="rounded-2xl border border-dashed border-arc-gray-200/80 bg-white/60 p-10 text-center text-sm text-arc-gray-500 dark:border-arc-gray-800/80 dark:bg-slate-900/60 dark:text-arc-gray-300">
          <div className="text-3xl">📊</div>
          <p className="mt-3 font-semibold text-arc-gray-700 dark:text-arc-gray-100">
            No runs yet
          </p>
          <p className="mt-2">
            Start your first analysis in the Workspace tab to see runs here.
          </p>
        </div>
      ) : view === 'cards' ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {sortedRuns.map((run) => (
            <RunCard key={run.id} run={run} />
          ))}
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-arc-gray-200/70 bg-white/70 text-sm text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200">
          <table className="w-full border-collapse">
            <thead className="text-xs uppercase tracking-[0.2em] text-arc-gray-400">
              <tr className="border-b border-arc-gray-200/70 dark:border-arc-gray-800/70">
                <th className="px-4 py-3 text-left font-semibold">Run ID</th>
                <th className="px-4 py-3 text-left font-semibold">
                  <button type="button" onClick={() => handleSort('pipeline')}>
                    Pipeline
                  </button>
                </th>
                <th className="px-4 py-3 text-left font-semibold">
                  <button type="button" onClick={() => handleSort('status')}>
                    Status
                  </button>
                </th>
                <th className="px-4 py-3 text-left font-semibold">
                  <button type="button" onClick={() => handleSort('sampleCount')}>
                    Samples
                  </button>
                </th>
                <th className="px-4 py-3 text-left font-semibold">
                  <button type="button" onClick={() => handleSort('createdAt')}>
                    Created
                  </button>
                </th>
                <th className="px-4 py-3 text-left font-semibold">
                  <button type="button" onClick={() => handleSort('duration')}>
                    Duration
                  </button>
                </th>
                <th className="px-4 py-3 text-left font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {sortedRuns.map((run) => (
                <tr
                  key={run.id}
                  className="cursor-pointer border-b border-arc-gray-200/50 transition hover:bg-arc-gray-50/80 dark:border-arc-gray-800/50 dark:hover:bg-slate-800/60"
                  onClick={() => router.push(`/runs/${run.id}`)}
                >
                  <td className="px-4 py-3 text-xs font-semibold text-arc-gray-700 dark:text-arc-gray-100">
                    {run.id}
                  </td>
                  <td className="px-4 py-3">
                    <p className="font-semibold text-arc-gray-700 dark:text-arc-gray-100">
                      {run.pipeline}
                    </p>
                    <p className="text-xs text-arc-gray-500 dark:text-arc-gray-300">
                      {run.version ?? '—'}
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    <RunStatusBadge status={run.status} />
                  </td>
                  <td className="px-4 py-3">{run.sampleCount ?? '—'}</td>
                  <td className="px-4 py-3 text-xs">{formatDate(run.createdAt)}</td>
                  <td className="px-4 py-3 text-xs">{formatDuration(run)}</td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      className="rounded-full border border-arc-gray-200/70 px-3 py-1 text-xs font-semibold text-arc-gray-600 hover:bg-arc-gray-100 dark:border-arc-gray-700 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800"
                      onClick={(event) => {
                        event.stopPropagation();
                        router.push(`/runs/${run.id}`);
                      }}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-arc-gray-500 dark:text-arc-gray-300">
        <span>
          Page {pagination.page} of {pagination.totalPages} · {pagination.totalItems} runs
        </span>
        <div className="flex items-center gap-2">
          <select
            className="rounded-full border border-arc-gray-200/70 bg-white px-3 py-1 text-xs text-arc-gray-600 dark:border-arc-gray-700 dark:bg-slate-900 dark:text-arc-gray-200"
            value={pagination.pageSize}
            onChange={(event) => {
              setPageSize(Number(event.target.value));
              setPage(1);
            }}
          >
            {[5, 10, 20].map((size) => (
              <option key={size} value={size}>
                {size} per page
              </option>
            ))}
          </select>
          <button
            type="button"
            className="rounded-full border border-arc-gray-200/70 px-3 py-1 text-xs font-semibold text-arc-gray-600 disabled:opacity-50 dark:border-arc-gray-700 dark:text-arc-gray-200"
            onClick={() => setPage(Math.max(1, pagination.page - 1))}
            disabled={pagination.page <= 1}
          >
            Prev
          </button>
          <button
            type="button"
            className="rounded-full border border-arc-gray-200/70 px-3 py-1 text-xs font-semibold text-arc-gray-600 disabled:opacity-50 dark:border-arc-gray-700 dark:text-arc-gray-200"
            onClick={() => setPage(Math.min(pagination.totalPages, pagination.page + 1))}
            disabled={pagination.page >= pagination.totalPages}
          >
            Next
          </button>
        </div>
      </div>
    </section>
  );
}
