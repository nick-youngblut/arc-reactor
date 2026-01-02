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
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        className="h-5 w-5"
      >
        <path d="M4 4h16v12H7l-3 3V4z" />
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
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        className="h-5 w-5"
      >
        <path d="M12 6v12m6-6H6" />
        <circle cx="12" cy="12" r="9" />
      </svg>
    )
  }
];

export function Sidebar() {
  const pathname = usePathname();
  const sidebarOpen = useUiStore((state) => state.sidebarOpen);
  const toggleSidebar = useUiStore((state) => state.toggleSidebar);

  return (
    <>
      <div
        className={`fixed inset-0 z-30 bg-slate-950/40 transition-opacity lg:hidden ${sidebarOpen ? 'opacity-100' : 'pointer-events-none opacity-0'
          }`}
        onClick={toggleSidebar}
        aria-hidden="true"
      />
      <aside
        className={`fixed left-0 top-0 z-40 flex h-full w-72 flex-col gap-8 border-r border-arc-gray-200/50 bg-white px-6 pb-6 pt-24 transition-transform dark:border-arc-gray-800/50 dark:bg-night lg:static lg:h-auto lg:translate-x-0 lg:border-none lg:bg-transparent lg:pt-6 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
      >
        <div className="space-y-2">
          {navItems.map((item) => {
            const isActive = pathname?.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`group flex items-center gap-4 rounded-2xl border px-4 py-3.5 transition-all ${isActive
                    ? 'border-arc-blue/20 bg-arc-blue/5 text-arc-blue shadow-sm'
                    : 'border-transparent text-arc-gray-600 hover:bg-arc-gray-50 dark:text-arc-gray-400 dark:hover:bg-arc-gray-900/50'
                  }`}
              >
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-xl transition-all ${isActive
                      ? 'bg-arc-blue text-white shadow-lg shadow-arc-blue/30 scale-105'
                      : 'bg-arc-gray-100/50 text-arc-gray-500 group-hover:bg-arc-gray-200 dark:bg-arc-gray-800/50 dark:text-arc-gray-400'
                    }`}
                >
                  {item.icon}
                </div>
                <div>
                  <span className={`block text-sm font-bold ${isActive ? 'text-arc-night dark:text-white' : ''}`}>
                    {item.label}
                  </span>
                  <span className="block text-[11px] font-medium text-arc-gray-400 dark:text-arc-gray-500">
                    {item.description}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>

        <div className="mt-auto overflow-hidden rounded-2xl border border-arc-gray-200/50 bg-arctic/50 p-5 dark:border-arc-gray-800/50 dark:bg-night/50">
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
      </aside>
    </>
  );
}
