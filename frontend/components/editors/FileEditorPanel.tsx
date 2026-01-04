'use client';

import { useEffect, useMemo, useRef, useState } from 'react';

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
  const setSamplesheet = useWorkspaceStore((state) => state.setSamplesheet);
  const setConfig = useWorkspaceStore((state) => state.setConfig);
  const [isMobile, setIsMobile] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const update = () => setIsMobile(window.innerWidth < 768);
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  const samplesheetColumnDefs = useMemo(
    () => getSamplesheetColumns(selectedPipeline),
    [selectedPipeline]
  );
  const samplesheetColumns = useMemo(
    () => samplesheetColumnDefs.map((column) => column.key),
    [samplesheetColumnDefs]
  );

  const samplesheetErrors =
    validationResult?.errors.filter((error) => samplesheetColumns.includes(error.field)) ?? [];
  const configErrors =
    validationResult?.errors.filter((error) => !samplesheetColumns.includes(error.field)) ?? [];

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

  const validateSamplesheetUpload = (content: string) => {
    const trimmed = content.trim();
    if (!trimmed) return null;

    const headerLine = trimmed.split(/\r?\n/).find((line) => line.trim().length > 0);
    if (!headerLine) return null;

    const delimiter = headerLine.includes('\t') && !headerLine.includes(',') ? '\t' : ',';
    const headers = headerLine
      .split(delimiter)
      .map((header) => header.trim().toLowerCase())
      .filter((header) => header.length > 0);

    const columnKeys = samplesheetColumnDefs.map((column) => column.key.toLowerCase());
    const hasKnownHeader = headers.some((header) => columnKeys.includes(header));
    if (!hasKnownHeader) {
      return `Samplesheet CSV header must include columns like: ${samplesheetColumnDefs
        .map((column) => column.key)
        .join(', ')}.`;
    }

    const missingRequired = samplesheetColumnDefs
      .filter((column) => column.required)
      .map((column) => column.key.toLowerCase())
      .filter((key) => !headers.includes(key));
    if (missingRequired.length) {
      return `Missing required columns: ${missingRequired.join(', ')}.`;
    }

    return null;
  };

  const isLikelyBinary = (content: string) => content.includes('\u0000');

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploadError(null);

    if (file.size === 0) {
      if (activeTab === 'samplesheet') {
        setSamplesheet('');
      } else {
        setConfig('');
      }
      event.target.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onerror = () => {
      setUploadError('Unable to read the selected file.');
    };
    reader.onload = () => {
      const content = String(reader.result ?? '');
      if (isLikelyBinary(content)) {
        setUploadError('This file appears to be binary. Please upload a text file.');
        return;
      }

      if (activeTab === 'samplesheet') {
        const validationError = validateSamplesheetUpload(content);
        if (validationError) {
          setUploadError(validationError);
          return;
        }
        setSamplesheet(content);
      } else {
        setConfig(content);
      }
    };

    try {
      reader.readAsText(file);
    } catch {
      setUploadError('Unable to read the selected file.');
    } finally {
      event.target.value = '';
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
          onClick={() => fileInputRef.current?.click()}
        >
          <span className="flex items-center gap-2">
            <svg
              viewBox="0 0 24 24"
              aria-hidden="true"
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 3v12" />
              <path d="m7 8 5-5 5 5" />
              <path d="M5 21h14" />
            </svg>
            Upload File
          </span>
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.tsv,.config,.nf,.txt,text/*"
          className="hidden"
          onChange={handleFileUpload}
        />
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
                ? 'bg-arc-blue text-white shadow-md shadow-arc-blue/20'
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

      {uploadError ? (
        <div className="rounded-2xl border border-arc-error/30 bg-arc-error/5 px-4 py-3 text-xs text-arc-gray-700 dark:text-arc-gray-100">
          <p className="font-semibold uppercase tracking-[0.2em] text-arc-error">
            Upload error
          </p>
          <p className="mt-2 text-arc-gray-600 dark:text-arc-gray-300">{uploadError}</p>
        </div>
      ) : null}

      <div className="flex-1 overflow-hidden">
        {activeTab === 'config' ? (
          <ConfigEditor readOnly={isMobile} />
        ) : (
          <SamplesheetEditor readOnly={isMobile} />
        )}
      </div>
    </section>
  );
}
