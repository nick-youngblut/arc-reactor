'use client';

import type { ValidationResult } from '@/stores/workspaceStore';

interface ValidationDisplayProps {
  result: ValidationResult;
  sampleCount?: number;
}

export function ValidationDisplay({ result, sampleCount }: ValidationDisplayProps) {
  const summaryLine =
    typeof sampleCount === 'number'
      ? `Samples: ${sampleCount} · File verification: pending`
      : 'File verification: pending';

  if (!result.errors.length && !result.warnings.length) {
    return (
      <div className="rounded-2xl border border-arc-gray-200/70 bg-white/70 p-4 text-sm text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200">
        <p>No validation issues found.</p>
        <p className="mt-2 text-xs text-arc-gray-500 dark:text-arc-gray-300">{summaryLine}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {result.errors.length ? (
        <div className="rounded-2xl border border-arc-error/30 bg-arc-error/5 p-4 text-sm text-arc-gray-700 dark:text-arc-gray-100">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-error">
            Errors
          </p>
          <div className="mt-3 space-y-3">
            {result.errors.map((error, index) => (
              <div key={`${error.field}-${index}`} className="flex gap-3">
                <span className="mt-0.5 text-arc-error">✗</span>
                <div>
                  <p className="font-medium">{error.message}</p>
                  <p className="text-xs text-arc-gray-500 dark:text-arc-gray-300">
                    {error.sample ? `Sample: ${error.sample}` : 'General config'} · Field:{' '}
                    {error.field}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs font-semibold">
                    <button
                      type="button"
                      className="rounded-full border border-arc-error/30 px-3 py-1 text-arc-error"
                    >
                      Fix value
                    </button>
                    <button
                      type="button"
                      className="rounded-full border border-arc-gray-200/70 px-3 py-1 text-arc-gray-600 dark:border-arc-gray-700 dark:text-arc-gray-200"
                    >
                      Ask AI
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {result.warnings.length ? (
        <div className="rounded-2xl border border-arc-warning/30 bg-arc-warning/5 p-4 text-sm text-arc-gray-700 dark:text-arc-gray-100">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-warning">
            Warnings
          </p>
          <div className="mt-3 space-y-3">
            {result.warnings.map((warning, index) => (
              <div key={`${warning.field}-${index}`} className="flex gap-3">
                <span className="mt-0.5 text-arc-warning">⚠</span>
                <div>
                  <p className="font-medium">{warning.message}</p>
                  <p className="text-xs text-arc-gray-500 dark:text-arc-gray-300">
                    {warning.sample ? `Sample: ${warning.sample}` : 'General config'} · Field:{' '}
                    {warning.field}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <p className="text-xs text-arc-gray-500 dark:text-arc-gray-300">{summaryLine}</p>
    </div>
  );
}
