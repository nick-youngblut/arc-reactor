import { create } from 'zustand';

export type ThemeMode = 'light' | 'dark';

interface UiState {
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  activeTab: string;
  theme: ThemeMode;
  toggleSidebar: () => void;
  toggleSidebarCollapsed: () => void;
  setActiveTab: (tab: string) => void;
  setTheme: (theme: ThemeMode) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: false,
  sidebarCollapsed: false,
  activeTab: 'samplesheet',
  theme: 'light',
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  toggleSidebarCollapsed: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setTheme: (theme) => set({ theme })
}));
