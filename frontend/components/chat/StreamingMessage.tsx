'use client';

export function StreamingMessage({ text, isStreaming }: { text: string; isStreaming?: boolean }) {
  return (
    <span className="whitespace-pre-wrap">
      {text}
      {isStreaming ? <span className="ml-1 inline-block h-4 w-2 animate-pulse bg-arc-blue" /> : null}
    </span>
  );
}
