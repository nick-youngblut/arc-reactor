type RunDetailPageProps = {
  params: { id: string };
};

export default function RunDetailPage({ params }: RunDetailPageProps) {
  return (
    <section className="space-y-3">
      <p className="text-sm font-semibold uppercase tracking-[0.3em] text-arc-gray-400">
        Run detail
      </p>
      <h1 className="text-3xl font-semibold text-content">Run {params.id}</h1>
      <p className="max-w-2xl text-sm text-arc-gray-500 dark:text-arc-gray-300">
        This is a placeholder for the run detail view. Overview, logs, files, and parameters land
        here in Phase 4.4.
      </p>
    </section>
  );
}
