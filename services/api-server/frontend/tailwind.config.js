/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1E3A5F',
          50:  '#EEF3F9',
          100: '#D5E2F0',
          200: '#ACC5E1',
          300: '#82A8D2',
          400: '#598BC3',
          500: '#3B82F6',
          600: '#2C6FD4',
          700: '#1E3A5F',
          800: '#162B47',
          900: '#0E1C2F',
        },
        secondary: '#3B82F6',
        accent:    '#8B5CF6',
        success:   '#10B981',
        warning:   '#F59E0B',
        danger:    '#EF4444',
        surface:   '#FFFFFF',
        background:'#FAFBFD',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card:  '8px',
        btn:   '6px',
        modal: '12px',
      },
      boxShadow: {
        card:       '0 1px 3px rgba(0,0,0,0.08)',
        'card-hover':'0 4px 12px rgba(0,0,0,0.12)',
      },
    },
  },
  plugins: [],
}
