'use client';

import { useEffect, useState } from 'react';

import type { RunStatus } from '@/lib/api';

export function useRunEvents(runId: string, enabled: boolean = true) {
  const [status, setStatus] = useState<RunStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!enabled || !runId) return undefined;

    const eventSource = new EventSource(`/api/runs/${runId}/events`);

    eventSource.addEventListener('open', () => {
      setIsConnected(true);
    });

    eventSource.addEventListener('status', (event) => {
      try {
        const data = JSON.parse((event as MessageEvent<string>).data) as RunStatus;
        setStatus(data);
      } catch {
        // ignore malformed payloads
      }
    });

    eventSource.addEventListener('done', () => {
      setIsConnected(false);
      eventSource.close();
    });

    eventSource.onerror = () => {
      setIsConnected(false);
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, [runId, enabled]);

  return { status, isConnected };
}
