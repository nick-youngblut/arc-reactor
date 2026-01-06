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

export type ModifierType = 'agent' | 'user' | null;

export interface FileState {
  content: string | null;
  modified_by: ModifierType;
  modified_at: string | null;
}

export interface ValidationResult {
  is_valid: boolean;
  errors: Array<{ field: string; message: string; sample?: string }>;
  warnings: Array<{ field: string; message: string; sample?: string }>;
}

export interface WorkspaceResponse {
  id: string;
  user_email: string;
  thread_id: string | null;
  pipeline: string | null;
  version: string | null;
  samplesheet: FileState;
  config: FileState;
  validation_result: ValidationResult | null;
  created_at: string;
  updated_at: string;
}

export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
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
    return Promise.reject(new ApiError(message, error.response?.status));
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

export const fetchWorkspaceDraft = async () => {
  const { data } = await apiClient.get<WorkspaceResponse | null>('/workspaces/draft');
  return data;
};

export const fetchWorkspaceByThread = async (threadId: string) => {
  const { data } = await apiClient.get<WorkspaceResponse>(`/workspaces/by-thread/${threadId}`);
  return data;
};

export const createWorkspace = async (payload: {
  thread_id?: string | null;
  pipeline?: string | null;
  version?: string | null;
  samplesheet?: string | null;
  config?: string | null;
}) => {
  const { data } = await apiClient.post<WorkspaceResponse>('/workspaces', payload);
  return data;
};

export const updateWorkspaceSamplesheet = async (workspaceId: string, content: string) => {
  const { data } = await apiClient.patch<WorkspaceResponse>(
    `/workspaces/${workspaceId}/samplesheet`,
    { content }
  );
  return data;
};

export const updateWorkspaceConfig = async (workspaceId: string, content: string) => {
  const { data } = await apiClient.patch<WorkspaceResponse>(
    `/workspaces/${workspaceId}/config`,
    { content }
  );
  return data;
};

export const updateWorkspacePipeline = async (
  workspaceId: string,
  pipeline: string,
  version?: string | null
) => {
  const { data } = await apiClient.patch<WorkspaceResponse>(
    `/workspaces/${workspaceId}/pipeline`,
    { pipeline, version: version ?? null }
  );
  return data;
};

export const associateWorkspaceThread = async (workspaceId: string, threadId: string) => {
  const { data } = await apiClient.post<WorkspaceResponse>(
    `/workspaces/${workspaceId}/associate`,
    { thread_id: threadId }
  );
  return data;
};

export const deleteWorkspace = async (workspaceId: string) => {
  const { data } = await apiClient.delete<boolean>(`/workspaces/${workspaceId}`);
  return data;
};

export { apiClient };
