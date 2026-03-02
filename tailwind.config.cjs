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
          DEFAULT: '#818CF8', // Soft indigo for dark bg
          dark: '#6366F1',
          light: '#A5B4FC',
          50: 'rgba(129, 140, 248, 0.06)',
          100: 'rgba(129, 140, 248, 0.12)',
          600: '#6366F1',
          700: '#4F46E5',
        },
        secondary: {
          DEFAULT: '#F472B6', // Soft pink
          dark: '#EC4899',
          light: '#F9A8D4',
          50: 'rgba(244, 114, 182, 0.06)',
          100: 'rgba(244, 114, 182, 0.12)',
        },
        accent: {
          DEFAULT: '#34D399', // Emerald for success
          dark: '#10B981',
          light: '#6EE7B7',
        },
        background: '#0B0F1A',
        'background-secondary': '#111827',
        surface: {
          DEFAULT: '#1E293B',       // Card backgrounds
          light: '#334155',         // Elevated surfaces
          glass: 'rgba(30, 41, 59, 0.60)', // Glassmorphism
        },
        text: {
          primary: '#F1F5F9',
          secondary: '#94A3B8',
          tertiary: '#64748B',
        },
        border: 'rgba(148, 163, 184, 0.12)',
        'border-light': 'rgba(148, 163, 184, 0.20)',
        error: '#F87171',
        success: '#34D399',
        warning: '#FBBF24',
        info: '#60A5FA',
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans', 'system-ui', 'sans-serif']
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #818CF8 0%, #6366F1 100%)',
        'gradient-secondary': 'linear-gradient(135deg, #F472B6 0%, #EC4899 100%)',
        'gradient-accent': 'linear-gradient(135deg, #34D399 0%, #10B981 100%)',
        'gradient-hero': 'linear-gradient(160deg, #0B0F1A 0%, #1E1B4B 40%, #312E81 70%, #1E1B4B 100%)',
        'gradient-card': 'linear-gradient(135deg, rgba(129, 140, 248, 0.08) 0%, rgba(244, 114, 182, 0.05) 100%)',
        'gradient-glow': 'radial-gradient(600px circle at var(--mouse-x, 50%) var(--mouse-y, 50%), rgba(129, 140, 248, 0.06), transparent 40%)',
        'mesh-gradient': 'radial-gradient(at 27% 37%, #1E1B4B 0px, transparent 50%), radial-gradient(at 97% 21%, #312E81 0px, transparent 50%), radial-gradient(at 52% 99%, #1E1B4B 0px, transparent 50%), radial-gradient(at 10% 29%, rgba(129, 140, 248, 0.15) 0px, transparent 50%)',
      },
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.3), 0 10px 20px -2px rgba(0, 0, 0, 0.2)',
        'medium': '0 4px 25px -5px rgba(0, 0, 0, 0.4), 0 10px 30px -5px rgba(0, 0, 0, 0.3)',
        'large': '0 10px 40px -10px rgba(0, 0, 0, 0.5), 0 20px 50px -10px rgba(0, 0, 0, 0.4)',
        'glow': '0 0 20px rgba(129, 140, 248, 0.25)',
        'glow-lg': '0 0 40px rgba(129, 140, 248, 0.35)',
        'glow-pink': '0 0 30px rgba(244, 114, 182, 0.20)',
        'card': '0 0 0 1px rgba(148, 163, 184, 0.06), 0 8px 32px rgba(0, 0, 0, 0.3)',
        'card-hover': '0 0 0 1px rgba(129, 140, 248, 0.15), 0 16px 48px rgba(0, 0, 0, 0.4), 0 0 24px rgba(129, 140, 248, 0.08)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'gradient-x': 'gradient-x 15s ease infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite alternate',
      },
      keyframes: {
        'gradient-x': {
          '0%, 100%': { 'background-position': '0% 50%' },
          '50%': { 'background-position': '100% 50%' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'glow-pulse': {
          '0%': { opacity: '0.5' },
          '100%': { opacity: '1' },
        },
      },
      backdropBlur: {
        'xs': '2px',
      },
    },
  },
  plugins: [],
}
