'use client';

import { useQuery } from '@tanstack/react-query';

import { fetchRun, type RunStatus } from '@/lib/api';

const isTerminal = (status?: RunStatus) =>
  status === 'completed' || status === 'failed' || status === 'cancelled';

export function useRunStatus(runId: string) {
  return useQuery({
    queryKey: ['runs', 'detail', runId],
    queryFn: () => fetchRun(runId),
    enabled: !!runId,
    refetchInterval: (data) => {
      if (!data) return 5000;
      return isTerminal(data.status) ? false : 10000;
    }
  });
}
