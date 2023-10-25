import { createApp } from 'vue'
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
import CascadeSelect from 'primevue/cascadeselect'
import MultiSelect from 'primevue/multiselect'
import SelectButton from 'primevue/selectbutton'
import RadioButton from 'primevue/radiobutton'
import AutoComplete from 'primevue/autocomplete'
import Slider from 'primevue/slider'
import DataTable from 'primevue/datatable'
import Accordion from 'primevue/accordion'
import AccordionTab from 'primevue/accordiontab'
import InputMask from 'primevue/inputmask'

// check if we need this
import Column from 'primevue/column'
// layout components
import DefaultLayout from '@/components/layout/DefaultLayout.vue'
import SectionLayout from '@/components/layout/SectionLayout.vue'
import Toast from 'primevue/toast'
import ToastService from 'primevue/toastservice'

// to clean for CRUD table
import FileUpload from 'primevue/fileupload'
import Toolbar from 'primevue/toolbar'
import Rating from 'primevue/rating'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import Dialog from 'primevue/dialog'
import Tailwind from 'primevue/passthrough/tailwind'
const app = createApp(App)
// app.use(createPinia())
app.use(router)
app.use(PrimeVue, { ripple: true, unstyled: true, pt: Tailwind, ptOptions: { mergeProps: true } })
app.use(ToastService)
app.component('DefaultLayout', DefaultLayout)
app.component('SectionLayout', SectionLayout)
app.component('MultiSelect', MultiSelect)
app.component('TreeSelect', TreeSelect)
app.component('CascadeSelect', CascadeSelect)
app.component('SelectButton', SelectButton)
app.component('RadioButton', RadioButton)
app.component('Dropdown', Dropdown)
app.component('Divider', Divider)
app.component('InputText', InputText)
app.component('Button', Button)
app.component('AutoComplete', AutoComplete)
app.component('Slider', Slider)
app.component('DataTable', DataTable)
app.component('Column', Column)

app.component('FileUpload', FileUpload)
app.component('Toolbar', Toolbar)
app.component('Rating', Rating)
app.component('Tag', Tag)
app.component('Textarea', Textarea)
app.component('InputNumber', InputNumber)
app.component('Dialog', Dialog)
app.component('Accordion', Accordion)
app.component('AccordionTab', AccordionTab)
app.component('InputMask', InputMask)

app.mount('#app')
