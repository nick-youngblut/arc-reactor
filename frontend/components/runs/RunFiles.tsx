'use client';

import type { RunSummary } from '@/lib/api';

interface RunFile {
  name: string;
  size: string;
  updatedAt: string;
}

const formatDate = (value?: string) => {
  if (!value) return '—';
  const date = new Date(value);
  return date.toLocaleString();
};

interface RunFilesProps {
  run: RunSummary;
}

export function RunFiles({ run }: RunFilesProps) {
  const files: RunFile[] = [
    { name: 'inputs/samplesheet.csv', size: '24 KB', updatedAt: run.createdAt ?? '' },
    { name: 'inputs/nextflow.config', size: '8 KB', updatedAt: run.createdAt ?? '' },
    { name: 'logs/nextflow.log', size: '1.1 MB', updatedAt: run.completedAt ?? run.startedAt ?? '' },
    ...(run.status === 'completed'
      ? [{ name: 'results/multiqc_report.html', size: '2.4 MB', updatedAt: run.completedAt ?? '' }]
      : [])
  ];

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-arc-gray-200/70 bg-white/70 p-4 text-sm text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-gray-400">
          File browser
        </p>
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          <span className="rounded-full border border-arc-gray-200/70 px-3 py-1">inputs/</span>
          {run.status === 'completed' ? (
            <span className="rounded-full border border-arc-gray-200/70 px-3 py-1">results/</span>
          ) : null}
          <span className="rounded-full border border-arc-gray-200/70 px-3 py-1">logs/</span>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-arc-gray-200/70 bg-white/70 text-sm text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200">
        <table className="w-full border-collapse">
          <thead className="text-xs uppercase tracking-[0.2em] text-arc-gray-400">
            <tr className="border-b border-arc-gray-200/70 dark:border-arc-gray-800/70">
              <th className="px-4 py-3 text-left font-semibold">File</th>
              <th className="px-4 py-3 text-left font-semibold">Size</th>
              <th className="px-4 py-3 text-left font-semibold">Last modified</th>
              <th className="px-4 py-3 text-left font-semibold">Action</th>
            </tr>
          </thead>
          <tbody>
            {files.map((file) => (
              <tr
                key={file.name}
                className="border-b border-arc-gray-200/50 last:border-b-0 dark:border-arc-gray-800/50"
              >
                <td className="px-4 py-3 text-xs font-semibold text-arc-gray-700 dark:text-arc-gray-100">
                  {file.name}
                </td>
                <td className="px-4 py-3 text-xs">{file.size}</td>
                <td className="px-4 py-3 text-xs">{formatDate(file.updatedAt)}</td>
                <td className="px-4 py-3 text-xs">
                  <button
                    type="button"
                    className="rounded-full border border-arc-gray-200/70 px-3 py-1 text-xs font-semibold text-arc-gray-600 hover:bg-arc-gray-100 dark:border-arc-gray-700 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800"
                  >
                    Download
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
