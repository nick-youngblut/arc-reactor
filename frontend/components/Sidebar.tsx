'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { useUiStore } from '@/stores/uiStore';

const navItems = [
  {
    href: '/workspace',
    label: 'Workspace',
    description: 'Chat + editors',
    icon: (
      <svg
        viewBox="0 0 24 24"
        fill="currentColor"
        className="h-5 w-5"
      >
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
      </svg>
    )
  },
  {
    href: '/runs',
    label: 'Runs',
    description: 'History & logs',
    icon: (
      <svg
        viewBox="0 0 24 24"
        fill="currentColor"
        className="h-5 w-5"
      >
        <path d="M13 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V9l-7-7zM6 20V4h6v5h5v11H6z" />
        <path d="M8 12h8v2H8zm0 4h8v2H8zm0-8h3v2H8z" />
      </svg>
    )
  }
];

export function Sidebar() {
  const pathname = usePathname();
  const sidebarOpen = useUiStore((state) => state.sidebarOpen);
  const sidebarCollapsed = useUiStore((state) => state.sidebarCollapsed);
  const toggleSidebar = useUiStore((state) => state.toggleSidebar);
  const toggleSidebarCollapsed = useUiStore((state) => state.toggleSidebarCollapsed);

  return (
    <>
      <div
        className={`fixed inset-0 z-30 bg-slate-950/40 transition-opacity lg:hidden ${sidebarOpen ? 'opacity-100' : 'pointer-events-none opacity-0'
          }`}
        onClick={toggleSidebar}
        aria-hidden="true"
      />
      <aside
        className={`fixed left-0 top-0 z-40 flex h-full flex-col gap-6 border-r border-arc-gray-200/50 bg-white pb-6 pt-24 transition-all duration-300 dark:border-arc-gray-800/50 dark:bg-night lg:static lg:h-auto lg:translate-x-0 lg:border-none lg:bg-transparent lg:pt-6 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          } ${sidebarCollapsed ? 'w-20 px-3' : 'w-72 px-6'}`}
      >
        <div className="flex items-center justify-between border-b border-arc-gray-100 pb-4 dark:border-arc-gray-800">
          {!sidebarCollapsed && (
            <span className="text-[10px] font-bold uppercase tracking-widest text-arc-gray-400">Navigation</span>
          )}
          <button
            type="button"
            onClick={toggleSidebarCollapsed}
            className={`flex h-8 w-8 items-center justify-center rounded-lg border border-arc-gray-200/50 bg-white/50 text-arc-gray-400 transition-all hover:bg-white hover:text-arc-blue dark:border-arc-gray-700/50 dark:bg-night/50 ${sidebarCollapsed ? 'mx-auto' : ''}`}
            aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <svg
              className={`h-4 w-4 transition-transform duration-300 ${sidebarCollapsed ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        </div>

        <div className="space-y-2">
          {navItems.map((item) => {
            const isActive = pathname?.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`group flex items-center gap-4 rounded-2xl border transition-all ${sidebarCollapsed ? 'justify-center p-2' : 'px-4 py-3.5'
                  } ${isActive
                    ? 'border-arc-blue/20 bg-arc-blue/5 text-arc-blue shadow-sm'
                    : 'border-transparent text-arc-gray-600 hover:bg-arc-gray-50 dark:text-arc-gray-400 dark:hover:bg-arc-gray-900/50'
                  }`}
                title={sidebarCollapsed ? item.label : ''}
              >
                <div
                  className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-all ${isActive
                    ? 'bg-arc-blue text-white shadow-lg shadow-arc-blue/30 scale-105'
                    : 'bg-arc-gray-100/50 text-arc-gray-500 group-hover:bg-arc-gray-200 dark:bg-arc-gray-800/50 dark:text-arc-gray-400'
                    }`}
                >
                  {item.icon}
                </div>
                {!sidebarCollapsed && (
                  <div className="overflow-hidden whitespace-nowrap">
                    <span className={`block text-sm font-bold ${isActive ? 'text-arc-night dark:text-white' : ''}`}>
                      {item.label}
                    </span>
                    <span className="block text-[11px] font-medium text-arc-gray-400 dark:text-arc-gray-500">
                      {item.description}
                    </span>
                  </div>
                )}
              </Link>
            );
          })}
        </div>

        <div className={`mt-auto transition-all duration-300 ${sidebarCollapsed ? 'opacity-0 scale-90' : 'opacity-100 scale-100'}`}>
          {!sidebarCollapsed && (
            <div className="overflow-hidden rounded-2xl border border-arc-gray-200/50 bg-arctic/50 p-5 dark:border-arc-gray-800/50 dark:bg-night/50">
              <div className="flex items-center gap-3 mb-3">
                <div className="h-8 w-8 rounded-lg bg-arc-blue p-1.5 shadow-sm">
                  <img src="/arc-logo-white.png" alt="Arc" className="h-full w-full object-contain" />
                </div>
                <div>
                  <p className="text-xs font-bold text-arc-night dark:text-white leading-tight">Arc Institute</p>
                  <p className="text-[10px] font-semibold text-arc-blue uppercase tracking-wider">v1.2.4</p>
                </div>
              </div>
              <p className="text-[11px] font-medium leading-relaxed text-arc-gray-500 dark:text-arc-gray-400">
                Computational Biology Platform
                <br />
                Next-gen pipeline orchestrator.
              </p>
            </div>
          )}
        </div>

      </aside>
    </>
  );
}
