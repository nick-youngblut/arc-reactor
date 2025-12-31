type RunDetailPageProps = {
  params: { id: string };
};

export default function RunDetailPage({ params }: RunDetailPageProps) {
  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="text-3xl font-semibold text-arc-navy">Run {params.id}</h1>
      <p className="mt-4 text-base text-arc-slate">
        This is a placeholder for the run detail view.
      </p>
    </main>
  );
}
