'use client';

import { Toaster } from 'sonner';

import { ErrorBoundary } from '@/components/ErrorBoundary';
import { QueryProvider } from '@/components/providers/QueryProvider';
import { ThemeProvider } from '@/components/ThemeProvider';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <QueryProvider>
        <ErrorBoundary>
          {children}
          <Toaster position="top-right" richColors />
        </ErrorBoundary>
      </QueryProvider>
    </ThemeProvider>
  );
}
