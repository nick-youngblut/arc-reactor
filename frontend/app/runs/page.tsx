import { RunList } from '@/components/runs/RunList';

export default function RunsPage() {
  return (
    <section className="space-y-6">
      <header>
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-arc-gray-400">
          Runs
        </p>
        <h1 className="text-3xl font-semibold text-content">Run history</h1>
        <p className="max-w-2xl text-sm text-arc-gray-500 dark:text-arc-gray-300">
          Track pipeline progress, review outcomes, and re-run experiments with confidence.
        </p>
      </header>
      <RunList />
    </section>
  );
}
