/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './hooks/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
    './stores/**/*.{ts,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        arc: {
          navy: '#0a1e3d',
          sky: '#4aa3ff',
          teal: '#1cc2b5',
          slate: '#1f2937',
          mist: '#f2f7fb'
        }
      }
    }
  },
  plugins: [require('@tailwindcss/forms'), require('@tailwindcss/typography')]
};
