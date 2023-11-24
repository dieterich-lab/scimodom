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
        crmg: 'rgb(var(--color-crmg) / <alpha-value>)',
        crmgs: {
          25: 'rgb(var(--color-crmg-one) / <alpha-value>)',
          50: 'rgb(var(--color-crmg-two) / <alpha-value>)',
          75: 'rgb(var(--color-crmg-three) / <alpha-value>)',
          100: 'rgb(var(--color-crmg-four) / <alpha-value>)'
        },
        crmb: 'rgb(var(--color-crmb) / <alpha-value>)',
        crmbs: {
          25: 'rgb(var(--color-crmb-one) / <alpha-value>)',
          50: 'rgb(var(--color-crmb-two) / <alpha-value>)',
          75: 'rgb(var(--color-crmb-three) / <alpha-value>)',
          100: 'rgb(var(--color-crmb-four) / <alpha-value>)'
        }
      },
      fontFamily: {
        ham: ["'ham'"]
      }
    }
  },
  plugins: []
}
