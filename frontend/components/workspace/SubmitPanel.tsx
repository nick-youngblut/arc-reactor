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
    <section className="flex flex-col gap-5 rounded-2xl border border-arc-gray-100 bg-panel/60 p-5 backdrop-blur-md shadow-lg shadow-arc-night/5 dark:border-arc-gray-800">
      <div className="flex flex-wrap items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="relative">
            {isValid ? (
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-arc-evergreen text-white shadow-lg shadow-arc-evergreen/20">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            ) : errorCount ? (
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-arc-clay text-white shadow-lg shadow-arc-clay/20">
                <span className="text-lg font-black">{errorCount}</span>
              </div>
            ) : (
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-arc-marigold text-white shadow-lg shadow-arc-marigold/20">
                <div className="h-2 w-2 rounded-full bg-white animate-pulse" />
              </div>
            )}
          </div>
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-arc-gray-400">
                Analysis Readiness
              </p>
            </div>
            <p className="text-base font-extrabold tracking-tight text-content">
              {isValid
                ? 'Ready for submission'
                : errorCount
                  ? 'Attention required'
                  : 'Validation pending'}
            </p>
            {warningCount ? (
              <p className="text-[10px] font-bold text-arc-marigold uppercase tracking-wider">⚠ {warningCount} warnings</p>
            ) : null}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            className="rounded-xl border border-arc-gray-200/50 bg-element/50 px-5 py-2.5 text-xs font-bold text-content transition-all hover:bg-element dark:border-arc-gray-700/50"
            onClick={handleValidate}
          >
            Run Checks
          </button>
          <button
            type="button"
            className="arc-button-primary disabled:opacity-20 disabled:grayscale disabled:scale-100"
            disabled={errorCount > 0 || sampleCount === 0}
          >
            Launch Pipeline run
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
