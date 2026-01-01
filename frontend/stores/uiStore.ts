import { create } from 'zustand';

export type ThemeMode = 'light' | 'dark';

interface UiState {
  sidebarOpen: boolean;
  activeTab: string;
  theme: ThemeMode;
  toggleSidebar: () => void;
  setActiveTab: (tab: string) => void;
  setTheme: (theme: ThemeMode) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: false,
  activeTab: 'samplesheet',
  theme: 'light',
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setTheme: (theme) => set({ theme })
}));
