import { create } from 'zustand';

export type ThemeMode = 'light' | 'dark';

interface UiState {
  activeTab: string;
  theme: ThemeMode;
  setActiveTab: (tab: string) => void;
  setTheme: (theme: ThemeMode) => void;
}

export const useUiStore = create<UiState>((set) => ({
  activeTab: 'samplesheet',
  theme: 'light',
  setActiveTab: (tab) => set({ activeTab: tab }),
  setTheme: (theme) => set({ theme })
}));
