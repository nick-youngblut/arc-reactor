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
  const hotRef = useRef<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isLocalUpdate = useRef(false);

  const samplesheet = useWorkspaceStore((state) => state.samplesheet);
  const selectedPipeline = useWorkspaceStore((state) => state.selectedPipeline);
  const setSamplesheet = useWorkspaceStore((state) => state.setSamplesheet);
  const setValidationResult = useWorkspaceStore((state) => state.setValidationResult);

  const columns = useMemo(() => getSamplesheetColumns(selectedPipeline), [selectedPipeline]);
  const createEmptyRow = (columnDefs: typeof columns) => {
    return columnDefs.reduce<SamplesheetRow>((acc, column) => {
      acc[column.key] = column.defaultValue ?? '';
      return acc;
    }, {});
  };
  const ensureRows = (nextRows: SamplesheetRow[], columnDefs: typeof columns) =>
    nextRows.length ? nextRows : [createEmptyRow(columnDefs)];
  const [rows, setRows] = useState<SamplesheetRow[]>(() =>
    ensureRows(parseSamplesheetCsv(samplesheet, columns), columns)
  );
  const [invalidCells, setInvalidCells] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (isLocalUpdate.current) {
      isLocalUpdate.current = false;
      return;
    }
    setRows(ensureRows(parseSamplesheetCsv(samplesheet, columns), columns));
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
    const hot = (hotRef.current as any)?.hotInstance;
    const data = hot?.getSourceData() as SamplesheetRow[] | undefined;
    if (!data) return;
    const nextCsv = serializeSamplesheetCsv(data, columns);
    if (nextCsv === samplesheet) return;

    setRows(data);
    isLocalUpdate.current = true;
    setSamplesheet(nextCsv);
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
      const parsed = ensureRows(parseSamplesheetCsv(text, columns), columns);
      setRows(parsed);
      isLocalUpdate.current = true;
      setSamplesheet(serializeSamplesheetCsv(parsed, columns));
    };
    reader.readAsText(file);
  };

  const invalidCount = invalidCells.size;

  return (
    <div className="flex h-full flex-col gap-5">
      <div className="flex flex-wrap items-end justify-between gap-4 px-1">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="h-1.5 w-4 rounded-full bg-arc-blue"></div>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-arc-gray-400">
              Samplesheet Editor
            </p>
          </div>
          <h3 className="text-sm font-bold text-content">
            Metadata <span className="text-arc-gray-400">&</span> FASTQ paths
          </h3>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className="rounded-xl border border-arc-gray-200/50 bg-element/50 px-3.5 py-1.5 text-[11px] font-bold uppercase tracking-wider text-arc-gray-600 transition-all hover:bg-element hover:text-arc-blue dark:border-arc-gray-800/50 dark:text-arc-gray-300"
            onClick={handleExport}
          >
            Export CSV
          </button>
          <button
            type="button"
            className="rounded-xl border border-arc-gray-200/50 bg-element/50 px-3.5 py-1.5 text-[11px] font-bold uppercase tracking-wider text-arc-gray-600 transition-all hover:bg-element hover:text-arc-blue dark:border-arc-gray-800/50 dark:text-arc-gray-300"
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

      <div className="flex-1 overflow-hidden rounded-2xl border border-arc-gray-200/70 bg-panel/70 p-2 dark:border-arc-gray-800/70">
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
