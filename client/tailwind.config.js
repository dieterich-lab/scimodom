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
        ctransparent: 'rgb(255 255 255 / <alpha-value>)',
        cselect: 'rgb(2 176 237 / <alpha-value>)',
        cborder: 'rgb(226 236 236 / <alpha-value>)',

        crmapgreen: 'rgb(0 176 81 / <alpha-value>)', // #00b051ff
        crmapblue: 'rgb(2 176 237 / <alpha-value>)', // #02b0edff

        crmapgreen1: 'rgb(114 191 132 / <alpha-value>)', // #72bf84ff
        crmapgreen2: 'rgb(94 156 108 / <alpha-value>)', // #5e9c6cff
        crmapgreen3: 'rgb(73 122 84 / <alpha-value>)', // #497a54ff
        crmapgreen4: 'rgb(42 69 48 / <alpha-value>)', // #2a4530ff

        crmapblue1: 'rgb(139 201 242 / <alpha-value>)', // #8bc9f2ff
        crmapblue2: 'rgb(90 167 231 / <alpha-value>)', // #5aa7e7ff
        crmapblue3: 'rgb(36 135 219 / <alpha-value>)', // #2487dbff
        crmapblue4: 'rgb(0 81 158 / <alpha-value>)' // #00519eff
      },
      fontFamily: {
        ham: ["'ham'"]
      }
    }
  },
  plugins: []
}
