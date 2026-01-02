'use client';

const prompts = [
  'Find my samples from last week',
  'Search for SspArc0050',
  'Run scRNA-seq analysis',
  'Show available pipelines'
];

export function SuggestedPrompts({ onSelect }: { onSelect: (prompt: string) => void }) {
  return (
    <div className="mt-6 space-y-3">
      <p className="text-xs font-semibold uppercase tracking-[0.3em] text-arc-gray-400">
        Suggested prompts
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        {prompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => onSelect(prompt)}
            className="rounded-2xl border border-arc-gray-200/70 bg-white px-4 py-3 text-left text-sm text-arc-gray-600 transition hover:border-arc-blue/60 hover:text-arc-blue dark:border-arc-gray-800/70 dark:bg-slate-900 dark:text-arc-gray-200"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
