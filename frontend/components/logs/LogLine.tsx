'use client';

import { useMemo } from 'react';

export type LogLevel = 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';

const levelStyles: Record<LogLevel, string> = {
  INFO: 'bg-arc-blue/10 text-arc-blue',
  WARN: 'bg-arc-warning/10 text-arc-warning',
  ERROR: 'bg-arc-error/10 text-arc-error',
  DEBUG: 'bg-arc-gray-200 text-arc-gray-600'
};

const highlightToken = (text: string, token?: string) => {
  if (!token) return text;
  const lower = text.toLowerCase();
  const search = token.toLowerCase();
  const index = lower.indexOf(search);
  if (index === -1) return text;
  return (
    <>
      {text.slice(0, index)}
      <mark className="rounded bg-arc-warning/40 px-1">{text.slice(index, index + token.length)}</mark>
      {text.slice(index + token.length)}
    </>
  );
};

const PATH_REGEX = /(gs:\/\/\S+|\/[\w\-./]+\.(?:log|txt|csv|tsv|json|yaml|yml|html|gz|bam|fastq|fastq.gz))/g;

interface LogLineProps {
  timestamp: string;
  level: LogLevel;
  message: string;
  highlight?: string;
}

export function LogLine({ timestamp, level, message, highlight }: LogLineProps) {
  const parts = useMemo(() => message.split(PATH_REGEX), [message]);

  return (
    <div className="flex flex-wrap items-start gap-3 text-xs text-arc-gray-600 dark:text-arc-gray-200">
      <span className="whitespace-nowrap text-arc-gray-400">{timestamp}</span>
      <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${levelStyles[level]}`}>
        {level}
      </span>
      <span className="font-mono text-arc-gray-700 dark:text-arc-gray-100">
        {parts.map((part, index) => {
          const isPath = PATH_REGEX.test(part);
          PATH_REGEX.lastIndex = 0;
          if (isPath) {
            return (
              <span key={`${part}-${index}`} className="text-arc-blue">
                {highlightToken(part, highlight)}
              </span>
            );
          }
          return <span key={`${part}-${index}`}>{highlightToken(part, highlight)}</span>;
        })}
      </span>
    </div>
  );
}
