'use client';

import type { RunStatus } from '@/lib/api';

const statusConfig: Record<RunStatus, { label: string; color: string; icon: string }> = {
  pending: { label: 'Pending', color: 'bg-arc-gray-200 text-arc-gray-600', icon: '○' },
  submitted: { label: 'Submitted', color: 'bg-arc-blue/10 text-arc-blue', icon: '◐' },
  running: { label: 'Running', color: 'bg-arc-blue/10 text-arc-blue', icon: '●' },
  completed: { label: 'Completed', color: 'bg-arc-success/10 text-arc-success', icon: '✓' },
  failed: { label: 'Failed', color: 'bg-arc-error/10 text-arc-error', icon: '✗' },
  cancelled: { label: 'Cancelled', color: 'bg-arc-gray-200 text-arc-gray-600', icon: '⦸' }
};

const statusDescriptions: Record<RunStatus, string> = {
  pending: 'Created, not submitted yet.',
  submitted: 'Queued for execution.',
  running: 'Pipeline is actively running.',
  completed: 'Finished successfully.',
  failed: 'Finished with errors.',
  cancelled: 'Stopped by user.'
};

interface RunStatusBadgeProps {
  status: RunStatus;
}

export function RunStatusBadge({ status }: RunStatusBadgeProps) {
  const config = statusConfig[status];

  return (
    <span
      title={statusDescriptions[status]}
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${
        config.color
      }`}
    >
      <span className={status === 'running' ? 'animate-pulse' : ''}>{config.icon}</span>
      {config.label}
    </span>
  );
}
