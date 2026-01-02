'use client';

import { RunDetail } from '@/components/runs/RunDetail';
import { useRunEvents } from '@/hooks/useRunEvents';
import { useRunStatus } from '@/hooks/useRunStatus';

type RunDetailPageProps = {
  params: { id: string };
};

export default function RunDetailPage({ params }: RunDetailPageProps) {
  const { data: run, isLoading, error } = useRunStatus(params.id);
  const { status, isConnected } = useRunEvents(params.id, !!run);

  if (isLoading) {
    return (
      <section className="space-y-4">
        <div className="h-6 w-32 animate-pulse rounded-full bg-arc-gray-200/70 dark:bg-arc-gray-800/70" />
        <div className="h-10 w-72 animate-pulse rounded-2xl bg-arc-gray-200/70 dark:bg-arc-gray-800/70" />
        <div className="h-64 animate-pulse rounded-2xl border border-arc-gray-200/70 bg-white/60 dark:border-arc-gray-800/70 dark:bg-slate-900/60" />
      </section>
    );
  }

  if (error || !run) {
    return (
      <section className="rounded-2xl border border-arc-error/30 bg-arc-error/5 p-6 text-sm text-arc-gray-600">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-arc-gray-400">
          Run detail
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-content">Run not found</h1>
        <p className="mt-2 text-sm text-arc-gray-500">
          We could not locate run {params.id}. Check the run ID or return to the runs list.
        </p>
      </section>
    );
  }

  return (
    <div className="space-y-3">
      {isConnected ? (
        <p className="text-xs text-arc-gray-400">Live updates connected.</p>
      ) : null}
      <RunDetail run={run} statusOverride={status} />
    </div>
  );
}
