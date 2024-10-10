import { createApp } from 'vue'
import App from '@/App.vue'

// global styles
import '@/assets/style/index.css'
// presets
import PrimeVue from 'primevue/config'
import WindScm from '@/presets/windscm'
import { VueCookieNext } from 'vue-cookie-next'
import { createPinia } from 'pinia'
// UI components
import 'primeicons/primeicons.css'
import ConfirmationService from 'primevue/confirmationservice'
import DialogService from 'primevue/dialogservice'
import Tooltip from 'primevue/tooltip'
// layout components

import ToastService from 'primevue/toastservice'

import router from '@/router'

const app = createApp(App)

// app.use(PrimeVue, { unstyled: true, pt: LaraScm, ripple: true })
app.use(PrimeVue, { unstyled: true, pt: WindScm, ripple: true })

app.use(ToastService)
app.use(ConfirmationService)
app.use(DialogService)
app.use(router)
app.use(VueCookieNext)
app.use(createPinia())

app.directive('tooltip', Tooltip)

app.mount('#app')
