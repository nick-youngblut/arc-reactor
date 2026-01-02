'use client';

import { useEffect, useState } from 'react';

interface LogDownloadProps {
  runId: string;
}

export function LogDownload({ runId }: LogDownloadProps) {
  const [progress, setProgress] = useState(0);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (!downloading) return undefined;
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          setDownloading(false);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
    return () => clearInterval(timer);
  }, [downloading]);

  const handleDownload = () => {
    setProgress(0);
    setDownloading(true);
    // TODO: wire to signed URL download once backend is ready.
  };

  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={handleDownload}
        disabled={downloading}
        className="rounded-full border border-arc-gray-200/70 px-3 py-1.5 text-xs font-semibold text-arc-gray-600 transition hover:bg-arc-gray-100 disabled:opacity-60 dark:border-arc-gray-800/70 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800"
      >
        ⬇ Download logs
      </button>
      {downloading ? (
        <div className="h-2 w-24 overflow-hidden rounded-full bg-arc-gray-200">
          <div className="h-full bg-arc-blue" style={{ width: `${progress}%` }} />
        </div>
      ) : (
        <p className="text-[10px] text-arc-gray-400">Includes nextflow.log, trace.txt, timeline.html, report.html</p>
      )}
    </div>
  );
}
