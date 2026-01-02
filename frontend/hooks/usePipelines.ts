'use client';

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

import { fetchPipelines, type PipelineSummary } from '@/lib/api';

export function usePipelines() {
  const listQuery = useQuery({
    queryKey: ['pipelines'],
    queryFn: fetchPipelines,
    staleTime: Infinity
  });

  const pipelineMap = useMemo(() => {
    const map = new Map<string, PipelineSummary>();
    (listQuery.data ?? []).forEach((pipeline) => {
      map.set(pipeline.name, pipeline);
    });
    return map;
  }, [listQuery.data]);

  const getPipeline = (name: string) => pipelineMap.get(name) ?? null;

  return {
    pipelines: listQuery.data ?? [],
    getPipeline,
    isLoading: listQuery.isLoading,
    error: listQuery.error as Error | null
  };
}
