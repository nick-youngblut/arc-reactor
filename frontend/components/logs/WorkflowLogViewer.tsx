'use client';

import { useEffect, useMemo, useRef, useState } from 'react';

import { LogLine, type LogLevel } from '@/components/logs/LogLine';

const sampleLogs = Array.from({ length: 120 }).map((_, index) => {
  const level: LogLevel = index % 15 === 0 ? 'ERROR' : index % 7 === 0 ? 'WARN' : 'INFO';
  return {
    id: `log-${index}`,
    timestamp: `2024-12-30 10:${String(Math.floor(index / 2)).padStart(2, '0')}:${String(
      (index * 7) % 60
    ).padStart(2, '0')}`,
    level,
    message:
      index % 10 === 0
        ? `Uploading gs://arc-reactor-runs/runs/run-123/logs/nextflow.log`
        : `Process ${index} completed successfully.`
  };
});

const ROW_HEIGHT = 28;
const OVERSCAN = 8;

interface WorkflowLogViewerProps {
  searchQuery: string;
  severity: LogLevel | 'ALL';
}

export function WorkflowLogViewer({ searchQuery, severity }: WorkflowLogViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [height, setHeight] = useState(320);
  const [autoScroll, setAutoScroll] = useState(true);

  const filteredLogs = useMemo(() => {
    return sampleLogs.filter((log) => {
      if (severity !== 'ALL' && log.level !== severity) return false;
      if (searchQuery && !log.message.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    });
  }, [searchQuery, severity]);

  useEffect(() => {
    if (!containerRef.current) return;
    setHeight(containerRef.current.clientHeight);
  }, []);

  useEffect(() => {
    if (!autoScroll || !containerRef.current) return;
    containerRef.current.scrollTop = containerRef.current.scrollHeight;
  }, [autoScroll, filteredLogs.length]);

  const totalHeight = filteredLogs.length * ROW_HEIGHT;
  const startIndex = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - OVERSCAN);
  const endIndex = Math.min(
    filteredLogs.length,
    Math.ceil((scrollTop + height) / ROW_HEIGHT) + OVERSCAN
  );

  const visibleLogs = filteredLogs.slice(startIndex, endIndex);
  const topSpacer = startIndex * ROW_HEIGHT;
  const bottomSpacer = Math.max(0, totalHeight - topSpacer - visibleLogs.length * ROW_HEIGHT);

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex items-center justify-between text-xs text-arc-gray-500 dark:text-arc-gray-300">
        <span>{filteredLogs.length} log lines</span>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(event) => setAutoScroll(event.target.checked)}
            className="rounded border-arc-gray-300"
          />
          Auto-scroll
        </label>
      </div>
      <div
        ref={containerRef}
        className="h-[360px] overflow-auto rounded-2xl border border-arc-gray-200/70 bg-white/70 p-3 dark:border-arc-gray-800/70 dark:bg-slate-900/70"
        onScroll={(event) => setScrollTop(event.currentTarget.scrollTop)}
      >
        <div style={{ height: topSpacer }} />
        <div className="space-y-2">
          {visibleLogs.map((log) => (
            <LogLine
              key={log.id}
              timestamp={log.timestamp}
              level={log.level}
              message={log.message}
              highlight={searchQuery}
            />
          ))}
        </div>
        <div style={{ height: bottomSpacer }} />
      </div>
      <p className="text-[10px] text-arc-gray-400">Streaming enabled for active runs.</p>
    </div>
  );
}
