'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { Header } from '@/components/Header';
import { Sidebar } from '@/components/Sidebar';
import { useUiStore } from '@/stores/uiStore';

const bottomNav = [
  { href: '/workspace', label: 'Workspace' },
  { href: '/runs', label: 'Runs' }
];

export function MainLayout({ children }: { children: React.ReactNode }) {
  const sidebarCollapsed = useUiStore((state) => state.sidebarCollapsed);

  return (
    <div className="min-h-screen bg-arc-radial dark:bg-arc-radial-dark">
      <Header />
      <div className={`mx-auto flex w-full transition-all duration-300 pb-24 pt-6 ${sidebarCollapsed ? 'gap-0' : 'gap-6'} px-4 sm:px-6`}>
        <Sidebar />
        <main className="flex-1 overflow-hidden">
          <div className="arc-surface arc-glow min-h-[70vh] w-full p-6 sm:p-8">{children}</div>
        </main>
      </div>
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
