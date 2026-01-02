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
    <header
      className="sticky top-0 z-40 border-b backdrop-blur-xl transition-colors duration-300"
      style={{
        backgroundColor: 'rgb(var(--color-surface) / 0.7)',
        borderColor: 'rgb(var(--color-border) / 0.5)'
      }}
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-4">
          <button
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-arc-gray-200/70 bg-white text-arc-gray-700 transition-all hover:bg-arc-gray-50 dark:border-arc-gray-700/50 dark:bg-arc-night dark:text-arc-gray-200 lg:hidden"
            onClick={toggleSidebar}
            type="button"
            aria-label="Toggle navigation"
          >
            <span className="sr-only">Toggle sidebar</span>
            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M3 5h14v2H3V5zm0 6h14v2H3v-2zm0 6h14v2H3v-2z" />
            </svg>
          </button>
          <Link href="/workspace" className="flex items-center gap-3 group">
            <div className="relative h-10 w-10 overflow-hidden rounded-xl transition-transform group-hover:scale-105">
              <img
                src={theme === 'dark' ? '/arc-logo-white.png' : '/arc-logo_blue-circle.png'}
                alt="Arc Logo"
                className="h-full w-full object-contain"
              />
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-bold tracking-tight text-arc-night dark:text-white">Arc Reactor</p>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-arc-blue">
                Intelligence Layer
              </p>
            </div>
          </Link>
        </div>

        <nav className="hidden items-center gap-1 md:flex">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-xl px-4 py-1.5 text-sm font-bold transition-all ${pathname?.startsWith(link.href)
                ? 'bg-arc-blue text-white shadow-lg shadow-arc-blue/20'
                : 'text-arc-gray-600 hover:bg-arc-gray-100 dark:text-arc-gray-300 dark:hover:bg-night'
                }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <button
            className="hidden h-9 w-9 items-center justify-center rounded-xl border border-arc-gray-200/50 bg-white/50 text-arc-gray-600 backdrop-blur-sm transition-all hover:bg-white dark:border-arc-gray-700/50 dark:bg-night/50 dark:text-arc-gray-300 dark:hover:bg-night sm:flex"
            onClick={toggleTheme}
            type="button"
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {theme === 'dark' ? (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
              </svg>
            ) : (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>
          <details className="group relative">
            <summary className="flex cursor-pointer list-none items-center gap-2 rounded-xl border border-arc-gray-200/50 bg-white/50 p-1 pr-3 text-sm font-medium text-arc-gray-700 backdrop-blur-sm transition-all hover:bg-white dark:border-arc-gray-700/50 dark:bg-night/50 dark:text-arc-gray-100 dark:hover:bg-night">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-arc-blue text-[10px] font-bold text-white shadow-sm shadow-arc-blue/20">
                AN
              </span>
              <span className="hidden text-left sm:block">
                <span className="block text-xs font-bold leading-tight text-arc-night dark:text-white">arc.user</span>
              </span>
              <svg className="h-4 w-4 text-arc-gray-400 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </summary>
            <div className="absolute right-0 mt-3 w-60 origin-top-right overflow-hidden rounded-2xl border border-arc-gray-200/50 bg-white p-1.5 shadow-2xl shadow-arc-night/10 backdrop-blur-xl dark:border-arc-gray-800/50 dark:bg-night">
              <div className="px-3 py-2.5 border-b border-arc-gray-100 dark:border-arc-gray-800 mb-1">
                <p className="text-[10px] font-bold uppercase tracking-wider text-arc-gray-400">Biological intelligence</p>
                <p className="text-sm font-bold truncate text-arc-night dark:text-white">arc.user@arcinstitute.org</p>
              </div>
              <Link
                href="/settings"
                className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-arc-gray-600 transition-all hover:bg-arc-gray-50 dark:text-arc-gray-400 dark:hover:bg-arc-gray-800 hover:text-arc-blue dark:hover:text-white"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Settings
              </Link>
              <button
                className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm font-semibold text-arc-clay transition-all hover:bg-arc-clay/5"
                type="button"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Log out
              </button>
            </div>
          </details>
        </div>
      </div>
    </header>
  );
}
