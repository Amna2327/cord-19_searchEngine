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
          50: '#fef7ff',
          100: '#fceeff',
          200: '#fae5ff',
          300: '#f5ccff',
          400: '#eda5ff',
          500: '#e373ff',
          600: '#d44aff',
          700: '#c029e8',
          800: '#9e1fc0',
          900: '#831d9d',
        },
        pastel: {
          pink: '#FFD6E8',
          purple: '#E8D6FF',
          blue: '#D6E8FF',
          mint: '#D6FFE8',
          peach: '#FFE8D6',
          lavender: '#F0E8FF',
        },
      },
    },
  },
  plugins: [],
}


