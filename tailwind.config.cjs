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
          DEFAULT: '#6366F1', // Modern indigo
          dark: '#4F46E5',
          light: '#818CF8',
          50: '#EEF2FF',
          100: '#E0E7FF',
          600: '#4F46E5',
          700: '#4338CA',
        },
        secondary: {
          DEFAULT: '#EC4899', // Modern pink
          dark: '#DB2777',
          light: '#F472B6',
          50: '#FDF2F8',
          100: '#FCE7F3',
        },
        accent: {
          DEFAULT: '#10B981', // Emerald for success states
          dark: '#059669',
          light: '#34D399',
        },
        background: '#F8FAFC', // Cooler, modern slate background
        surface: '#FFFFFF',
        text: {
          primary: '#0F172A',
          secondary: '#64748B',
          tertiary: '#94A3B8',
        },
        border: '#E2E8F0',
        error: '#EF4444',
        success: '#10B981',
        warning: '#F59E0B',
        info: '#3B82F6',
      },
      fontFamily: {
        sans: ['Noto Sans', 'Inter', 'system-ui', 'sans-serif']
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
        'gradient-secondary': 'linear-gradient(135deg, #F093FB 0%, #F5576C 100%)',
        'gradient-accent': 'linear-gradient(135deg, #4FD1C5 0%, #81E6D9 100%)',
        'gradient-hero': 'linear-gradient(135deg, #667EEA 0%, #764BA2 50%, #F093FB 100%)',
      },
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        'medium': '0 4px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 30px -5px rgba(0, 0, 0, 0.04)',
        'large': '0 10px 40px -10px rgba(0, 0, 0, 0.15), 0 20px 50px -10px rgba(0, 0, 0, 0.1)',
        'glow': '0 0 20px rgba(99, 102, 241, 0.3)',
        'glow-lg': '0 0 40px rgba(99, 102, 241, 0.4)',
      },
    },
  },
  plugins: [],
}
