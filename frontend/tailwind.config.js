/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#b4c5ff',
          dim: 'rgba(180, 197, 255, 0.15)',
          light: '#90abff',
        },
        secondary: {
          DEFAULT: '#00D4FF',
          light: '#a2e7ff',
          dark: '#00d2fd',
        },
        tertiary: {
          DEFAULT: '#33FF66',
          light: '#4bff6e',
          dark: '#00daf3',
        },
        error: {
          DEFAULT: '#FF3366',
          light: '#ff716c',
          dark: '#FF3B6F',
        },
        warning: '#FFB800',
        surface: {
          DEFAULT: '#0c0e14',
          50: '#11131a',
          100: '#191c1f',
          200: '#1d1f28',
          300: '#23262e',
          400: '#282a2e',
          500: '#323539',
          lowest: '#000000',
        },
        glass: {
          panel: 'rgba(18, 25, 45, 0.75)',
          base: 'rgba(10, 15, 30, 0.6)',
          hover: 'rgba(25, 35, 60, 0.8)',
        },
      },
      fontFamily: {
        display: ['Space Grotesk', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        body: ['Inter', 'sans-serif'],
      },
      fontSize: {
        'display': ['3rem', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        'headline': ['1.5rem', { lineHeight: '1.2', letterSpacing: '0.05em' }],
        'title': ['1rem', { lineHeight: '1.4' }],
        'body': ['0.875rem', { lineHeight: '1.6' }],
        'label': ['0.6875rem', { lineHeight: '1.4', letterSpacing: '0.05em' }],
        'mono-data': ['0.75rem', { lineHeight: '1.4' }],
      },
      backdropBlur: {
        glass: '20px',
        panel: '12px',
      },
      boxShadow: {
        'glow-primary': '0 0 15px rgba(42, 109, 255, 0.4)',
        'glow-secondary': '0 0 15px rgba(0, 212, 255, 0.4)',
        'glow-tertiary': '0 0 15px rgba(51, 255, 102, 0.3)',
        'glow-error': '0 0 15px rgba(255, 51, 102, 0.4)',
        'glow-text-cyan': '0 0 10px rgba(0, 212, 255, 0.5)',
        'glow-text-blue': '0 0 10px rgba(42, 109, 255, 0.5)',
      },
      borderRadius: {
        'none': '0px',
      },
      animation: {
        'pulse-ring': 'pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scanline': 'scanline 8s linear infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'flicker': 'flicker 0.15s infinite',
      },
      keyframes: {
        'pulse-ring': {
          '0%': { transform: 'scale(0.95)', boxShadow: '0 0 0 0 rgba(0, 218, 243, 0.7)' },
          '70%': { transform: 'scale(1)', boxShadow: '0 0 0 6px rgba(0, 218, 243, 0)' },
          '100%': { transform: 'scale(0.95)', boxShadow: '0 0 0 0 rgba(0, 218, 243, 0)' },
        },
        'scanline': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        'glow': {
          '0%': { opacity: '0.5' },
          '100%': { opacity: '1' },
        },
        'flicker': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
      },
    },
  },
  plugins: [],
}
