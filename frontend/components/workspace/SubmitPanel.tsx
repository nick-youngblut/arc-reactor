'use client';

import { useMemo, useState } from 'react';

import { ValidationDisplay } from '@/components/workspace/ValidationDisplay';
import { getSamplesheetColumns } from '@/lib/handsontable/columnConfig';
import { parseSamplesheetCsv } from '@/lib/handsontable/csv';
import { validateSamplesheetRows } from '@/lib/handsontable/validators';
import { useWorkspaceStore } from '@/stores/workspaceStore';

export function SubmitPanel() {
  const samplesheet = useWorkspaceStore((state) => state.samplesheet);
  const selectedPipeline = useWorkspaceStore((state) => state.selectedPipeline);
  const validationResult = useWorkspaceStore((state) => state.validationResult);
  const setValidationResult = useWorkspaceStore((state) => state.setValidationResult);

  const [showDetails, setShowDetails] = useState(false);

  const columns = useMemo(() => getSamplesheetColumns(selectedPipeline), [selectedPipeline]);
  const sampleCount = useMemo(
    () => parseSamplesheetCsv(samplesheet, columns).length,
    [samplesheet, columns]
  );

  const errorCount = validationResult?.errors.length ?? 0;
  const warningCount = validationResult?.warnings.length ?? 0;
  const isValid = validationResult?.isValid ?? false;

  const handleValidate = () => {
    const rows = parseSamplesheetCsv(samplesheet, columns);
    const { result } = validateSamplesheetRows(rows, columns);
    setValidationResult(result);
    setShowDetails(true);
  };

  return (
    <section className="flex flex-col gap-4 rounded-2xl border border-arc-gray-200/70 bg-white/70 p-4 text-sm text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          {isValid ? (
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-arc-success/15 text-arc-success">
              ✓
            </span>
          ) : errorCount ? (
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-arc-error/15 text-arc-error">
              {errorCount}
            </span>
          ) : (
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-arc-warning/15 text-arc-warning">
              ●
            </span>
          )}
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-gray-400">
              Validation
            </p>
            <p className="text-sm font-medium text-arc-gray-700 dark:text-arc-gray-100">
              {isValid
                ? 'All checks passed.'
                : errorCount
                  ? `${errorCount} errors need attention.`
                  : 'Validation pending.'}
            </p>
            {warningCount ? (
              <p className="text-xs text-arc-warning">⚠ {warningCount} warnings found.</p>
            ) : null}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className="rounded-full border border-arc-gray-200/70 px-4 py-2 text-xs font-semibold text-arc-gray-600 transition hover:bg-arc-gray-100 dark:border-arc-gray-800/70 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800"
            onClick={handleValidate}
          >
            Validate
          </button>
          <button
            type="button"
            className="rounded-full bg-arc-blue px-5 py-2 text-xs font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={errorCount > 0}
          >
            Submit Run
          </button>
        </div>
      </div>

      {validationResult ? (
        <div>
          <button
            type="button"
            className="text-xs font-semibold text-arc-blue"
            onClick={() => setShowDetails((prev) => !prev)}
          >
            {showDetails ? 'Hide validation details' : 'Show validation details'}
          </button>
          {showDetails ? (
            <div className="mt-3">
              <ValidationDisplay result={validationResult} sampleCount={sampleCount} />
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
