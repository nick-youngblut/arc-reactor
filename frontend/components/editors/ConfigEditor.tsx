'use client';

import dynamic from 'next/dynamic';
import type { Monaco } from '@monaco-editor/react';

import { registerNextflowLanguage } from '@/lib/monaco/nextflowLanguage';
import { useUiStore } from '@/stores/uiStore';
import { useWorkspaceStore } from '@/stores/workspaceStore';

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

interface ConfigEditorProps {
  readOnly?: boolean;
}

export function ConfigEditor({ readOnly = false }: ConfigEditorProps) {
  const theme = useUiStore((state) => state.theme);
  const config = useWorkspaceStore((state) => state.config);
  const setConfig = useWorkspaceStore((state) => state.setConfig);

  const handleBeforeMount = (monaco: Monaco) => {
    registerNextflowLanguage(monaco);
  };

  return (
    <div className="flex h-full flex-col gap-4">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-arc-gray-400">
          Nextflow config
        </p>
        <p className="text-xs text-arc-gray-500 dark:text-arc-gray-300">
          Review or edit pipeline parameters.
        </p>
      </div>

      <div className="relative flex-1 overflow-hidden rounded-2xl border border-arc-gray-200/70 bg-white/70 dark:border-arc-gray-800/70 dark:bg-slate-900/70">
        <MonacoEditor
          value={config}
          onChange={(value) => setConfig(value ?? '')}
          beforeMount={handleBeforeMount}
          language="nextflow"
          theme={theme === 'dark' ? 'vs-dark' : 'vs-light'}
          options={{
            minimap: { enabled: true },
            lineNumbers: 'on',
            wordWrap: 'off',
            automaticLayout: true,
            fontSize: 13,
            readOnly
          }}
        />
        {!config && (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center text-xs text-arc-gray-400">
            Paste or generate a nextflow.config to begin editing.
          </div>
        )}
      </div>
    </div>
  );
}
