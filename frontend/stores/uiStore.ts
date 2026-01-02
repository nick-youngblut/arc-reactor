import { create } from 'zustand';

export type ThemeMode = 'light' | 'dark';

export interface UiState {
  activeTab: string;
  theme: ThemeMode;
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  setActiveTab: (tab: string) => void;
  setTheme: (theme: ThemeMode) => void;
  toggleSidebar: () => void;
  toggleSidebarCollapsed: () => void;
}

export const useUiStore = create<UiState>((set) => ({
  activeTab: 'samplesheet',
  theme: 'light',
  sidebarOpen: false,
  sidebarCollapsed: false,
  setActiveTab: (tab) => set({ activeTab: tab }),
  setTheme: (theme) => set({ theme }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  toggleSidebarCollapsed: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }))
}));
