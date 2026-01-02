'use client';

import { useState } from 'react';

import { RecoveryAdvancedOptions } from '@/components/runs/RecoveryAdvancedOptions';

interface RecoveryModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (payload: {
    notes: string;
    overrides: Array<{ key: string; value: string }>;
    overrideConfig: string;
  }) => void;
}

export function RecoveryModal({ open, onClose, onConfirm }: RecoveryModalProps) {
  const [confirmed, setConfirmed] = useState(false);
  const [notes, setNotes] = useState('');
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [overrides, setOverrides] = useState<Array<{ key: string; value: string }>>([
    { key: '', value: '' }
  ]);
  const [overrideConfig, setOverrideConfig] = useState('');

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-3xl rounded-2xl border border-arc-gray-200/70 bg-white p-6 text-sm text-arc-gray-600 shadow-xl dark:border-arc-gray-800/70 dark:bg-slate-900 dark:text-arc-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-gray-400">
              Recovery
            </p>
            <h2 className="mt-2 text-xl font-semibold text-content">Recover run with -resume</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-arc-gray-200/70 px-3 py-1 text-xs font-semibold text-arc-gray-600 dark:border-arc-gray-800/70 dark:text-arc-gray-200"
          >
            Close
          </button>
        </div>

        <p className="mt-3 text-sm text-arc-gray-500 dark:text-arc-gray-300">
          This will re-run the workflow and reuse completed tasks from the previous work directory.
        </p>

        <label className="mt-4 flex items-start gap-2 text-xs text-arc-gray-500 dark:text-arc-gray-300">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(event) => setConfirmed(event.target.checked)}
            className="mt-0.5"
          />
          I understand this will reuse the existing work directory and may incur compute costs.
        </label>

        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-arc-gray-400">Notes</p>
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            className="mt-2 w-full rounded-xl border border-arc-gray-200/70 bg-white p-3 text-xs text-arc-gray-600 dark:border-arc-gray-800/70 dark:bg-slate-900 dark:text-arc-gray-100"
            rows={3}
            placeholder="Add optional recovery notes"
          />
        </div>

        <div className="mt-4">
          <button
            type="button"
            onClick={() => setAdvancedOpen((prev) => !prev)}
            className="text-xs font-semibold text-arc-blue"
          >
            {advancedOpen ? 'Hide advanced options' : 'Show advanced options'}
          </button>
        </div>

        {advancedOpen ? (
          <div className="mt-4">
            <RecoveryAdvancedOptions
              overrides={overrides}
              onChangeOverrides={setOverrides}
              overrideConfig={overrideConfig}
              onChangeConfig={setOverrideConfig}
            />
          </div>
        ) : null}

        <div className="mt-6 flex flex-wrap justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-arc-gray-200/70 px-4 py-2 text-xs font-semibold text-arc-gray-600 dark:border-arc-gray-800/70 dark:text-arc-gray-200"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!confirmed}
            onClick={() => onConfirm({ notes, overrides, overrideConfig })}
            className="rounded-full bg-arc-blue px-4 py-2 text-xs font-semibold text-white disabled:opacity-50"
          >
            Confirm recovery
          </button>
        </div>
      </div>
    </div>
  );
}
