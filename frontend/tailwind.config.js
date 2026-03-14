/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx}'
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"Work Sans"', 'sans-serif']
      },
      colors: {
        ink: {
          900: '#0d1117',
          800: '#1a2230',
          700: '#232f42'
        },
        mist: '#e9eef5',
        glow: '#dff5ff',
        coral: '#ff7a59',
        mint: '#25d0a6'
      },
      boxShadow: {
        glass: '0 12px 40px rgba(7, 12, 22, 0.35)'
      }
    }
  },
  plugins: []
}
