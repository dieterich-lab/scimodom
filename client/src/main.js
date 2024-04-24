import { createApp } from 'vue'
import App from './App.vue'

// global styles
import '@/assets/style/index.css'
// presets
import PrimeVue from 'primevue/config'
// import LaraScm from '@/presets/larascm'
import WindScm from '@/presets/windscm'
import VueCookies from 'vue-cookies'
import { createPinia } from 'pinia'
// UI components
import 'primeicons/primeicons.css'
import Button from 'primevue/button'
import CascadeSelect from 'primevue/cascadeselect'
import Column from 'primevue/column'
import ColumnGroup from 'primevue/columngroup'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import DialogService from 'primevue/dialogservice'
import Divider from 'primevue/divider'
import Dropdown from 'primevue/dropdown'
import FileUpload from 'primevue/fileupload'
import DynamicDialog from 'primevue/dynamicdialog'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Menu from 'primevue/menu'
import Message from 'primevue/message'
import MultiSelect from 'primevue/multiselect'
import Panel from 'primevue/panel'
import ProgressSpinner from 'primevue/progressspinner'
import RadioButton from 'primevue/radiobutton'
import Row from 'primevue/row'
import Stepper from 'primevue/stepper'
import StepperPanel from 'primevue/stepperpanel'
import TabPanel from 'primevue/tabpanel'
import TabView from 'primevue/tabview'
import Textarea from 'primevue/textarea'
import TreeSelect from 'primevue/treeselect'
// layout components
import DefaultLayout from '@/components/layout/DefaultLayout.vue'
import SectionLayout from '@/components/layout/SectionLayout.vue'

import ToastService from 'primevue/toastservice'

import router from '@/router'

const app = createApp(App)

// app.use(PrimeVue, { unstyled: true, pt: LaraScm, ripple: true })
app.use(PrimeVue, { unstyled: true, pt: WindScm, ripple: true })

app.use(ToastService)
app.use(DialogService)
app.use(router)
app.use(VueCookies)
app.use(createPinia())

app.component('Button', Button)
app.component('CascadeSelect', CascadeSelect)
app.component('Column', Column)
app.component('ColumnGroup', ColumnGroup)
app.component('DataTable', DataTable)
app.component('Dialog', Dialog)
app.component('Divider', Divider)
app.component('Dropdown', Dropdown)
app.component('DynamicDialog', DynamicDialog)
app.component('FileUpload', FileUpload)
app.component('InputNumber', InputNumber)
app.component('InputText', InputText)
app.component('Menu', Menu)
app.component('Message', Message)
app.component('MultiSelect', MultiSelect)
app.component('Panel', Panel)
app.component('ProgressSpinner', ProgressSpinner)
app.component('RadioButton', RadioButton)
app.component('Row', Row)
app.component('Stepper', Stepper)
app.component('StepperPanel', StepperPanel)
app.component('TabPanel', TabPanel)
app.component('TabView', TabView)
app.component('Textarea', Textarea)
app.component('TreeSelect', TreeSelect)

app.component('DefaultLayout', DefaultLayout)
app.component('SectionLayout', SectionLayout)

app.mount('#app')
