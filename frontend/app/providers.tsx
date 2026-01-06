'use client';

import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ThemeProvider } from '@/components/ThemeProvider';
import { QueryProvider } from '@/components/providers/QueryProvider';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <QueryProvider>
        <ErrorBoundary>{children}</ErrorBoundary>
      </QueryProvider>
    </ThemeProvider>
  );
}
