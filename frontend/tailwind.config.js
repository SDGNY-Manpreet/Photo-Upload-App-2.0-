/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#fafceb',
          100: '#f3facc',
          200: '#e5f59c',
          300: '#d0ed63',
          400: '#b2df31',
          500: '#A3FF1A',
          600: '#8ae60c',
          700: '#6eb30b',
          800: '#54870d',
          900: '#436b0f',
          950: '#233d04',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
