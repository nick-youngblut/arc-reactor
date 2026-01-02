'use client';

interface LogSearchProps {
  query: string;
  matchCount: number;
  onQueryChange: (value: string) => void;
  onNext: () => void;
  onPrev: () => void;
}

export function LogSearch({ query, matchCount, onQueryChange, onNext, onPrev }: LogSearchProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="flex items-center gap-2 rounded-full border border-arc-gray-200/70 bg-white px-3 py-1.5 text-xs text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900 dark:text-arc-gray-100">
        <span>🔍</span>
        <input
          type="search"
          placeholder="Search logs"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          className="w-36 border-0 bg-transparent text-xs outline-none"
        />
      </div>
      <span className="text-xs text-arc-gray-500 dark:text-arc-gray-300">{matchCount} matches</span>
      <button
        type="button"
        className="rounded-full border border-arc-gray-200/70 px-2 py-1 text-[10px] font-semibold text-arc-gray-600 dark:border-arc-gray-800/70 dark:text-arc-gray-200"
        onClick={onPrev}
      >
        Prev
      </button>
      <button
        type="button"
        className="rounded-full border border-arc-gray-200/70 px-2 py-1 text-[10px] font-semibold text-arc-gray-600 dark:border-arc-gray-800/70 dark:text-arc-gray-200"
        onClick={onNext}
      >
        Next
      </button>
    </div>
  );
}
