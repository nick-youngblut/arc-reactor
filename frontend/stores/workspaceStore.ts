import { create } from 'zustand';

export interface ValidationResult {
  isValid: boolean;
  errors: Array<{ field: string; message: string; sample?: string }>;
  warnings: Array<{ field: string; message: string; sample?: string }>;
}

interface WorkspaceState {
  selectedPipeline: string | null;
  selectedVersion: string | null;
  samplesheet: string;
  config: string;
  validationResult: ValidationResult | null;
  isDirty: boolean;
  samplesheetDirty: boolean;
  configDirty: boolean;
  setPipeline: (pipeline: string | null, version?: string | null) => void;
  setSamplesheet: (value: string) => void;
  setConfig: (value: string) => void;
  clearWorkspace: () => void;
  setValidationResult: (result: ValidationResult | null) => void;
}

const initialState = {
  selectedPipeline: null,
  selectedVersion: null,
  samplesheet: '',
  config: '',
  validationResult: null,
  isDirty: false,
  samplesheetDirty: false,
  configDirty: false
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
  setSamplesheet: (value) =>
    set({ samplesheet: value, isDirty: true, samplesheetDirty: true }),
  setConfig: (value) => set({ config: value, isDirty: true, configDirty: true }),
  clearWorkspace: () => set(initialState),
  setValidationResult: (result) => set({ validationResult: result })
}));
