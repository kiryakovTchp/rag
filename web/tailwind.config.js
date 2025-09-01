/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary colors from promoai-landing
        primary: {
          50: 'oklch(92% 0.004 286.32)',
          100: 'oklch(85% 0.008 286.32)',
          500: 'oklch(64% 0.222 41.116)',
          600: 'oklch(58% 0.222 41.116)',
          700: 'oklch(52% 0.222 41.116)',
          900: 'oklch(21% 0.006 285.885)',
        },
        // Secondary and muted colors
        secondary: {
          50: 'oklch(98% 0.002 286.32)',
          100: 'oklch(95% 0.004 286.32)',
          200: 'oklch(90% 0.006 286.32)',
          300: 'oklch(85% 0.008 286.32)',
          400: 'oklch(80% 0.010 286.32)',
          500: 'oklch(75% 0.012 286.32)',
          600: 'oklch(70% 0.014 286.32)',
          700: 'oklch(65% 0.016 286.32)',
          800: 'oklch(60% 0.018 286.32)',
          900: 'oklch(55% 0.020 286.32)',
        },
        muted: {
          50: 'oklch(98% 0.002 286.32)',
          70: 'oklch(44% 0.017 285.786)',
          100: 'oklch(95% 0.004 286.32)',
          200: 'oklch(90% 0.006 286.32)',
          300: 'oklch(85% 0.008 286.32)',
          400: 'oklch(80% 0.010 286.32)',
          500: 'oklch(75% 0.012 286.32)',
          600: 'oklch(70% 0.014 286.32)',
          700: 'oklch(65% 0.016 286.32)',
          800: 'oklch(60% 0.018 286.32)',
          900: 'oklch(55% 0.020 286.32)',
        },
        // Background and foreground
        background: 'oklch(100% 0 0)',
        foreground: 'oklch(21% 0.006 285.885)',
        // Border colors
        border: 'oklch(44% 0.017 285.786)',
        // Success, warning, error colors
        success: {
          50: 'oklch(95% 0.020 120)',
          500: 'oklch(65% 0.150 120)',
          600: 'oklch(60% 0.150 120)',
        },
        warning: {
          50: 'oklch(95% 0.020 60)',
          500: 'oklch(65% 0.150 60)',
          600: 'oklch(60% 0.150 60)',
        },
        error: {
          50: 'oklch(95% 0.020 0)',
          500: 'oklch(65% 0.150 0)',
          600: 'oklch(60% 0.150 0)',
        },
      },
      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
