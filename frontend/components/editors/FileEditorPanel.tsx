'use client';

import { useMemo } from 'react';

import { SamplesheetEditor } from '@/components/editors/SamplesheetEditor';
import { ConfigEditor } from '@/components/editors/ConfigEditor';
import { getSamplesheetColumns } from '@/lib/handsontable/columnConfig';
import { useUiStore } from '@/stores/uiStore';
import { useWorkspaceStore } from '@/stores/workspaceStore';

const tabConfig = [
  { id: 'samplesheet', label: 'Samplesheet' },
  { id: 'config', label: 'Config' }
] as const;

export function FileEditorPanel() {
  const activeTab = useUiStore((state) => state.activeTab);
  const setActiveTab = useUiStore((state) => state.setActiveTab);
  const samplesheet = useWorkspaceStore((state) => state.samplesheet);
  const config = useWorkspaceStore((state) => state.config);
  const validationResult = useWorkspaceStore((state) => state.validationResult);
  const samplesheetDirty = useWorkspaceStore((state) => state.samplesheetDirty);
  const configDirty = useWorkspaceStore((state) => state.configDirty);
  const selectedPipeline = useWorkspaceStore((state) => state.selectedPipeline);

  const samplesheetColumns = useMemo(
    () => getSamplesheetColumns(selectedPipeline).map((column) => column.key),
    [selectedPipeline]
  );

  const samplesheetErrors =
    validationResult?.errors.filter((error) => samplesheetColumns.includes(error.field)) ?? [];
  const configErrors =
    validationResult?.errors.filter((error) => !samplesheetColumns.includes(error.field)) ?? [];

  const hasFiles = samplesheet.trim().length > 0 || config.trim().length > 0;

  const tabMeta = {
    samplesheet: {
      dirty: samplesheetDirty,
      errors: samplesheetErrors.length,
      valid: samplesheetErrors.length === 0 && samplesheet.trim().length > 0
    },
    config: {
      dirty: configDirty,
      errors: configErrors.length,
      valid: configErrors.length === 0 && config.trim().length > 0
    }
  };

  return (
    <section className="flex h-full flex-col gap-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-arc-gray-400">
            File editors
          </p>
          <h2 className="text-lg font-semibold text-content">Samplesheet & config</h2>
        </div>
        <button
          type="button"
          className="rounded-full bg-arc-blue px-4 py-2 text-xs font-semibold text-white transition hover:opacity-90"
        >
          Ask AI to modify
        </button>
      </header>

      <div className="flex flex-wrap gap-2 rounded-full border border-arc-gray-200/70 bg-white/70 p-1 text-xs font-semibold text-arc-gray-500 dark:border-arc-gray-800/70 dark:bg-slate-900/70">
        {tabConfig.map((tab) => {
          const meta = tabMeta[tab.id];
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 rounded-full px-4 py-2 transition ${
                isActive
                  ? 'bg-arc-blue text-white shadow-sm'
                  : 'text-arc-gray-500 hover:bg-arc-gray-100 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800'
              }`}
            >
              {tab.label}
              <span className="flex items-center gap-1">
                {meta.dirty ? (
                  <span className="h-1.5 w-1.5 rounded-full bg-arc-warning" />
                ) : null}
                {meta.errors ? (
                  <span className="flex h-4 w-4 items-center justify-center rounded-full bg-arc-error/15 text-[10px] text-arc-error">
                    !
                  </span>
                ) : null}
                {!meta.errors && meta.valid ? (
                  <span className="flex h-4 w-4 items-center justify-center rounded-full bg-arc-success/15 text-[10px] text-arc-success">
                    ✓
                  </span>
                ) : null}
              </span>
            </button>
          );
        })}
      </div>

      <div className="flex-1 overflow-hidden">
        {!hasFiles ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-arc-gray-200/80 bg-white/60 p-6 text-center text-sm text-arc-gray-500 dark:border-arc-gray-800/80 dark:bg-slate-900/60 dark:text-arc-gray-300">
            <span className="text-3xl">📄</span>
            <p className="max-w-xs">
              No files yet. Chat with Arc Assistant to generate your samplesheet and config files.
            </p>
          </div>
        ) : activeTab === 'config' ? (
          <ConfigEditor />
        ) : (
          <SamplesheetEditor />
        )}
      </div>
    </section>
  );
}
