<script setup>
import { ref, computed, onMounted, defineAsyncComponent } from 'vue'
import { useDialog } from 'primevue/usedialog'
import { useForm, useFieldArray } from 'vee-validate'
import { object, array, string, number } from 'yup'
import { HTTP } from '@/services/API'
import { toTree, toCascade, nestedSort } from '@/utils/index.js'
import {
  updOrganismFromMod,
  updTechnologyFromModAndOrg,
  updSelectionFromAll
} from '@/utils/selection.js'

import FormDropdown from '@/components/ui/FormDropdown.vue'
import FormMultiSelect from '@/components/ui/FormMultiSelect.vue'
import FormCascade from '@/components/ui/FormCascade.vue'
import FormTextInput from '@/components/ui/FormTextInput.vue'
import FormTextArea from '@/components/ui/FormTextArea.vue'
import FormButton from '@/components/ui/FormButton.vue'

// TODO define in BE
const rna = ref([
  { id: 'mRNA', label: 'mRNA' },
  { id: 'rRNA', label: 'rRNA' }
])
const options = ref([])
const modification = ref([])
const organism = ref([])
const technology = ref([])
const assembly = ref([])

const ProjectList = defineAsyncComponent(() => import('@/components/project/ProjectList.vue'))
const dialog = useDialog()
const showProjects = () => {
  const dialogRef = dialog.open(ProjectList, {
    props: {
      header: 'Available projects',
      breakpoints: {
        '960px': '75vw',
        '640px': '90vw'
      },
      pt: {
        root: { class: 'w-fit' },
        closeButton: { class: 'focus:ring-secondary-400 dark:focus:ring-secondary-300' }
      },
      ptOptions: { mergeProps: true },
      modal: true
    },
    onClose: (options) => {
      const data = options.data
      if (data) {
        const buttonType = data.buttonType
        const summary_and_detail = buttonType
          ? { summary: 'No Product Selected', detail: `Pressed '${buttonType}' button` }
          : { summary: 'Product Selected', detail: data.name }
        smid.value = data.id
      }
    }
  })
}

const validationSchema = object({
  smid: string().max(8, 'At most 8 characters allowed!').required('SMID is required!'),
  rna_type: string().max(32, 'At most 32 characters allowed!').required('RNA type is required!'),
  modification_id: array()
    .of(
      number()
        .integer()
        .typeError('Modification ID must be a number!')
        .transform((_, val) => (val !== '' ? Number(val) : null))
    )
    .required('Modification is required!')
    .min(1, 'Modification is required!'),
  organism_id: number()
    .integer()
    .required('Organism is required!')
    .typeError('Organism ID must be a number!')
    .transform((_, val) => (val !== '' ? Number(val) : null)),
  assembly_id: number()
    .integer()
    .required('Assembly is required!')
    .typeError('Assembly ID must be a number!')
    .transform((_, val) => (val !== '' ? Number(val) : null)),
  technology_id: number()
    .integer()
    .required('Technology is required!')
    .typeError('Technology ID must be a number!')
    .transform((_, val) => (val !== '' ? Number(val) : null)),
  title: string().required('Title is required!').max(255, 'At most 255 characters allowed!')
})

const { defineField, handleSubmit, errors } = useForm({
  validationSchema: validationSchema
})
/* const { remove, push, fields } = useFieldArray('metadata') */

const [smid, smidProps] = defineField('smid')
const [rna_type, rnaProps] = defineField('rna_type')
const [modification_id, modificationProps] = defineField('modification_id')
const [organism_id, organismProps] = defineField('organism_id')
const [assembly_id, assemblyProps] = defineField('assembly_id')
const [technology_id, technologyProps] = defineField('technology_id')
const [title, titleProps] = defineField('title')

const onSubmit = handleSubmit((values) => {
  console.log('SUBMIT', values)
})

const pick = (obj, keys) =>
  Object.keys(obj)
    .filter((k) => keys.includes(k))
    .reduce((res, k) => Object.assign(res, { [k]: obj[k] }), {})

const updModification = (value) => {
  modification_id.value = undefined
  organism_id.value = undefined
  technology_id.value = undefined
  assembly_id.value = undefined
  let opts = options.value
    .filter((item) => item.rna == value)
    .map((obj) => pick(obj, ['modomics_sname', 'modification_id']))
  modification.value = [...new Map(opts.map((item) => [item.modification_id, item])).values()]
}

const updOrganism = (value) => {
  organism.value = []
  organism_id.value = undefined
  technology_id.value = undefined
  assembly_id.value = undefined
  if (value.length > 0) {
    organism.value = updOrganismFromMod(options.value, value)
  }
}

const updTechnology = (value) => {
  technology.value = []
  technology_id.value = undefined
  technology.value = updTechnologyFromModAndOrg(options.value, modification_id.value, {
    key: value
  })
}

const getAssemblies = (value) => {
  assembly.value = []
  assembly_id.value = undefined
  let taxid = options.value
    .filter((item) => item.organism_id == value)
    .map((obj) => pick(obj, ['taxa_id']))[0].taxa_id
  HTTP.get(`/assembly/${taxid}`)
    .then(function (response) {
      assembly.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
}

onMounted(() => {
  HTTP.get('/selection')
    .then(function (response) {
      options.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
})
</script>

<template>
  <div>
    <form @submit.prevent="onSubmit">
      <h3 class="mt-0 mb-4 dark:text-white/80">
        Fill the submission form for each dataset (bedRMod file) that belongs to this project. For
        more information on the bedRMod format, consult the
        <RouterLink
          :to="{ name: 'documentation' }"
          target="_blank"
          class="inline-flex items-center font-semibold text-primary-500 hover:text-secondary-500"
          >Documentation.
        </RouterLink>
        After completion, click <span class="inline font-semibold">"Submit"</span> to finalise the
        submission. You cannot go back after this step.
      </h3>
      <div class="grid grid-cols-2 gap-y-2 gap-x-8">
        <div class="flex flex-row">
          <FormTextInput v-model="smid" :error="errors.smid" placeholder="XXXXXXXX"
            >Sci-ModoM ID (SMID)
          </FormTextInput>
          <Button
            class="ml-4 self-center"
            label="Select a project"
            icon="pi pi-search-plus"
            @click="showProjects"
          />
          <DynamicDialog />
        </div>
        <div />
        <FormDropdown
          v-model="rna_type"
          :options="rna"
          @change="updModification($event)"
          optionValue="id"
          :error="errors.rna_type"
          placeholder="Select RNA type"
          >RNA type
        </FormDropdown>
        <FormMultiSelect
          v-model="modification_id"
          :options="modification"
          @change="updOrganism($event)"
          optionLabel="modomics_sname"
          optionValue="modification_id"
          :error="errors.modification_id"
          placeholder="Select modification"
          >Modification
        </FormMultiSelect>
        <FormCascade
          v-model="organism_id"
          :options="organism"
          @change="updTechnology($event), getAssemblies($event)"
          :optionGroupChildren="['child1', 'child2']"
          optionValue="key"
          :error="errors.organism_id"
          placeholder="Select organism"
          >Organism
        </FormCascade>
        <FormDropdown
          v-model="assembly_id"
          :options="assembly"
          optionLabel="name"
          optionValue="id"
          :error="errors.assembly_id"
          placeholder="Select assembly"
          >Assembly
        </FormDropdown>
        <FormCascade
          v-model="technology_id"
          :options="technology"
          :optionGroupChildren="['children']"
          optionValue="key"
          :error="errors.technology_id"
          placeholder="Select technology"
          >Technology
        </FormCascade>
        <FormTextInput
          v-model="title"
          :error="errors.title"
          placeholder="Wild type mouse heart (Tech-seq) treatment X ..."
          >Dataset title
        </FormTextInput>
      </div>
      <br />
      <div class="flex pt-4 justify-left">
        <Button type="submit" label="Submit dataset" />
      </div>
    </form>
  </div>
</template>
