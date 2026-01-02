/** @type {import('tailwindcss').Config} */
const { heroui } = require('@heroui/theme');

module.exports = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './hooks/**/*.{ts,tsx}',
    './stores/**/*.{ts,tsx}',
    './node_modules/@heroui/theme/dist/**/*.{js,ts,jsx,tsx}'
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'arc-blue': '#0073E6',
        'arc-night': '#0C2043',
        'arc-arctic': '#F7F9FB',
        'arc-fog': '#F7F8F9',
        'arc-marigold': '#F39A22',
        'arc-clay': '#BD5D32',
        'arc-moss': '#455F29',
        'arc-evergreen': '#197A57',
        'arc-twilight': '#595F89',
        'arc-slate': '#433F45',
        'arc-gray-50': '#F8FAFC',
        'arc-gray-100': '#F1F5F9',
        'arc-gray-200': '#E2E8F0',
        'arc-gray-300': '#CBD5E1',
        'arc-gray-400': '#94A3B8',
        'arc-gray-500': '#64748B',
        'arc-gray-600': '#475569',
        'arc-gray-700': '#334155',
        'arc-gray-800': '#1F2937',
        'arc-gray-900': '#0F172A',
        surface: 'rgb(var(--color-surface) / <alpha-value>)',
        base: 'rgb(var(--color-bg) / <alpha-value>)',
        content: 'rgb(var(--color-fg) / <alpha-value>)',
        panel: 'rgb(var(--color-panel) / <alpha-value>)',
        element: 'rgb(var(--color-element) / <alpha-value>)'
      },
      fontFamily: {
        display: ['"Space Grotesk"', '"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        body: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace']
      },
      spacing: {
        18: '4.5rem',
        22: '5.5rem',
        30: '7.5rem'
      },
      boxShadow: {
        glow: '0 0 30px rgba(29, 78, 216, 0.25)'
      }
    }
  },
  plugins: [heroui()]
};
