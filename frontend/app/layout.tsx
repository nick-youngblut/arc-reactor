import '../styles/globals.css';

import type { Metadata } from 'next';

import { MainLayout } from '@/components/MainLayout';

import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'Arc Reactor',
  description: 'Arc Institute pipeline orchestration workspace',
  icons: {
    icon: '/favicon.svg'
  }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <Providers>
          <MainLayout>{children}</MainLayout>
        </Providers>
      </body>
    </html>
  );
}
