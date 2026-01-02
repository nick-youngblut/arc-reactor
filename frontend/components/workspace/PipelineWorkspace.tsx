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
    <section className="flex h-full flex-col gap-8 py-2">
      <header className="flex flex-wrap items-end justify-between gap-6 px-1">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="h-1.5 w-6 rounded-full bg-arc-blue shadow-[0_0_12px_rgba(0,115,230,0.5)]"></div>
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-arc-gray-400">
              Pipeline workspace
            </p>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-content">
            Configure <span className="text-arc-blue">&</span> run pipelines
          </h1>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2 rounded-2xl bg-element/50 p-1.5 backdrop-blur-sm border border-arc-gray-100 dark:border-arc-gray-800 shadow-sm">
            <select
              className="rounded-xl border-none bg-transparent px-4 py-1.5 text-sm font-bold text-content focus:ring-0"
              value={pipeline.name}
              onChange={(event) => {
                const next = pipelines.find((item) => item.name === event.target.value) ?? pipelines[0];
                setPipeline(next);
                setVersion(next.versions[0]);
              }}
            >
              {pipelines.map((item) => (
                <option key={item.name} value={item.name} className="dark:bg-arc-night">
                  {item.name}
                </option>
              ))}
            </select>
            <div className="h-4 w-px bg-arc-gray-200 dark:bg-arc-gray-800"></div>
            <select
              className="rounded-xl border-none bg-transparent px-4 py-1.5 text-sm font-bold text-arc-blue focus:ring-0"
              value={version}
              onChange={(event) => setVersion(event.target.value)}
            >
              {pipeline.versions.map((item) => (
                <option key={item} value={item} className="dark:bg-arc-night">
                  {item}
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>

      <div className="grid flex-1 gap-8 lg:grid-cols-[2fr_3fr]">
        <div className="arc-surface flex min-h-[580px] flex-col overflow-hidden border-arc-blue/10 bg-panel/40 ring-1 ring-arc-night/5 dark:ring-white/5 shadow-2xl shadow-arc-night/5">
          <ChatPanel />
        </div>
        <div className="arc-surface flex min-h-[580px] flex-col overflow-hidden border-arc-blue/10 bg-panel/40 ring-1 ring-arc-night/5 dark:ring-white/5 shadow-2xl shadow-arc-night/5">
          <FileEditorPanel />
        </div>
      </div>

      <SubmitPanel />
    </section>
  );
}
