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

const apiClient = axios.create({
  baseURL: '/api',
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

export { apiClient };
