/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#2E7D32',
          dark: '#1B5E20',
          light: '#4CAF50'
        },
        secondary: {
          DEFAULT: '#FF6F00',
          dark: '#E65100',
          light: '#FF9800'
        },
        background: '#FAFAF7',
        surface: '#FFFFFF',
        text: {
          primary: '#1A1A1A',
          secondary: '#555555'
        },
        border: '#E0E0E0',
        error: '#D32F2F',
        success: '#388E3C',
        warning: '#F57C00'
      },
      fontFamily: {
        sans: ['Noto Sans', 'Inter', 'system-ui', 'sans-serif']
      }
    },
  },
  plugins: [],
}
