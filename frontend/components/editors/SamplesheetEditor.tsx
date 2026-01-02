'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { HotTable } from '@handsontable/react';
import { registerAllModules } from 'handsontable/registry';

import 'handsontable/dist/handsontable.full.min.css';

import { getSamplesheetColumns } from '@/lib/handsontable/columnConfig';
import {
  type SamplesheetRow,
  validateSamplesheetRows
} from '@/lib/handsontable/validators';
import { parseSamplesheetCsv, serializeSamplesheetCsv } from '@/lib/handsontable/csv';
import { useWorkspaceStore } from '@/stores/workspaceStore';

registerAllModules();

interface SamplesheetEditorProps {
  readOnly?: boolean;
}

export function SamplesheetEditor({ readOnly = false }: SamplesheetEditorProps) {
  const hotRef = useRef<HotTable>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isLocalUpdate = useRef(false);

  const samplesheet = useWorkspaceStore((state) => state.samplesheet);
  const selectedPipeline = useWorkspaceStore((state) => state.selectedPipeline);
  const setSamplesheet = useWorkspaceStore((state) => state.setSamplesheet);
  const setValidationResult = useWorkspaceStore((state) => state.setValidationResult);

  const columns = useMemo(() => getSamplesheetColumns(selectedPipeline), [selectedPipeline]);
  const [rows, setRows] = useState<SamplesheetRow[]>(() =>
    parseSamplesheetCsv(samplesheet, columns)
  );
  const [invalidCells, setInvalidCells] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (isLocalUpdate.current) {
      isLocalUpdate.current = false;
      return;
    }
    setRows(parseSamplesheetCsv(samplesheet, columns));
  }, [samplesheet, columns]);

  useEffect(() => {
    const { result, invalidCells: nextInvalid } = validateSamplesheetRows(rows, columns);
    setInvalidCells(nextInvalid);
    setValidationResult(result);
  }, [rows, columns, setValidationResult]);

  const colHeaders = columns.map((column) =>
    column.required ? `${column.label} *` : column.label
  );

  const hotColumns = columns.map((column) => ({
    data: column.key,
    type: column.type,
    source: column.options
  }));

  const handleDataChange = (_changes: unknown, source?: string) => {
    if (source === 'loadData') return;
    const data = hotRef.current?.hotInstance.getSourceData() as SamplesheetRow[] | undefined;
    if (!data) return;
    setRows(data);

    isLocalUpdate.current = true;
    setSamplesheet(serializeSamplesheetCsv(data, columns));
  };

  const handleExport = () => {
    const csv = serializeSamplesheetCsv(rows, columns);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'samplesheet.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result ?? '');
      const parsed = parseSamplesheetCsv(text, columns);
      setRows(parsed);
      isLocalUpdate.current = true;
      setSamplesheet(serializeSamplesheetCsv(parsed, columns));
    };
    reader.readAsText(file);
  };

  const invalidCount = invalidCells.size;

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-arc-gray-400">
            Samplesheet
          </p>
          <p className="text-xs text-arc-gray-500 dark:text-arc-gray-300">
            Edit sample metadata and FASTQ paths.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className="rounded-full border border-arc-gray-200/70 px-3 py-1.5 text-xs font-semibold text-arc-gray-600 transition hover:bg-arc-gray-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-arc-gray-800/70 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800"
            onClick={handleExport}
          >
            Export CSV
          </button>
          <button
            type="button"
            className="rounded-full border border-arc-gray-200/70 px-3 py-1.5 text-xs font-semibold text-arc-gray-600 transition hover:bg-arc-gray-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-arc-gray-800/70 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800"
            onClick={() => fileInputRef.current?.click()}
            disabled={readOnly}
          >
            Import CSV
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleImport}
          />
        </div>
      </div>

      <div className="flex-1 overflow-hidden rounded-2xl border border-arc-gray-200/70 bg-white/70 p-2 dark:border-arc-gray-800/70 dark:bg-slate-900/70">
        <HotTable
          ref={hotRef}
          data={rows}
          columns={hotColumns}
          colHeaders={colHeaders}
          rowHeaders
          width="100%"
          height="100%"
          licenseKey="non-commercial-and-evaluation"
          stretchH="all"
          contextMenu={!readOnly}
          manualColumnResize
          readOnly={readOnly}
          allowInsertRow={!readOnly}
          allowRemoveRow={!readOnly}
          filters
          dropdownMenu
          afterChange={handleDataChange}
          cells={(row, col) => {
            const columnKey = columns[col]?.key;
            const cellKey = `${row}:${columnKey}`;
            if (invalidCells.has(cellKey)) {
              return { className: 'hot-invalid-cell' };
            }
            return {};
          }}
        />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-arc-gray-500 dark:text-arc-gray-300">
        <span>{rows.length} samples</span>
        <span className={invalidCount ? 'text-arc-error' : ''}>
          {invalidCount ? `${invalidCount} errors found` : 'All required fields complete'}
        </span>
      </div>
    </div>
  );
}
