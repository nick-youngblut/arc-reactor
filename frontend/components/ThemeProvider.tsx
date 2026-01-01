'use client';

import { PropsWithChildren, useEffect } from 'react';

import { ThemeMode, useUiStore } from '@/stores/uiStore';

const THEME_KEY = 'arc-theme';

export function ThemeProvider({ children }: PropsWithChildren) {
  const theme = useUiStore((state) => state.theme);
  const setTheme = useUiStore((state) => state.setTheme);

  useEffect(() => {
    const stored = window.localStorage.getItem(THEME_KEY) as ThemeMode | null;
    if (stored) {
      setTheme(stored);
      return;
    }

    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setTheme(prefersDark ? 'dark' : 'light');
  }, [setTheme]);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    document.documentElement.classList.toggle('light', theme === 'light');
    window.localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  return <>{children}</>;
}
