import { createApp } from 'vue'
import App from './App.vue'
import PrimeVue from 'primevue/config'
import { usePassThrough } from 'primevue/passthrough'
import Tailwind from 'primevue/passthrough/tailwind'
import router from './router'

import ToastService from 'primevue/toastservice'

// global styles
import '@/assets/style/index.css'
// UI components
import 'primeicons/primeicons.css'
import Accordion from 'primevue/accordion'
import AccordionTab from 'primevue/accordiontab'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import Divider from 'primevue/divider'
import Dropdown from 'primevue/dropdown'
import FileUpload from 'primevue/fileupload'
import InputText from 'primevue/inputtext'
import MultiSelect from 'primevue/multiselect'
import SelectButton from 'primevue/selectbutton'
import Steps from 'primevue/steps'
import Toolbar from 'primevue/toolbar'
import TreeSelect from 'primevue/treeselect'
// layout components
import DefaultLayout from '@/components/layout/DefaultLayout.vue'
import SectionLayout from '@/components/layout/SectionLayout.vue'

const app = createApp(App)
const tailoredTailwind = usePassThrough(
  Tailwind,
  {
    inputtext: {
      root: (context) => ({
        class: [
          'text-gray-600 border border-crmapblue0',
          {
            'hover:border-crmapblue2 focus:outline-none focus:outline-offset-0 focus:shadow-[0_0_0_0.2rem_rgba(2,176,237,1)]':
              !context.disabled,
            'opacity-60 select-none pointer-events-none cursor-default': context.disabled
          }
        ]
      })
    },
    treeselect: {
      root: { class: 'max-w-[30rem] md:w-full bg-transparent border-cborder' },
      tree: {
        container: 'm-0 p-0 list-none -space-y-2 overflow-auto',
        root: { class: 'border-none' },
        toggler: ({ context }) => ({
          class: [
            'cursor-pointer select-none inline-flex items-center justify-center overflow-hidden relative shrink-0',
            'mr-2 w-8 h-8 border-0 bg-transparent rounded-full transition duration-200',
            'hover:border-transparent focus:outline-none focus:outline-offset-0 focus:shadow-[0_0_0_0.2rem_rgba(114,191,132,1)]',
            {
              'text-gray-500 hover:bg-crmapgreen1 hover:text-gray-800': !context.selected,
              'text-red-600 hover:bg-crmapgreen1': context.selected
            },
            {
              hidden: context.leaf
            }
          ]
        }),
        checkbox: ({ context, props }) => ({
          class: [
            'cursor-pointer inline-flex relative select-none align-bottom',
            'w-6 h-6',
            'flex items-center justify-center',
            'border-2 w-6 h-6 rounded-lg transition-colors duration-200 text-white text-base',
            {
              'border-gray-300 bg-white': !context.checked,
              'border-crmapgreen1 text-white bg-crmapgreen1': context.checked
            },
            {
              'hover:border-crmapgreen1 focus:outline-none focus:outline-offset-0 focus:shadow-[0_0_0_0.2rem_rgba(114,191,132,1)]':
                !props.disabled,
              'cursor-default opacity-60': props.disabled
            }
          ]
        }),
        subgroup: {
          class: ['ml-4 list-none', 'p-0 pl-4']
        }
      }
    },
    datatable: {
      bodyrow: ({ context }) => ({
        class: [
          context.selected ? 'bg-crmapblue0 text-crmapblue0' : 'bg-white text-gray-600',
          context.stripedRows
            ? context.index % 2 === 0
              ? 'bg-white text-gray-600'
              : 'bg-crmapblue0/20 text-gray-600'
            : '',
          'transition duration-200',
          'focus:outline focus:outline-[0.15rem] focus:outline-crmapblue0 focus:outline-offset-[-0.15rem]', // Focus
          {
            'cursor-pointer': context.selectable,
            'hover:bg-gray-300/20 hover:text-gray-600': context.selectable && !context.selected // Hover
          }
        ]
      })
    }
  },
  {
    mergeSections: true,
    mergeProps: true
  }
)

app.use(PrimeVue, {
  ripple: true,
  unstyled: true,
  pt: tailoredTailwind,
  ptOptions: { mergeProps: true, mergeSections: true }
})

app.use(ToastService)
app.use(router)

app.component('Accordion', Accordion)
app.component('AccordionTab', AccordionTab)
app.component('Button', Button)
app.component('Card', Card)
app.component('Column', Column)
app.component('DataTable', DataTable)
app.component('Dialog', Dialog)
app.component('Divider', Divider)
app.component('Dropdown', Dropdown)
app.component('FileUpload', FileUpload)
app.component('InputText', InputText)
app.component('MultiSelect', MultiSelect)
app.component('SelectButton', SelectButton)
app.component('Steps', Steps)
app.component('Toolbar', Toolbar)
app.component('TreeSelect', TreeSelect)

app.component('DefaultLayout', DefaultLayout)
app.component('SectionLayout', SectionLayout)

app.mount('#app')
