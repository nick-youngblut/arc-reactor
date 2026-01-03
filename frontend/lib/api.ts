import axios, { AxiosError } from 'axios';

export type RunStatus =
  | 'pending'
  | 'submitted'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface RunSummary {
  id: string;
  pipeline: string;
  version?: string;
  status: RunStatus;
  sampleCount?: number;
  createdAt?: string;
  startedAt?: string;
  completedAt?: string;
}

export interface PipelineSummary {
  name: string;
  version?: string;
  description?: string;
}

export interface RecoverRunOptions {
  notes?: string;
  overrideParameters?: Record<string, string | number | boolean | null>;
  overrideConfig?: string;
}

export interface TaskSummary {
  total: number;
  completed: number;
  running: number;
  submitted: number;
  failed: number;
  cached: number;
}

export interface TaskItem {
  id: string;
  run_id: string;
  task_id: number;
  hash: string;
  name: string;
  process: string;
  status: string;
  exit_code: number | null;
  submit_time: number | null;
  start_time: number | null;
  complete_time: number | null;
  duration_ms: number | null;
  realtime_ms: number | null;
  cpu_percent: number | null;
  peak_rss: number | null;
  peak_vmem: number | null;
  workdir: string | null;
  container: string | null;
  attempt: number;
  error_message: string | null;
}

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL
    ? `${process.env.NEXT_PUBLIC_API_URL}/api`
    : '/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = window.localStorage.getItem('arc-token');
    if (token) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
    }
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const message = error.response?.data?.detail ?? error.message ?? 'Request failed';
    return Promise.reject(new Error(message));
  }
);

export const fetchRuns = async () => {
  const { data } = await apiClient.get<RunSummary[]>('/runs');
  return data;
};

export const fetchRun = async (id: string) => {
  const { data } = await apiClient.get<RunSummary>(`/runs/${id}`);
  return data;
};

export const createRun = async (payload: Record<string, unknown>) => {
  const { data } = await apiClient.post<RunSummary>('/runs', payload);
  return data;
};

export const cancelRun = async (id: string) => {
  const { data } = await apiClient.post<RunSummary>(`/runs/${id}/cancel`);
  return data;
};

export const recoverRun = async (id: string, options: RecoverRunOptions) => {
  const { data } = await apiClient.post<RunSummary>(`/runs/${id}/recover`, options);
  return data;
};

export const fetchPipelines = async () => {
  const { data } = await apiClient.get<PipelineSummary[]>('/pipelines');
  return data;
};

export const fetchPipeline = async (name: string) => {
  const { data } = await apiClient.get<PipelineSummary>(`/pipelines/${name}`);
  return data;
};

export const fetchTasks = async (runId: string) => {
  const { data } = await apiClient.get<TaskItem[]>(`/runs/${runId}/tasks`);
  return data;
};

export const fetchTaskSummary = async (runId: string) => {
  const { data } = await apiClient.get<TaskSummary>(`/runs/${runId}/tasks/summary`);
  return data;
};

export { apiClient };
