'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { useUiStore } from '@/stores/uiStore';

const navLinks = [
  { href: '/workspace', label: 'Workspace' },
  { href: '/runs', label: 'Runs' }
];

export function Header() {
  const pathname = usePathname();
  const theme = useUiStore((state) => state.theme);
  const setTheme = useUiStore((state) => state.setTheme);
  const toggleSidebar = useUiStore((state) => state.toggleSidebar);

  const toggleTheme = () => setTheme(theme === 'dark' ? 'light' : 'dark');

  return (
    <header className="sticky top-0 z-40 border-b border-arc-gray-200/80 bg-white/80 backdrop-blur dark:border-arc-gray-800/80 dark:bg-slate-900/70">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-4">
          <button
            className="flex h-9 w-9 items-center justify-center rounded-full border border-arc-gray-200/70 bg-white text-arc-gray-700 transition hover:bg-arc-gray-100 dark:border-arc-gray-700/70 dark:bg-slate-900 dark:text-arc-gray-200 lg:hidden"
            onClick={toggleSidebar}
            type="button"
            aria-label="Toggle navigation"
          >
            <span className="sr-only">Toggle sidebar</span>
            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M3 5h14v2H3V5zm0 6h14v2H3v-2zm0 6h14v2H3v-2z" />
            </svg>
          </button>
          <Link href="/workspace" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-arc-blue text-white shadow-glow">
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2v4m0 12v4m10-10h-4M6 12H2m15.5-6.5-3 3m0 9 3 3M8.5 5.5l3 3m0 9-3 3" />
              </svg>
            </span>
            <div className="hidden sm:block">
              <p className="text-sm font-semibold text-arc-gray-800 dark:text-white">Arc Reactor</p>
              <p className="text-xs text-arc-gray-500 dark:text-arc-gray-300">
                Pipeline workspace
              </p>
            </div>
          </Link>
        </div>

        <nav className="hidden items-center gap-2 md:flex">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                pathname?.startsWith(link.href)
                  ? 'bg-arc-blue text-white shadow-glow'
                  : 'text-arc-gray-600 hover:bg-arc-gray-100 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800'
              }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <button
            className="hidden rounded-full border border-arc-gray-200/70 px-3 py-2 text-xs font-semibold text-arc-gray-600 transition hover:bg-arc-gray-100 dark:border-arc-gray-700/70 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800 sm:inline-flex"
            onClick={toggleTheme}
            type="button"
          >
            {theme === 'dark' ? 'Light mode' : 'Dark mode'}
          </button>
          <details className="group relative">
            <summary className="flex cursor-pointer list-none items-center gap-3 rounded-full border border-arc-gray-200/70 bg-white px-3 py-1.5 text-sm font-medium text-arc-gray-700 transition hover:bg-arc-gray-100 dark:border-arc-gray-700/70 dark:bg-slate-900 dark:text-arc-gray-100 dark:hover:bg-arc-gray-800">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-arc-gray-100 text-sm font-semibold text-arc-gray-700 dark:bg-arc-gray-800 dark:text-arc-gray-100">
                AN
              </span>
              <span className="hidden text-left sm:block">
                <span className="block text-xs text-arc-gray-500 dark:text-arc-gray-300">Arcinstitute.org</span>
                <span className="block text-sm">arc.user@arcinstitute.org</span>
              </span>
            </summary>
            <div className="absolute right-0 mt-3 w-52 rounded-2xl border border-arc-gray-200/70 bg-white p-2 shadow-lg dark:border-arc-gray-700/70 dark:bg-slate-900">
              <Link
                href="/settings"
                className="block rounded-xl px-3 py-2 text-sm text-arc-gray-600 transition hover:bg-arc-gray-100 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800"
              >
                Settings
              </Link>
              <button
                className="mt-1 w-full rounded-xl px-3 py-2 text-left text-sm text-arc-gray-600 transition hover:bg-arc-gray-100 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800"
                type="button"
              >
                Log out
              </button>
              <button
                className="mt-2 w-full rounded-xl border border-arc-gray-200/70 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-arc-gray-500 transition hover:bg-arc-gray-100 dark:border-arc-gray-700/70 dark:text-arc-gray-300 dark:hover:bg-arc-gray-800 sm:hidden"
                onClick={toggleTheme}
                type="button"
              >
                Toggle {theme === 'dark' ? 'light' : 'dark'} mode
              </button>
            </div>
          </details>
        </div>
      </div>
    </header>
  );
}
