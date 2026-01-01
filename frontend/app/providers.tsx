'use client';

import { HeroUIProvider } from '@heroui/react';

import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ThemeProvider } from '@/components/ThemeProvider';
import { QueryProvider } from '@/lib/queryClient';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <HeroUIProvider>
        <QueryProvider>
          <ErrorBoundary>{children}</ErrorBoundary>
        </QueryProvider>
      </HeroUIProvider>
    </ThemeProvider>
  );
}
