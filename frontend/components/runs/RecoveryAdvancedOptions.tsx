'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

interface ParamOverride {
  key: string;
  value: string;
}

interface RecoveryAdvancedOptionsProps {
  overrides: ParamOverride[];
  onChangeOverrides: (overrides: ParamOverride[]) => void;
  overrideConfig: string;
  onChangeConfig: (value: string) => void;
}

export function RecoveryAdvancedOptions({
  overrides,
  onChangeOverrides,
  overrideConfig,
  onChangeConfig
}: RecoveryAdvancedOptionsProps) {
  const [showConfig, setShowConfig] = useState(false);

  const handleOverrideChange = (index: number, field: keyof ParamOverride, value: string) => {
    const next = [...overrides];
    next[index] = { ...next[index], [field]: value };
    onChangeOverrides(next);
  };

  return (
    <div className="space-y-4 rounded-2xl border border-arc-gray-200/70 bg-white/70 p-4 text-sm text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-200">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-gray-400">
          Override parameters
        </p>
        <div className="mt-3 space-y-2">
          {overrides.map((item, index) => (
            <div key={`override-${index}`} className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
              <input
                type="text"
                placeholder="param"
                value={item.key}
                onChange={(event) => handleOverrideChange(index, 'key', event.target.value)}
                className="rounded-xl border border-arc-gray-200/70 bg-white px-3 py-2 text-xs dark:border-arc-gray-800/70 dark:bg-slate-900"
              />
              <input
                type="text"
                placeholder="value"
                value={item.value}
                onChange={(event) => handleOverrideChange(index, 'value', event.target.value)}
                className="rounded-xl border border-arc-gray-200/70 bg-white px-3 py-2 text-xs dark:border-arc-gray-800/70 dark:bg-slate-900"
              />
              <button
                type="button"
                className="rounded-full border border-arc-gray-200/70 px-3 py-2 text-[10px] font-semibold text-arc-gray-600 dark:border-arc-gray-800/70 dark:text-arc-gray-200"
                onClick={() => onChangeOverrides(overrides.filter((_, idx) => idx !== index))}
              >
                Remove
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={() => onChangeOverrides([...overrides, { key: '', value: '' }])}
            className="rounded-full border border-arc-gray-200/70 px-3 py-1 text-[10px] font-semibold text-arc-gray-600 dark:border-arc-gray-800/70 dark:text-arc-gray-200"
          >
            + Add param override
          </button>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-gray-400">
            Override config
          </p>
          <button
            type="button"
            onClick={() => setShowConfig((prev) => !prev)}
            className="text-xs font-semibold text-arc-blue"
          >
            {showConfig ? 'Hide editor' : 'Edit config'}
          </button>
        </div>
        {showConfig ? (
          <div className="mt-3 overflow-hidden rounded-2xl border border-arc-gray-200/70 bg-white/70 dark:border-arc-gray-800/70 dark:bg-slate-900/70">
            <MonacoEditor
              value={overrideConfig}
              onChange={(value) => onChangeConfig(value ?? '')}
              language="groovy"
              theme="vs-light"
              height={200}
              options={{
                minimap: { enabled: false },
                lineNumbers: 'on',
                wordWrap: 'on',
                automaticLayout: true
              }}
            />
            <div className="border-t border-arc-gray-200/70 p-3 text-xs text-arc-gray-500 dark:border-arc-gray-800/70 dark:text-arc-gray-300">
              Diff preview will appear here once original config is available.
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
