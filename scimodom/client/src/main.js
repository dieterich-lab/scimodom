import {createApp} from 'vue'
// import {createPinia} from 'pinia'

import App from './App.vue'
import router from './router'

import PrimeVue from 'primevue/config'

// global styles
import '@/assets/style/index.css'
// UI components
import 'primevue/resources/themes/tailwind-light/theme.css'
import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css'
import Dropdown from 'primevue/dropdown'
import Divider from 'primevue/divider'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import TreeSelect from 'primevue/treeselect'
import MultiSelect from 'primevue/multiselect'
import SelectButton from 'primevue/selectbutton'
import RadioButton from 'primevue/radiobutton'
// layout components
import DefaultLayout from '@/components/layout/DefaultLayout.vue'
import SectionLayout from '@/components/layout/SectionLayout.vue'

const app = createApp(App)
// app.use(createPinia())
app.use(router)
app.use(PrimeVue)
app.component('DefaultLayout', DefaultLayout)
app.component('SectionLayout', SectionLayout)
app.component('MultiSelect', MultiSelect)
app.component('TreeSelect', TreeSelect)
app.component('SelectButton', SelectButton)
app.component('RadioButton', RadioButton)
app.component('Dropdown', Dropdown)
app.component('Divider', Divider)
app.component('InputText', InputText)
app.component('Button', Button)
app.mount('#app')
