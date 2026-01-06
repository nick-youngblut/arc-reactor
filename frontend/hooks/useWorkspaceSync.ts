'use client';

import { useCallback, useEffect, useRef } from 'react';
import { useDebouncedCallback } from 'use-debounce';

import {
  ApiError,
  associateWorkspaceThread,
  createWorkspace,
  fetchWorkspaceByThread,
  fetchWorkspaceDraft,
  updateWorkspaceConfig,
  updateWorkspacePipeline,
  updateWorkspaceSamplesheet
} from '@/lib/api';
import { useChatStore } from '@/stores/chatStore';
import { useWorkspaceStore } from '@/stores/workspaceStore';

const SYNC_DEBOUNCE_MS = 500;
const RETRY_BASE_DELAY_MS = 500;
const MAX_PENDING_RETRY_ATTEMPTS = 5;

interface PendingSync {
  content: string;
  retryCount: number;
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getErrorStatus(error: unknown): number | null {
  if (error instanceof ApiError) {
    return error.status ?? null;
  }
  if (typeof error === 'object' && error !== null) {
    const status = (error as { status?: number }).status;
    if (typeof status === 'number') return status;
    const responseStatus = (error as { response?: { status?: number } }).response?.status;
    if (typeof responseStatus === 'number') return responseStatus;
  }
  return null;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  return 'Request failed';
}

function isRetryableError(error: unknown): boolean {
  const status = getErrorStatus(error);
  if (status === null) return true;
  return status >= 500;
}

async function withRetry<T>(
  fn: () => Promise<T>,
  options: { maxAttempts?: number; initialDelayMs?: number } = {}
): Promise<T> {
  const maxAttempts = options.maxAttempts ?? 3;
  const initialDelayMs = options.initialDelayMs ?? RETRY_BASE_DELAY_MS;

  let attempt = 0;
  while (true) {
    try {
      return await fn();
    } catch (error) {
      attempt += 1;
      if (!isRetryableError(error) || attempt >= maxAttempts) {
        throw error;
      }
      await delay(initialDelayMs * 2 ** (attempt - 1));
    }
  }
}

export function useWorkspaceSync() {
  const threadId = useChatStore((state) => state.threadId);
  const setThreadId = useChatStore((state) => state.setThreadId);

  const samplesheet = useWorkspaceStore((state) => state.samplesheet);
  const config = useWorkspaceStore((state) => state.config);
  const samplesheetDirty = useWorkspaceStore((state) => state.samplesheetDirty);
  const configDirty = useWorkspaceStore((state) => state.configDirty);
  const samplesheetModifiedBy = useWorkspaceStore((state) => state.samplesheetModifiedBy);
  const configModifiedBy = useWorkspaceStore((state) => state.configModifiedBy);
  const selectedPipeline = useWorkspaceStore((state) => state.selectedPipeline);
  const selectedVersion = useWorkspaceStore((state) => state.selectedVersion);

  const setSyncing = useWorkspaceStore((state) => state.setSyncing);
  const setSyncError = useWorkspaceStore((state) => state.setSyncError);
  const markSamplesheetSynced = useWorkspaceStore((state) => state.markSamplesheetSynced);
  const markConfigSynced = useWorkspaceStore((state) => state.markConfigSynced);
  const loadFromBackend = useWorkspaceStore((state) => state.loadFromBackend);
  const setWorkspaceId = useWorkspaceStore((state) => state.setWorkspaceId);

  const setSyncingRef = useRef(setSyncing);
  const setSyncErrorRef = useRef(setSyncError);
  const markSamplesheetSyncedRef = useRef(markSamplesheetSynced);
  const markConfigSyncedRef = useRef(markConfigSynced);
  const loadFromBackendRef = useRef(loadFromBackend);
  const setWorkspaceIdRef = useRef(setWorkspaceId);
  const selectedPipelineRef = useRef(selectedPipeline);
  const selectedVersionRef = useRef(selectedVersion);

  useEffect(() => {
    setSyncingRef.current = setSyncing;
    setSyncErrorRef.current = setSyncError;
    markSamplesheetSyncedRef.current = markSamplesheetSynced;
    markConfigSyncedRef.current = markConfigSynced;
    loadFromBackendRef.current = loadFromBackend;
    setWorkspaceIdRef.current = setWorkspaceId;
    selectedPipelineRef.current = selectedPipeline;
    selectedVersionRef.current = selectedVersion;
  }, [
    setSyncing,
    setSyncError,
    markSamplesheetSynced,
    markConfigSynced,
    loadFromBackend,
    setWorkspaceId,
    selectedPipeline,
    selectedVersion
  ]);

  // Tracks unsent content + retry counts for offline/5xx failures.
  const pendingSyncs = useRef<{ samplesheet?: PendingSync; config?: PendingSync }>({});
  const workspaceCreationInFlight = useRef<Promise<string | null> | null>(null);
  const previousThreadId = useRef<string | null>(null);
  const hasLoadedRef = useRef(false);
  const generatedThreadRef = useRef(false);

  const setSyncErrorMessage = useCallback((error: unknown) => {
    const status = getErrorStatus(error);
    if (status === 401 || status === 403) {
      setSyncErrorRef.current('Session expired. Please refresh.');
      return;
    }
    if (status === 404) {
      setSyncErrorRef.current('Workspace not found.');
      return;
    }
    setSyncErrorRef.current(getErrorMessage(error));
  }, []);

  // Mutex-protected workspace creation to avoid duplicate drafts/threads.
  const ensureWorkspace = useCallback(async () => {
    const existingId = useWorkspaceStore.getState().workspaceId;
    if (existingId) return existingId;

    if (workspaceCreationInFlight.current) {
      return workspaceCreationInFlight.current;
    }

    const creationPromise = (async () => {
      const currentId = useWorkspaceStore.getState().workspaceId;
      if (currentId) return currentId;

      let workspace = null;
      if (threadId) {
        try {
          workspace = await fetchWorkspaceByThread(threadId);
        } catch (error) {
          if (getErrorStatus(error) !== 404) throw error;
        }
        if (!workspace) {
          workspace = await createWorkspace({
            thread_id: threadId,
            pipeline: selectedPipelineRef.current ?? null,
            version: selectedVersionRef.current ?? null
          });
        }
      } else {
        workspace = await fetchWorkspaceDraft();
        if (!workspace) {
          workspace = await createWorkspace({
            pipeline: selectedPipelineRef.current ?? null,
            version: selectedVersionRef.current ?? null
          });
        }
      }

      if (workspace) {
        loadFromBackendRef.current(workspace);
        return workspace.id;
      }
      return null;
    })();

    workspaceCreationInFlight.current = creationPromise;
    try {
      return await creationPromise;
    } finally {
      workspaceCreationInFlight.current = null;
    }
  }, [threadId]);

  const handleSyncFailure = useCallback(
    (type: 'samplesheet' | 'config', content: string, error: unknown) => {
      const retryable = isRetryableError(error);
      if (!retryable) {
        pendingSyncs.current[type] = undefined;
        setSyncErrorMessage(error);
        return;
      }

      const current = pendingSyncs.current[type];
      const retryCount = (current?.retryCount ?? 0) + 1;
      if (retryCount > MAX_PENDING_RETRY_ATTEMPTS) {
        pendingSyncs.current[type] = undefined;
        setSyncErrorRef.current('Unable to sync changes. Please try again.');
        return;
      }

      pendingSyncs.current[type] = { content, retryCount };
      setSyncErrorRef.current('Sync failed. Will retry when online.');
    },
    [setSyncErrorMessage]
  );

  // Low-level sync that assumes a workspace already exists.
  const syncFileToWorkspace = useCallback(
    async (workspaceId: string, type: 'samplesheet' | 'config', content: string) => {
      const state = useWorkspaceStore.getState();
      const modifiedBy =
        type === 'samplesheet' ? state.samplesheetModifiedBy : state.configModifiedBy;
      if (modifiedBy !== 'user') {
        return;
      }

      setSyncingRef.current(true);
      setSyncErrorRef.current(null);

      try {
        const response = await withRetry(() =>
          type === 'samplesheet'
            ? updateWorkspaceSamplesheet(workspaceId, content)
            : updateWorkspaceConfig(workspaceId, content)
        );

        setWorkspaceIdRef.current(response.id);
        if (type === 'samplesheet') {
          markSamplesheetSyncedRef.current();
        } else {
          markConfigSyncedRef.current();
        }
        pendingSyncs.current[type] = undefined;
      } catch (error) {
        handleSyncFailure(type, content, error);
      } finally {
        setSyncingRef.current(false);
      }
    },
    [handleSyncFailure]
  );

  // Sync with auto-create, retry classification, and circuit-breaker tracking.
  const syncFile = useCallback(
    async (type: 'samplesheet' | 'config', content: string) => {
      const state = useWorkspaceStore.getState();
      let workspaceId = state.workspaceId;
      if (!workspaceId) {
        try {
          workspaceId = await ensureWorkspace();
        } catch (error) {
          setSyncErrorMessage(error);
          return;
        }
      }
      if (!workspaceId) {
        setSyncErrorRef.current('Unable to create workspace.');
        return;
      }

      await syncFileToWorkspace(workspaceId, type, content);
    },
    [ensureWorkspace, setSyncErrorMessage, syncFileToWorkspace]
  );

  const syncSamplesheet = useDebouncedCallback((content: string) => {
    void syncFile('samplesheet', content);
  }, SYNC_DEBOUNCE_MS);

  const syncConfig = useDebouncedCallback((content: string) => {
    void syncFile('config', content);
  }, SYNC_DEBOUNCE_MS);

  // Ensure dirty edits are persisted before switching threads.
  const saveUnsavedChangesBeforeSwitch = useCallback(async () => {
    const state = useWorkspaceStore.getState();
    const tasks: Array<Promise<void>> = [];

    if (state.workspaceId) {
      const pending = pendingSyncs.current;
      if (state.samplesheetDirty && state.samplesheetModifiedBy === 'user') {
        tasks.push(syncFileToWorkspace(state.workspaceId, 'samplesheet', state.samplesheet));
      } else if (pending.samplesheet) {
        tasks.push(
          syncFileToWorkspace(state.workspaceId, 'samplesheet', pending.samplesheet.content)
        );
      }
      if (state.configDirty && state.configModifiedBy === 'user') {
        tasks.push(syncFileToWorkspace(state.workspaceId, 'config', state.config));
      } else if (pending.config) {
        tasks.push(syncFileToWorkspace(state.workspaceId, 'config', pending.config.content));
      }
    }

    await Promise.all(tasks);
  }, [syncFileToWorkspace]);

  // Load draft or thread workspace, creating if missing.
  const loadWorkspaceForThread = useCallback(async () => {
    setSyncingRef.current(true);
    try {
      let workspace = null;
      if (threadId) {
        try {
          workspace = await fetchWorkspaceByThread(threadId);
        } catch (error) {
          if (getErrorStatus(error) !== 404) throw error;
        }
        if (!workspace) {
          // Check for a draft workspace first and associate it with the threadId
          // This preserves any config/samplesheet the user edited before starting chat
          const draft = await fetchWorkspaceDraft();
          if (draft) {
            try {
              workspace = await associateWorkspaceThread(draft.id, threadId);
            } catch {
              // Association failed (draft may already have a threadId), create new
              workspace = await createWorkspace({
                thread_id: threadId,
                pipeline: selectedPipelineRef.current ?? null,
                version: selectedVersionRef.current ?? null
              });
            }
          } else {
            workspace = await createWorkspace({
              thread_id: threadId,
              pipeline: selectedPipelineRef.current ?? null,
              version: selectedVersionRef.current ?? null
            });
          }
        }
      } else {
        workspace = await fetchWorkspaceDraft();
        if (!workspace) {
          workspace = await createWorkspace({
            pipeline: selectedPipelineRef.current ?? null,
            version: selectedVersionRef.current ?? null
          });
        }
      }

      if (workspace) {
        loadFromBackendRef.current(workspace);
      }
    } catch (error) {
      setSyncErrorMessage(error);
    } finally {
      setSyncingRef.current(false);
    }
  }, [setSyncErrorMessage, threadId]);

  // Retry queued syncs when the browser is back online/visible.
  const retryPendingSyncs = useCallback(() => {
    const pending = pendingSyncs.current;
    (['samplesheet', 'config'] as const).forEach((type) => {
      const entry = pending[type];
      if (!entry) return;
      if (entry.retryCount >= MAX_PENDING_RETRY_ATTEMPTS) {
        pendingSyncs.current[type] = undefined;
        setSyncErrorRef.current('Unable to sync changes. Please try again.');
        return;
      }
      void syncFile(type, entry.content);
    });
  }, [syncFile]);

  useEffect(() => {
    if (samplesheetDirty && samplesheetModifiedBy === 'user') {
      syncSamplesheet(samplesheet);
    }
  }, [samplesheet, samplesheetDirty, samplesheetModifiedBy, syncSamplesheet]);

  useEffect(() => {
    if (configDirty && configModifiedBy === 'user') {
      syncConfig(config);
    }
  }, [config, configDirty, configModifiedBy, syncConfig]);

  useEffect(() => {
    const workspaceId = useWorkspaceStore.getState().workspaceId;
    if (!selectedPipeline || !workspaceId) return;

    void updateWorkspacePipeline(workspaceId, selectedPipeline, selectedVersion)
      .then((workspace) => loadFromBackendRef.current(workspace))
      .catch(() => undefined);
  }, [selectedPipeline, selectedVersion]);

  useEffect(() => {
    const currentThreadId = threadId ?? null;
    if (hasLoadedRef.current && previousThreadId.current === currentThreadId) return;

    void (async () => {
      if (hasLoadedRef.current) {
        await saveUnsavedChangesBeforeSwitch();
      }
    if (!currentThreadId && !generatedThreadRef.current) {
      if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
        generatedThreadRef.current = true;
        const fallbackId = `thread-${crypto.randomUUID()}`;
        setThreadId(fallbackId);
        previousThreadId.current = fallbackId;
        // Don't set hasLoadedRef.current = true here - let the effect run again
        // with the new threadId so loadWorkspaceForThread is called
        return;
      }
    }
      await loadWorkspaceForThread();
      const state = useWorkspaceStore.getState();
      if (state.workspaceId && threadId) {
        try {
          const associated = await associateWorkspaceThread(state.workspaceId, threadId);
          loadFromBackendRef.current(associated);
        } catch {
          // Ignore association errors to avoid blocking workspace load.
        }
      }
      previousThreadId.current = currentThreadId;
      hasLoadedRef.current = true;
    })();
  }, [loadWorkspaceForThread, saveUnsavedChangesBeforeSwitch, threadId, setThreadId]);

  useEffect(() => {
    const handleOnline = () => retryPendingSyncs();
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        retryPendingSyncs();
      }
    };

    window.addEventListener('online', handleOnline);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      window.removeEventListener('online', handleOnline);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [retryPendingSyncs]);

  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      const state = useWorkspaceStore.getState();
      const hasPending = pendingSyncs.current.samplesheet || pendingSyncs.current.config;
      if (hasPending || state.samplesheetDirty || state.configDirty) {
        event.preventDefault();
        event.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return event.returnValue;
      }
      return undefined;
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  const hasPendingSyncs = useCallback(() => {
    return Boolean(pendingSyncs.current.samplesheet || pendingSyncs.current.config);
  }, []);

  return {
    ensureWorkspace,
    syncSamplesheet,
    syncConfig,
    hasPendingSyncs
  };
}
