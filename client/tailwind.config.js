/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        flightnavy: '#0A1628',
        flightblue: '#0EA5E9',
      }
    },
  },
  plugins: [],
}
