<script setup>
import { ref, onMounted, defineAsyncComponent } from 'vue'
import { useRouter } from 'vue-router'
import { useDialog } from 'primevue/usedialog'
import { useForm } from 'vee-validate'
import { object, array, string, number } from 'yup'
import { getApiUrl } from '@/services/API.js'
import { HTTP, HTTPSecure } from '@/services/API'
import Instructions from '@/components/ui/Instructions.vue'
import { updOrganismFromMod, updTechnologyFromModAndOrg } from '@/utils/selection.js'

import FormDropdown from '@/components/ui/FormDropdown.vue'
import FormMultiSelect from '@/components/ui/FormMultiSelect.vue'
import FormCascade from '@/components/ui/FormCascade.vue'
import FormTextInput from '@/components/ui/FormTextInput.vue'

const router = useRouter()

const rna = ref([])
const options = ref([])
const modification = ref([])
const organism = ref([])
const technology = ref([])
const assembly = ref([])
const message = ref()

const uploadURL = getApiUrl('transfer/tmp_upload')

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
        smid.value = data.project_id
      }
    }
  })
}

const validationSchema = object({
  smid: string()
    .min(8, 'SMID has 8 characters exactly!')
    .max(8, 'SMID has 8 characters exactly!')
    .required('SMID is required!'),
  filename: string().required('A dataset file is required!'),
  path: string().required('A dataset file path is required!'),
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

const [smid, smidProps] = defineField('smid')
const [filename, filenameProps] = defineField('filename')
const [path, pathProps] = defineField('path')
const [rna_type, rnaProps] = defineField('rna_type')
const [modification_id, modificationProps] = defineField('modification_id')
const [organism_id, organismProps] = defineField('organism_id')
const [assembly_id, assemblyProps] = defineField('assembly_id')
const [technology_id, technologyProps] = defineField('technology_id')
const [title, titleProps] = defineField('title')

const onSubmit = handleSubmit((values) => {
  HTTPSecure.post('/management/dataset', values)
    .then((response) => {
      if (response.status == 200) {
        router.push({ name: 'home' })
      }
    })
    .catch((error) => {
      message.value = error.response.data.message
      console.log(error)
    })
})

const onUpload = (event) => {
  filename.value = event.files[0].name
  // path is "invisible", we could use path, and derive filename from it...
  path.value = event.xhr.response
}

const dropForm = () => {
  router.push({ name: 'home' })
}

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
  organism.value = []
  technology.value = []
  assembly.value = []
}

const updOrganism = (value) => {
  organism.value = []
  technology.value = []
  assembly.value = []
  organism_id.value = undefined
  technology_id.value = undefined
  assembly_id.value = undefined
  if (value.length > 0) {
    organism.value = updOrganismFromMod(options.value, value)
  }
}

const updTechnology = (value) => {
  technology.value = []
  assembly.value = []
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
  HTTP.get('/rna_types')
    .then(function (response) {
      rna.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
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
      <Instructions>
        Fill a submission form for each dataset (bedRMod file) that belongs to this project. For
        more information on the bedRMod format, consult the
        <RouterLink
          :to="{ name: 'documentation' }"
          target="_blank"
          class="inline-flex items-center font-semibold text-primary-500 hover:text-secondary-500"
          >Documentation.
        </RouterLink>
        Click <span class="inline font-semibold">"Upload"</span> to submit the form. You cannot go
        back after this step. Click <span class="inline font-semibold">"Cancel"</span> to drop the
        request. In the latter case, all information that you entered will be lost.
      </Instructions>
      <div class="grid grid-cols-2 gap-y-2 gap-x-8">
        <div class="flex flex-row">
          <FormTextInput v-model="smid" :error="errors.smid" :disabled="true" placeholder="XXXXXXXX"
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
        <div class="flex flex-row">
          <FormTextInput
            v-model="filename"
            :error="errors.filename"
            :disabled="true"
            placeholder="filename.bedrmod"
            class="w-full"
            >Dataset file
          </FormTextInput>
          <div class="ml-4 place-self-center">
            <FileUpload
              mode="basic"
              name="file"
              :url="uploadURL"
              accept="text/plain,.bed,.bedrmod"
              :maxFileSize="50000000"
              :auto="true"
              chooseLabel="Select a file"
              @upload="onUpload($event)"
            >
            </FileUpload>
          </div>
        </div>
        <FormTextInput
          v-model="title"
          :error="errors.title"
          placeholder="Wild type mouse heart (Tech-seq) treatment X ..."
          >Dataset title
        </FormTextInput>
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
        <div />
      </div>
      <div v-if="message" class="flex m-4 justify-center">
        <Message severity="error" :closable="false">{{ message }}</Message>
      </div>
      <div class="flex flow-row justify-center pt-4 gap-4">
        <Button label="Upload" size="large" type="submit" />
        <Button label="Cancel" size="large" severity="danger" @click="dropForm" />
      </div>
    </form>
  </div>
</template>
