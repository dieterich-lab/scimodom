import { createApp } from 'vue'
import App from './App.vue'

import PrimeVue from 'primevue/config'
import Tailwind from 'primevue/passthrough/tailwind'
import { usePassThrough } from 'primevue/passthrough'

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
import RadioButton from 'primevue/radiobutton'
import SelectButton from 'primevue/selectbutton'
import Skeleton from 'primevue/skeleton'
import Steps from 'primevue/steps'
import TabPanel from 'primevue/tabpanel'
import TabView from 'primevue/tabview'
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
          'text-gray-600 border border-crmb',
          {
            'hover:border-crmbs-50 focus:outline-none focus:outline-offset-0 focus:shadow-[0_0_0_0.2rem_rgba(2,176,237,1)]':
              !context.disabled,
            'opacity-60 select-none pointer-events-none cursor-default': context.disabled
          }
        ]
      })
    },
    dialog: {
      closeButton: {
        class: [
          '!text-crmb',
          'hover:text-gray-700 hover:border-transparent hover:bg-crmb/25',
          'focus:outline-none focus:outline-offset-0 focus:shadow-crmb/25' // focus
        ]
      }
    },
    radiobutton: {
      input: ({ props }) => ({
        class: [
          {
            'border-gray-300 bg-white': props.value !== props.modelValue,
            'border-crmg bg-crmg': props.value == props.modelValue
          },
          {
            'hover:border-crmg/25 focus:outline-none focus:outline-offset-0 focus:shadow-crmg/25':
              !props.disabled,
            'cursor-default opacity-60': props.disabled
          }
        ]
      })
    },
    dropdown: {
      root: {
        class: 'hover:border-gray-400 focus:outline-none focus:outline-offset-0 focus:shadow-none'
      },
      item: ({ context }) => ({
        class: [
          {
            'text-gray-700 hover:text-gray-700 hover:!bg-crmg/25':
              !context.focused && !context.selected,
            '!bg-crmg text-gray-700 hover:text-gray-700 hover:bg-crmg':
              context.focused && !context.selected,
            'bg-crmg text-gray-50': context.focused && context.selected,
            'bg-transparent text-gray-800': !context.focused && context.selected
          }
        ]
      })
    },
    multiselect: {
      item: ({ context }) => ({
        class: [
          {
            'text-gray-700 hover:text-gray-700 hover:!bg-crmg/25':
              !context.focused && !context.selected,
            '!bg-crmg/25 text-gray-700 hover:text-gray-700 hover:bg-crmg/25':
              context.focused && !context.selected,
            'bg-transparent !text-gray-700': context.focused && context.selected,
            'bg-transparent !text-gray-800': !context.focused && context.selected
          }
        ]
      }),
      headerCheckbox: ({ context }) => ({
        class: [
          'hover:border-crmg/25 focus:outline-none focus:outline-offset-0 focus:shadow-crmg/25',
          {
            'border-gray-300 bg-white': !context?.selected,
            '!border-crmg/25 !bg-crmg/25': context?.selected
          }
        ]
      }),
      checkbox: ({ context }) => ({
        class: [
          'hover:border-crmg/25 focus:outline-none focus:outline-offset-0 focus:shadow-crmg/25',
          {
            'border-gray-300 bg-white': !context?.selected,
            '!border-crmg/25 !bg-crmg/25': context?.selected
          }
        ]
      }),
      checkboxicon: {
        class: '!text-crmg'
      }
    },
    treeselect: {
      tree: {
        root: { class: 'border-none' },
        container: { class: '-space-y-4' },
        toggler: ({ context }) => ({
          class: [
            'focus:shadow-crmg/25',
            {
              'text-gray-500 hover:bg-crmg/25 hover:!text-crmg': !context.selected
            },
            {
              hidden: context.leaf
            }
          ]
        }),
        checkbox: ({ context, props }) => ({
          class: [
            {
              'border-gray-300 bg-transparent': !context.checked,
              'border-crmg/25 bg-crmg/25 !text-crmg': context.checked
            },
            {
              'hover:border-crmg/25 focus:shadow-crmg/25': !props.disabled
            }
          ]
        }),
        subgroup: { class: 'ml-4' }
      }
    },
    datatable: {
      bodyrow: ({ context }) => ({
        class: [
          context.selected ? 'bg-crmb text-crmb' : 'bg-white text-gray-600',
          context.stripedRows
            ? context.index % 2 === 0
              ? 'bg-white text-gray-600'
              : '!bg-crmb/10 text-gray-600'
            : '',
          'transition duration-200',
          'focus:outline focus:outline-[0.15rem] focus:!outline-crmb focus:outline-offset-[-0.15rem]' // Focus
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
  //   unstyled: true,
  pt: tailoredTailwind,
  ptOptions: { mergeProps: true, mergeSections: true } // twice!
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
app.component('RadioButton', RadioButton)
app.component('SelectButton', SelectButton)
app.component('Skeleton', Skeleton)
app.component('Steps', Steps)
app.component('TabPanel', TabPanel)
app.component('TabView', TabView)
app.component('Toolbar', Toolbar)
app.component('TreeSelect', TreeSelect)

app.component('DefaultLayout', DefaultLayout)
app.component('SectionLayout', SectionLayout)

app.mount('#app')
