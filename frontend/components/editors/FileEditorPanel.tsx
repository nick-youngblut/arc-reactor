'use client';

import { useEffect, useMemo, useState } from 'react';

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
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const update = () => setIsMobile(window.innerWidth < 768);
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

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
    <section className="flex h-full flex-col gap-5 p-6">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-arc-gray-100 pb-4 dark:border-arc-gray-800">
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <div className="h-1.5 w-4 rounded-full bg-arc-blue"></div>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-arc-gray-400">
              File editors
            </p>
          </div>
          <h2 className="text-xl font-extrabold tracking-tight text-content">Workspace Files</h2>
        </div>
        <button
          type="button"
          className="arc-button-primary"
        >
          Ask AI to modify
        </button>
      </header>

      <div className="flex flex-wrap gap-1.5 rounded-2xl bg-panel p-1.5 border border-arc-gray-100 dark:border-arc-gray-800">
        {tabConfig.map((tab) => {
          const meta = tabMeta[tab.id];
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2.5 rounded-xl px-4 py-2 text-xs font-bold transition-all duration-300 ${isActive
                ? 'bg-element text-arc-blue shadow-md shadow-arc-night/5'
                : 'text-arc-gray-500 hover:bg-element/50'
                }`}
            >
              {tab.label}
              <div className="flex items-center gap-1">
                {meta.dirty ? (
                  <span className="h-1.5 w-1.5 rounded-full bg-arc-marigold shadow-[0_0_8px_rgba(243,154,34,0.5)]" />
                ) : null}
                {meta.errors ? (
                  <div className="flex h-4 w-4 items-center justify-center rounded-md bg-arc-clay/15 text-[9px] font-black text-arc-clay ring-1 ring-arc-clay/20">
                    !
                  </div>
                ) : null}
                {!meta.errors && meta.valid ? (
                  <div className="flex h-4 w-4 items-center justify-center rounded-md bg-arc-evergreen/15 text-[9px] font-black text-arc-evergreen ring-1 ring-arc-evergreen/20">
                    ✓
                  </div>
                ) : null}
              </div>
            </button>
          );
        })}
      </div>

      <div className="flex-1 overflow-hidden">
        {!hasFiles ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-arc-gray-200/80 bg-panel/60 p-6 text-center text-sm text-arc-gray-500 dark:border-arc-gray-800/80 dark:text-arc-gray-300">
            <span className="text-3xl">📄</span>
            <p className="max-w-xs">
              No files yet. Chat with Arc Assistant to generate your samplesheet and config files.
            </p>
          </div>
        ) : activeTab === 'config' ? (
          <ConfigEditor readOnly={isMobile} />
        ) : (
          <SamplesheetEditor readOnly={isMobile} />
        )}
      </div>
    </section>
  );
}
