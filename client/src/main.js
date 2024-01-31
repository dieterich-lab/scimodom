import { createApp } from 'vue'
import App from './App.vue'

// global styles
import '@/assets/style/index.css'
// presets
import PrimeVue from 'primevue/config'
import LaraScm from '@/presets/larascm'
// UI components
import 'primeicons/primeicons.css'
import Button from 'primevue/button'
import Column from 'primevue/column'
import ColumnGroup from 'primevue/columngroup'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import Divider from 'primevue/divider'
import Dropdown from 'primevue/dropdown'
import FileUpload from 'primevue/fileupload'
import InputText from 'primevue/inputtext'
import MultiSelect from 'primevue/multiselect'
import RadioButton from 'primevue/radiobutton'
import Row from 'primevue/row'
import SelectButton from 'primevue/selectbutton'
import TabPanel from 'primevue/tabpanel'
import TabView from 'primevue/tabview'
import TreeSelect from 'primevue/treeselect'
// layout components
import DefaultLayout from '@/components/layout/DefaultLayout.vue'
import SectionLayout from '@/components/layout/SectionLayout.vue'

import ToastService from 'primevue/toastservice'

import router from '@/router'

const app = createApp(App)

app.use(PrimeVue, { unstyled: true, pt: LaraScm, ripple: true })

app.use(ToastService)
app.use(router)

app.component('Button', Button)
app.component('Column', Column)
app.component('ColumnGroup', ColumnGroup)
app.component('DataTable', DataTable)
app.component('Dialog', Dialog)
app.component('Divider', Divider)
app.component('Dropdown', Dropdown)
app.component('FileUpload', FileUpload)
app.component('InputText', InputText)
app.component('MultiSelect', MultiSelect)
app.component('RadioButton', RadioButton)
app.component('Row', Row)
app.component('SelectButton', SelectButton)
app.component('TabPanel', TabPanel)
app.component('TabView', TabView)
app.component('TreeSelect', TreeSelect)

app.component('DefaultLayout', DefaultLayout)
app.component('SectionLayout', SectionLayout)

app.mount('#app')
