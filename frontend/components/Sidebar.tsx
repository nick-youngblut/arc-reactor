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
        className={`fixed inset-0 z-30 bg-slate-950/40 transition-opacity lg:hidden ${
          sidebarOpen ? 'opacity-100' : 'pointer-events-none opacity-0'
        }`}
        onClick={toggleSidebar}
        aria-hidden="true"
      />
      <aside
        className={`fixed left-0 top-0 z-40 flex h-full w-72 flex-col gap-6 border-r border-arc-gray-200/70 bg-white px-6 pb-6 pt-24 transition-transform dark:border-arc-gray-800/70 dark:bg-slate-950 lg:static lg:h-auto lg:translate-x-0 lg:border-none lg:bg-transparent lg:pt-6 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="space-y-4">
          {navItems.map((item) => {
            const isActive = pathname?.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`group flex items-center gap-4 rounded-2xl border px-4 py-3 transition ${
                  isActive
                    ? 'border-arc-blue/30 bg-arc-blue/10 text-arc-blue dark:border-arc-blue/50 dark:bg-arc-blue/20'
                    : 'border-transparent text-arc-gray-600 hover:border-arc-gray-200 hover:bg-arc-gray-50 dark:text-arc-gray-200 dark:hover:border-arc-gray-800 dark:hover:bg-arc-gray-900'
                }`}
              >
                <span
                  className={`flex h-9 w-9 items-center justify-center rounded-xl ${
                  isActive
                    ? 'bg-arc-blue text-white'
                    : 'bg-arc-gray-100 text-arc-gray-500 group-hover:bg-arc-gray-200 dark:bg-arc-gray-800 dark:text-arc-gray-200'
                }`}
                >
                  {item.icon}
                </span>
                <span>
                  <span className="block text-sm font-semibold">{item.label}</span>
                  <span className="block text-xs text-arc-gray-500 dark:text-arc-gray-300">
                    {item.description}
                  </span>
                </span>
              </Link>
            );
          })}
        </div>

        <div className="mt-auto rounded-2xl border border-arc-gray-200/70 bg-arc-gray-50/70 p-4 text-xs text-arc-gray-500 dark:border-arc-gray-800/70 dark:bg-slate-900/70 dark:text-arc-gray-300">
          <p className="text-sm font-semibold text-arc-gray-700 dark:text-arc-gray-100">
            Arc Institute
          </p>
          <p className="mt-1">Computational Biology Platform</p>
        </div>
      </aside>
    </>
  );
}
