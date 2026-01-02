'use client';

import { useState } from 'react';

import { ChatPanel } from '@/components/chat/ChatPanel';

const pipelines = [
  { name: 'nf-core/scrnaseq', versions: ['2.7.0', '2.6.1'] },
  { name: 'nf-core/rnaseq', versions: ['3.12.0', '3.11.0'] }
];

export function PipelineWorkspace() {
  const [pipeline, setPipeline] = useState(pipelines[0]);
  const [version, setVersion] = useState(pipelines[0].versions[0]);

  return (
    <section className="flex h-full flex-col gap-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-arc-gray-400">
            Pipeline workspace
          </p>
          <h1 className="text-2xl font-semibold text-content">Configure & run pipelines</h1>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <select
            className="rounded-full border border-arc-gray-200/70 bg-white px-4 py-2 text-sm text-arc-gray-700 shadow-sm dark:border-arc-gray-800/70 dark:bg-slate-900 dark:text-arc-gray-100"
            value={pipeline.name}
            onChange={(event) => {
              const next = pipelines.find((item) => item.name === event.target.value) ?? pipelines[0];
              setPipeline(next);
              setVersion(next.versions[0]);
            }}
          >
            {pipelines.map((item) => (
              <option key={item.name} value={item.name}>
                {item.name}
              </option>
            ))}
          </select>
          <select
            className="rounded-full border border-arc-gray-200/70 bg-white px-4 py-2 text-sm text-arc-gray-700 shadow-sm dark:border-arc-gray-800/70 dark:bg-slate-900 dark:text-arc-gray-100"
            value={version}
            onChange={(event) => setVersion(event.target.value)}
          >
            {pipeline.versions.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
      </header>

      <div className="grid flex-1 gap-6 lg:grid-cols-[2fr_3fr]">
        <div className="arc-surface flex min-h-[520px] flex-col p-6">
          <ChatPanel />
        </div>
        <div className="arc-surface flex min-h-[520px] flex-col items-center justify-center border border-dashed border-arc-gray-200/80 bg-white/60 p-6 text-center text-sm text-arc-gray-500 dark:border-arc-gray-800/80 dark:bg-slate-900/60 dark:text-arc-gray-300">
          File editor panel lands here in Phase 4.3.
        </div>
      </div>

      <footer className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-arc-gray-200/70 bg-white/70 px-4 py-3 text-sm text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-arc-warning" />
          Validation pending.
        </div>
        <button
          type="button"
          className="rounded-full bg-arc-blue px-5 py-2 text-xs font-semibold text-white transition hover:opacity-90"
        >
          Submit Run
        </button>
      </footer>
    </section>
  );
}
