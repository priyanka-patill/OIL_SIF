/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#0A2238',
          900: '#123B5D',
          800: '#184D7A',
          700: '#1F5F94',
        },
        primary: {
          DEFAULT: '#1769AA',
          dark: '#123B5D',
          bright: '#2589C7',
        },
        teal: {
          DEFAULT: '#168C8C',
          light: '#E6F4F4',
        },
        safety: {
          green: '#2E8B57',
          yellow: '#E5A11A',
          orange: '#E67E22',
          red: '#D64545',
          blue: '#2589C7',
        },
        app: {
          bg: '#F4F7FA',
          secondary: '#EEF3F7',
          card: '#FFFFFF',
          border: '#D9E2EA',
          text: '#172B3A',
          muted: '#718394',
          subtext: '#526575',
        },
        slate: {
          950: '#F4F7FA',
          900: '#FFFFFF',
          850: '#EEF3F7',
          800: '#FFFFFF',
          700: '#D9E2EA',
          600: '#718394',
          500: '#526575',
          400: '#526575',
          300: '#172B3A',
          200: '#172B3A',
          100: '#172B3A',
          50: '#F4F7FA',
        }
      }
    },
  },
  plugins: [],
}

