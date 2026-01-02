'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { Header } from '@/components/Header';

const bottomNav = [
  { href: '/workspace', label: 'Workspace' },
  { href: '/runs', label: 'Runs' }
];

export function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 transition-colors duration-300">
      <Header />
      <main className="w-full px-4 py-4 sm:px-6 sm:py-6">
        {children}
      </main>
      <BottomNav />
    </div>
  );
}

function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-4 left-1/2 z-40 flex -translate-x-1/2 items-center gap-2 rounded-full border border-arc-gray-200/70 bg-white/90 px-4 py-2 shadow-lg backdrop-blur dark:border-arc-gray-800/70 dark:bg-slate-900/90 md:hidden">
      {bottomNav.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={`rounded-full px-3 py-2 text-xs font-semibold transition ${pathname?.startsWith(item.href)
            ? 'bg-arc-blue text-white'
            : 'text-arc-gray-600 hover:bg-arc-gray-100 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800'
            }`}
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
