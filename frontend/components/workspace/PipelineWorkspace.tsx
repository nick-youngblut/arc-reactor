'use client';

import { useEffect, useState } from 'react';

import { ChatPanel } from '@/components/chat/ChatPanel';
import { FileEditorPanel } from '@/components/editors/FileEditorPanel';
import { SubmitPanel } from '@/components/workspace/SubmitPanel';
import { useWorkspaceStore } from '@/stores/workspaceStore';

const pipelines = [
  { name: 'nf-core/scrnaseq', versions: ['2.7.0', '2.6.1'] },
  { name: 'nf-core/rnaseq', versions: ['3.12.0', '3.11.0'] }
];

export function PipelineWorkspace() {
  const [pipeline, setPipeline] = useState(pipelines[0]);
  const [version, setVersion] = useState(pipelines[0].versions[0]);
  const setWorkspacePipeline = useWorkspaceStore((state) => state.setPipeline);

  useEffect(() => {
    setWorkspacePipeline(pipeline.name, version);
  }, [pipeline.name, version, setWorkspacePipeline]);

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
        <div className="arc-surface flex min-h-[520px] flex-col p-6">
          <FileEditorPanel />
        </div>
      </div>

      <SubmitPanel />
    </section>
  );
}
