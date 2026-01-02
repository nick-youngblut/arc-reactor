'use client';

import { useState } from 'react';

import type { RunSummary } from '@/lib/api';

interface RunParametersProps {
  run: RunSummary;
}

export function RunParameters({ run }: RunParametersProps) {
  const [copied, setCopied] = useState(false);
  const params = {
    pipeline: run.pipeline,
    version: run.version,
    params: {
      genome: 'GRCh38',
      protocol: '10XV3',
      aligner: 'simpleaf'
    }
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(JSON.stringify(params, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-gray-400">
          Parameters
        </p>
        <button
          type="button"
          onClick={handleCopy}
          className="rounded-full border border-arc-gray-200/70 px-3 py-1 text-xs font-semibold text-arc-gray-600 hover:bg-arc-gray-100 dark:border-arc-gray-700 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800"
        >
          {copied ? 'Copied' : 'Copy JSON'}
        </button>
      </div>
      <pre className="overflow-auto rounded-2xl border border-arc-gray-200/70 bg-arc-gray-900/95 p-4 text-xs text-arc-gray-100">
{JSON.stringify(params, null, 2)}
      </pre>
      <div className="rounded-2xl border border-arc-gray-200/70 bg-white/70 p-4 text-xs text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200">
        <p className="font-semibold text-arc-gray-700 dark:text-arc-gray-100">Expandable sections</p>
        <p className="mt-2 text-arc-gray-500 dark:text-arc-gray-300">
          Nested parameters will be grouped once the backend provides structured config data.
        </p>
      </div>
    </div>
  );
}
