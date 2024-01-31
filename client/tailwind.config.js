/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    'index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/primevue/**/*.{vue,js,ts,jsx,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        // alpha value spec? 'rgb(var(--color) / <alpha-value>)'
        'primary-50': 'rgb(var(--primary-50))',
        'primary-100': 'rgb(var(--primary-100))',
        'primary-200': 'rgb(var(--primary-200))',
        'primary-300': 'rgb(var(--primary-300))',
        'primary-400': 'rgb(var(--primary-400))',
        'primary-500': 'rgb(var(--primary-500))',
        'primary-600': 'rgb(var(--primary-600))',
        'primary-700': 'rgb(var(--primary-700))',
        'primary-800': 'rgb(var(--primary-800))',
        'primary-900': 'rgb(var(--primary-900))',
        'primary-950': 'rgb(var(--primary-950))',
        'secondary-50': 'rgb(var(--secondary-50))',
        'secondary-100': 'rgb(var(--secondary-100))',
        'secondary-200': 'rgb(var(--secondary-200))',
        'secondary-300': 'rgb(var(--secondary-300))',
        'secondary-400': 'rgb(var(--secondary-400))',
        'secondary-500': 'rgb(var(--secondary-500))',
        'secondary-600': 'rgb(var(--secondary-600))',
        'secondary-700': 'rgb(var(--secondary-700))',
        'secondary-800': 'rgb(var(--secondary-800))',
        'secondary-900': 'rgb(var(--secondary-900))',
        'secondary-950': 'rgb(var(--secondary-950))',
        'surface-0': 'rgb(var(--surface-0))',
        'surface-50': 'rgb(var(--surface-50))',
        'surface-100': 'rgb(var(--surface-100))',
        'surface-200': 'rgb(var(--surface-200))',
        'surface-300': 'rgb(var(--surface-300))',
        'surface-400': 'rgb(var(--surface-400))',
        'surface-500': 'rgb(var(--surface-500))',
        'surface-600': 'rgb(var(--surface-600))',
        'surface-700': 'rgb(var(--surface-700))',
        'surface-800': 'rgb(var(--surface-800))',
        'surface-900': 'rgb(var(--surface-900))',
        'surface-950': 'rgb(var(--surface-950))',
        gg: {
          1: 'rgb(var(--gradient-green-1))',
          2: 'rgb(var(--gradient-green-2))',
          3: 'rgb(var(--gradient-green-3))',
          4: 'rgb(var(--gradient-green-4))'
        },
        gb: {
          1: 'rgb(var(--gradient-blue-1))',
          2: 'rgb(var(--gradient-blue-2))',
          3: 'rgb(var(--gradient-blue-3))',
          4: 'rgb(var(--gradient-blue-4))'
        }
      },
      fontFamily: {
        ham: ["'ham'"]
      }
    }
  },
  plugins: []
}
