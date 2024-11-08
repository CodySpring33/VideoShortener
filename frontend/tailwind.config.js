/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",  // Scan all files in src directory
    "./app/**/*.{js,ts,jsx,tsx,mdx}",  // Scan all files in app directory (if using app router)
    "./pages/**/*.{js,ts,jsx,tsx,mdx}", // Scan all files in pages directory (if using pages router)
    "./components/**/*.{js,ts,jsx,tsx,mdx}", // Scan all files in components directory
  ],
  theme: {
    extend: {},
  },
  plugins: [],
} 