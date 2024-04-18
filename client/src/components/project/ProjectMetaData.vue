<script setup>
import { ref, onMounted } from 'vue'
import { useForm, useFieldArray } from 'vee-validate'
import { object, array, string, number, date } from 'yup'
import { HTTPSecure } from '@/services/API'

import { toTree, toCascade, nestedSort, toIds } from '@/utils/index.js'
import { HTTP } from '@/services/API.js'
import {
  updModification,
  updOrganismFromMod,
  updTechnologyFromModAndOrg,
  updSelectionFromAll
} from '@/utils/selection.js'

const modification = ref([])
const method = ref([])
const taxid = ref([])
const assembly = ref([])
const selectedModification = ref()
const selectedMethod = ref()
const selectedTaxid = ref()
const selectedAssembly = ref()

import { useRouter } from 'vue-router'
const router = useRouter()
const routeData = router.resolve({ name: 'documentation' })
const tata = () => {
  window.open(routeData.href, '_blank')
}

// TODO define in BE
const rna = ref([
  { id: 'mRNA', label: 'mRNA' },
  { id: 'rRNA', label: 'rRNA' }
])

import FormDropdown from '@/components/ui/FormDropdown.vue'
import FormCascade from '@/components/ui/FormCascade.vue'

import FormTextInput from '@/components/ui/FormTextInput.vue'
import FormTextArea from '@/components/ui/FormTextArea.vue'
import FormButton from '@/components/ui/FormButton.vue'

const props = defineProps(['nextCallback', 'prevCallback'])
const model = defineModel()

const validationSchema = object({
  metadata: array().of(
    object().shape({
      rna: string().max(32, 'At most 32 characters allowed!').required('RNA type is required!'),
      modification: string()
        .max(128, 'At most 128 characters allowed!')
        .required('Modification is required!'),
      method: string().max(8, 'At most 8 characters allowed').required('Method is required!'),
      technology: string()
        .max(255, 'At most 255 characters allowed!')
        .required('Technology is required!'),
      taxid: number().integer().required('Organism is required!'),
      organism: string()
        .max(255, 'At most 255 characters allowed!')
        .required('Cell, tissue, or organ is required!'),
      assembly: number()
        .integer()
        .typeError('Assembly ID must be a number!')
        .transform((_, val) => (val !== '' ? Number(val) : null)),
      freeAssembly: string()
        .max(128, 'At most 128 characters allowed!')
        .required(
          'Assembly is required! If selecting from existing (left), copy your selection above.'
        ),
      note: string()
    })
  )
})

const initialValues = {
  rna: '',
  modification: '',
  method: '',
  technology: '',
  taxid: null,
  organism: '',
  assembly: null,
  freeAssembly: '',
  note: ''
}

const resetRefs = () => {
  selectedModification.value = undefined
  selectedMethod.value = undefined
  selectedTaxid.value = undefined
  selectedAssembly.value = undefined
}

const getInitialValues = () => {
  // is this used at all? i.e. it's not called on previous/next Stepper navigation
  // resetRefs()
  if (model.value === undefined) {
    return null
  } else {
    return { ...model.value }
  }
}

const { handleSubmit, errors } = useForm({
  validationSchema: validationSchema,
  initialValues: getInitialValues()
})

const { remove, push, fields } = useFieldArray('metadata')

const addMetadata = () => {
  resetRefs()
  push(initialValues)
}

const onSubmit = handleSubmit((values) => {
  // Submit to API
  console.log(values)
  model.value = values
  props.nextCallback()
})

const getAssemblies = () => {
  HTTP.get(`/assembly/${selectedTaxid.value.key}`)
    .then(function (response) {
      assembly.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
}

onMounted(() => {
  HTTP.get('/modification')
    .then(function (response) {
      modification.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
  HTTP.get('/method')
    .then(function (response) {
      method.value = toCascade(toTree(response.data, ['cls', 'meth'], 'id'))
      // console.log(method.value)
      nestedSort(method.value, ['child1'])
      // console.log('2', method.value)
    })
    .catch((error) => {
      console.log(error)
    })
  HTTP.get('/taxid')
    .then(function (response) {
      let opts = response.data
      opts = opts.map((item) => {
        const kingdom = Object.is(item.kingdom, null) ? item.domain : item.kingdom
        return { ...item, kingdom }
      })
      taxid.value = toCascade(toTree(opts, ['kingdom', 'taxa_sname'], 'id'))
      nestedSort(taxid.value, ['child1'])
    })
    .catch((error) => {
      console.log(error)
    })
})
</script>

<template>
  <SectionLayout>
    <div>
      <form @submit.prevent="onSubmit">
        <div class="flex flex-col mx-auto">
          <div class="text-center -mt-4 mb-4 text-xl font-semibold dark:text-white/80">
            Project metadata MODEL VALUE: {{ model }}
          </div>
        </div>
        <h3 class="mt-0 mb-4 dark:text-white/80">
          Click <span class="inline font-semibold">"Add metadata"</span> to add a metadata sheet for
          a dataset. Add a new metadata sheet for each dataset that belongs to this project or for
          each modification associated with a single dataset. Consult the
          <RouterLink
            :to="{ name: 'documentation' }"
            target="_blank"
            class="inline-flex items-center font-semibold text-primary-500 hover:text-secondary-500"
            >Documentation
          </RouterLink>
          for more information and examples.
        </h3>
        <Button @click="addMetadata()" label="Add metadata" class="mt-4 mb-4" />
        <div class="grid grid-cols-2 gap-x-8 mt-4" v-for="(field, idx) in fields" :key="field.key">
          <FormDropdown
            v-model="field.value.rna"
            :options="rna"
            :error="errors[`metadata[${idx}].rna`]"
            placeholder="Select RNA type"
            >RNA type
          </FormDropdown>
          <FormDropdown
            v-model="field.value.modification"
            :options="modification"
            optionsLabel="modomics_sname"
            :error="errors[`metadata[${idx}].modification`]"
            placeholder="Select modification"
            >Modification
          </FormDropdown>
          <FormCascade
            v-model="field.value.method"
            :options="method"
            :error="errors[`metadata[${idx}].method`]"
            placeholder="Select method"
            >Method
          </FormCascade>
          <FormTextInput
            v-model="field.value.technology"
            :error="errors[`metadata[${idx}].technology`]"
            placeholder="Tech-seq"
            >Technology
          </FormTextInput>
          <FormCascade
            v-model="field.value.taxid"
            :options="taxid"
            :error="errors[`metadata[${idx}].taxid`]"
            placeholder="Select organism"
            >Organism
          </FormCascade>
          <FormTextInput
            v-model="field.value.organism"
            :error="errors[`metadata[${idx}].organism`]"
            placeholder="e.g. HeLa, mESC, or Heart"
            >Cell, tissue, organ</FormTextInput
          >
          <FormDropdown
            v-model="field.value.assembly"
            :options="assembly"
            optionsLabel="name"
            :error="errors[`metadata[${idx}].assembly`]"
            placeholder="Select assembly"
            >Assembly (select from existing assemblies)
          </FormDropdown>
          <FormTextInput
            v-model="field.value.freeAssembly"
            :error="errors[`metadata[${idx}].freeAssembly`]"
            placeholder="e.g. NCBI36 (Ensembl release 54)"
            >Assembly (if not available)</FormTextInput
          >
          <FormTextArea
            v-model="field.value.note"
            :error="errors[`metadata[${idx}].note`]"
            placeholder="Tech-seq sources: 10.XXXX/... This metadata template is for published data (PubMed-ID, GEO, ...), etc."
          >
            Additional notes for this metadata template.
          </FormTextArea>
          <div class="place-self-start self-center">
            <Button @click="remove(idx)" label="Remove metadata" />
          </div>
        </div>
        <br />
        <div class="flex pt-4 justify-between">
          <Button label="Back" severity="secondary" icon="pi pi-arrow-left" @click="prevCallback" />
          <Button type="submit" label="Next" icon="pi pi-arrow-right" iconPos="right" />
        </div>
      </form>
    </div>
  </SectionLayout>
</template>
