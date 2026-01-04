import { create } from 'zustand';

export type ModifierType = 'agent' | 'user' | null;

export interface ValidationResult {
  isValid: boolean;
  errors: Array<{ field: string; message: string; sample?: string }>;
  warnings: Array<{ field: string; message: string; sample?: string }>;
}

export interface WorkspacePayload {
  id: string;
  pipeline: string | null;
  version: string | null;
  samplesheet: {
    content: string | null;
    modified_by: ModifierType;
    modified_at: string | null;
  };
  config: {
    content: string | null;
    modified_by: ModifierType;
    modified_at: string | null;
  };
  validation_result: {
    is_valid: boolean;
    errors: Array<{ field: string; message: string; sample?: string }>;
    warnings: Array<{ field: string; message: string; sample?: string }>;
  } | null;
}

interface WorkspaceState {
  workspaceId: string | null;
  selectedPipeline: string | null;
  selectedVersion: string | null;
  samplesheet: string;
  config: string;
  validationResult: ValidationResult | null;
  isDirty: boolean;
  samplesheetDirty: boolean;
  configDirty: boolean;
  samplesheetModifiedBy: ModifierType;
  samplesheetModifiedAt: string | null;
  configModifiedBy: ModifierType;
  configModifiedAt: string | null;
  isSyncing: boolean;
  syncError: string | null;
  lastSyncedAt: string | null;
  setPipeline: (pipeline: string | null, version?: string | null) => void;
  setSamplesheet: (value: string, modifiedBy?: ModifierType) => void;
  setConfig: (value: string, modifiedBy?: ModifierType) => void;
  clearWorkspace: () => void;
  setValidationResult: (result: ValidationResult | null) => void;
  loadFromBackend: (workspace: WorkspacePayload) => void;
  markSamplesheetSynced: () => void;
  markConfigSynced: () => void;
  setWorkspaceId: (id: string | null) => void;
  setSyncing: (isSyncing: boolean) => void;
  setSyncError: (message: string | null) => void;
  setLastSyncedAt: (timestamp: string | null) => void;
}

const initialState = {
  workspaceId: null,
  selectedPipeline: null,
  selectedVersion: null,
  samplesheet: '',
  config: '',
  validationResult: null,
  isDirty: false,
  samplesheetDirty: false,
  configDirty: false,
  samplesheetModifiedBy: null,
  samplesheetModifiedAt: null,
  configModifiedBy: null,
  configModifiedAt: null,
  isSyncing: false,
  syncError: null,
  lastSyncedAt: null
};

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  ...initialState,
  setPipeline: (pipeline, version = null) =>
    set({
      selectedPipeline: pipeline,
      selectedVersion: version,
      isDirty: false,
      samplesheetDirty: false,
      configDirty: false
    }),
  setSamplesheet: (value, modifiedBy = 'user') =>
    set((state) => {
      const samplesheetDirty = modifiedBy === 'user';
      const isDirty = samplesheetDirty || state.configDirty;
      return {
        samplesheet: value,
        isDirty,
        samplesheetDirty,
        samplesheetModifiedBy: modifiedBy,
        samplesheetModifiedAt: new Date().toISOString()
      };
    }),
  setConfig: (value, modifiedBy = 'user') =>
    set((state) => {
      const configDirty = modifiedBy === 'user';
      const isDirty = configDirty || state.samplesheetDirty;
      return {
        config: value,
        isDirty,
        configDirty,
        configModifiedBy: modifiedBy,
        configModifiedAt: new Date().toISOString()
      };
    }),
  clearWorkspace: () => set(initialState),
  setValidationResult: (result) => set({ validationResult: result }),
  loadFromBackend: (workspace) =>
    set({
      workspaceId: workspace.id,
      selectedPipeline: workspace.pipeline,
      selectedVersion: workspace.version,
      samplesheet: workspace.samplesheet.content ?? '',
      config: workspace.config.content ?? '',
      validationResult: workspace.validation_result
        ? {
            isValid: workspace.validation_result.is_valid,
            errors: workspace.validation_result.errors,
            warnings: workspace.validation_result.warnings
          }
        : null,
      isDirty: false,
      samplesheetDirty: false,
      configDirty: false,
      samplesheetModifiedBy: workspace.samplesheet.modified_by,
      samplesheetModifiedAt: workspace.samplesheet.modified_at,
      configModifiedBy: workspace.config.modified_by,
      configModifiedAt: workspace.config.modified_at,
      syncError: null
    }),
  markSamplesheetSynced: () =>
    set((state) => ({
      samplesheetDirty: false,
      isDirty: state.configDirty,
      lastSyncedAt: new Date().toISOString()
    })),
  markConfigSynced: () =>
    set((state) => ({
      configDirty: false,
      isDirty: state.samplesheetDirty,
      lastSyncedAt: new Date().toISOString()
    })),
  setWorkspaceId: (id) => set({ workspaceId: id }),
  setSyncing: (isSyncing) => set({ isSyncing }),
  setSyncError: (message) => set({ syncError: message }),
  setLastSyncedAt: (timestamp) => set({ lastSyncedAt: timestamp })
}));
