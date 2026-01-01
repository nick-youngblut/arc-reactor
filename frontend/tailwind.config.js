/** @type {import('tailwindcss').Config} */
const { heroui } = require('@heroui/theme');

module.exports = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './hooks/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
    './stores/**/*.{ts,tsx}'
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        arc: {
          blue: '#1d4ed8',
          secondary: '#14b8a6',
          success: '#16a34a',
          warning: '#f59e0b',
          error: '#ef4444',
          info: '#0ea5e9',
          navy: '#0a1e3d',
          slate: '#1f2937',
          mist: '#f2f7fb',
          gray: {
            50: '#f8fafc',
            100: '#f1f5f9',
            200: '#e2e8f0',
            300: '#cbd5e1',
            400: '#94a3b8',
            500: '#64748b',
            600: '#475569',
            700: '#334155',
            800: '#1f2937',
            900: '#0f172a'
          }
        },
        surface: 'rgb(var(--color-surface) / <alpha-value>)',
        base: 'rgb(var(--color-bg) / <alpha-value>)',
        content: 'rgb(var(--color-fg) / <alpha-value>)'
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
  plugins: [heroui(), require('@tailwindcss/forms'), require('@tailwindcss/typography')]
};
