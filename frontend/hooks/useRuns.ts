'use client';

import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { fetchRuns, type RunStatus, type RunSummary } from '@/lib/api';

export type RunFilters = {
  status?: RunStatus | 'all';
  pipeline?: string | 'all';
  search?: string;
  dateRange?: { from?: string; to?: string };
};

export type RunPagination = {
  page: number;
  pageSize: number;
  totalPages: number;
  totalItems: number;
};

const isActiveStatus = (status: RunStatus) =>
  status === 'pending' || status === 'submitted' || status === 'running';

export function useRuns(initialFilters: RunFilters = {}) {
  const [filters, setFiltersState] = useState<RunFilters>({
    status: 'all',
    pipeline: 'all',
    search: '',
    dateRange: {},
    ...initialFilters
  });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const query = useQuery({
    queryKey: ['runs'],
    queryFn: fetchRuns,
    refetchInterval: (data) => {
      if (!data) return 30000;
      return data.some((run) => isActiveStatus(run.status)) ? 10000 : false;
    }
  });

  const filteredRuns = useMemo(() => {
    const data = query.data ?? [];
    return data.filter((run) => {
      if (filters.status && filters.status !== 'all' && run.status !== filters.status) {
        return false;
      }
      if (filters.pipeline && filters.pipeline !== 'all' && run.pipeline !== filters.pipeline) {
        return false;
      }
      if (filters.search) {
        const term = filters.search.toLowerCase();
        if (!run.id.toLowerCase().includes(term) && !run.pipeline.toLowerCase().includes(term)) {
          return false;
        }
      }
      if (filters.dateRange?.from) {
        const fromDate = new Date(filters.dateRange.from);
        const created = run.createdAt ? new Date(run.createdAt) : null;
        if (!created || created < fromDate) {
          return false;
        }
      }
      if (filters.dateRange?.to) {
        const toDate = new Date(filters.dateRange.to);
        const created = run.createdAt ? new Date(run.createdAt) : null;
        if (!created || created > toDate) {
          return false;
        }
      }
      return true;
    });
  }, [filters, query.data]);

  const pagedRuns = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredRuns.slice(start, start + pageSize);
  }, [filteredRuns, page, pageSize]);

  const totalPages = Math.max(1, Math.ceil(filteredRuns.length / pageSize));

  const setFilters = (next: RunFilters) => {
    setFiltersState((prev) => ({ ...prev, ...next }));
    setPage(1);
  };

  return {
    runs: pagedRuns as RunSummary[],
    allRuns: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error as Error | null,
    pagination: {
      page,
      pageSize,
      totalPages,
      totalItems: filteredRuns.length
    } as RunPagination,
    setPage,
    setPageSize,
    filters,
    setFilters
  };
}
