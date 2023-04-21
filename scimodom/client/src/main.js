// global styles
import '@/assets/style/index.css'

// global components
import DefaultLayout from '@/components/layout/DefaultLayout.vue'
import SectionLayout from '@/components/layout/SectionLayout.vue'

import {createApp} from 'vue'
// import {createPinia} from 'pinia'

import App from './App.vue'
import router from './router'

// import PrimeVue from 'primevue/config'
// import 'primevue/resources/themes/tailwind-light/theme.css'
// import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css'

const app = createApp(App)

// app.use(createPinia())
app.use(router)
// app.use(PrimeVue)
app.component('DefaultLayout', DefaultLayout)
app.component('SectionLayout', SectionLayout)
app.mount('#app')
