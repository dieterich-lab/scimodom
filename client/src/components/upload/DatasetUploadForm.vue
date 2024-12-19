<script setup lang="ts">
import { ref } from 'vue'
import Message from 'primevue/message'
import Button from 'primevue/button'
import { useRouter } from 'vue-router'
import { useForm } from 'vee-validate'
import { object, array, string, number } from 'yup'

import { useDialogState } from '@/stores/DialogState'
import InstructionsText from '@/components/ui/InstructionsText.vue'
import FormTextInput from '@/components/ui/FormTextInput.vue'
import FormProjectSelection from '@/components/ui/FormProjectSelection.vue'
import FormTempFileUploader from '@/components/ui/FormTempFileUploader.vue'
import FormRnaTypeSelect from '@/components/ui/FormRnaTypeSelect.vue'
import FormMultiModificationTypeSelection from '@/components/ui/FormMultiModificationTypeSelection.vue'
import FormCtoSelection from '@/components/ui/FormCtoSelection.vue'
import FormAssemblySelect from '@/components/ui/FormAssemblySelect.vue'
import FormTechnologySelection from '@/components/ui/FormTechnologySelection.vue'

import { type Project } from '@/services/project'
import { type ModificationType, type Cto, type Technology } from '@/services/selection'

import { type DatasetPostRequest, postDataset } from '@/services/management'
import { type RnaType } from '@/services/rna_type'
import { type Assembly } from '@/services/assembly'
import { allDatasetsCache } from '@/services/dataset'
import { trashRequestErrors } from '@/services/API'

const MAX_UPLOAD_SIZE = 50 * 1024 * 1024
const dialogState = useDialogState()
const router = useRouter()

const message = ref<string>()
const rnaTypeRef = ref<RnaType>()
const ctoRef = ref<Cto>()
const assemblyRef = ref<Assembly>()
const technologyRef = ref<Technology>()

const loading = ref(false)

const validationSchema = object({
  smid: string()
    .min(8, 'SMID has 8 characters exactly!')
    .max(8, 'SMID has 8 characters exactly!')
    .required('SMID is required!'),
  file_id: string().required('A dataset file is required!'),
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

const { defineField, handleSubmit, errors, resetField } = useForm<DatasetPostRequest>({
  validationSchema: validationSchema
})

const [smid] = defineField('smid')
const [file_id] = defineField('file_id')
const [rna_type] = defineField('rna_type')
const [modification_id] = defineField('modification_id')
const [organism_id] = defineField('organism_id')
const [assembly_id] = defineField('assembly_id')
const [technology_id] = defineField('technology_id')
const [title] = defineField('title')

const modificationTypes = ref<ModificationType[]>([])

const onSubmit = handleSubmit((values: DatasetPostRequest) => {
  message.value = undefined
  loading.value = true
  postDataset(values, dialogState)
    .then(() => {
      allDatasetsCache.getData(true)
      router.push({ name: 'home' })
    })
    .catch((e) => trashRequestErrors(e))
    .finally(() => {
      loading.value = false
    })
})

function selectProject(project: Project) {
  smid.value = project.project_id
}

const dropForm = () => {
  router.push({ name: 'home' })
}

function selectRnaType(rnaType: RnaType) {
  rna_type.value = rnaType.id
  modificationTypes.value = []
  ctoRef.value = undefined
  assemblyRef.value = undefined
  technologyRef.value = undefined
  resetField('modification_id')
  resetField('organism_id')
  resetField('assembly_id')
  resetField('technology_id')
}

function selectModificationTypes(data: ModificationType[]) {
  modification_id.value = data.map((x) => x.modification_id)
  ctoRef.value = undefined
  assemblyRef.value = undefined
  technologyRef.value = undefined
  resetField('organism_id')
  resetField('assembly_id')
  resetField('technology_id')
}

function selectOrganism(data: Cto) {
  ctoRef.value = data
  assemblyRef.value = undefined
  organism_id.value = data.organism_id
  technologyRef.value = undefined
  resetField('assembly_id')
  resetField('technology_id')
}

function selectAssembly(data: Assembly) {
  assembly_id.value = data.id
  technologyRef.value = undefined
  resetField('technology_id')
}

function selectTechnology(data: Technology) {
  technology_id.value = data.technology_id
}
</script>
<template>
  <div>
    <form @submit.prevent="onSubmit">
      <InstructionsText>
        Fill the upload form for each dataset (bedRMod file) that belongs to this project. For more
        information on the bedRMod format, consult the
        <RouterLink
          :to="{ name: 'management-docs' }"
          target="_blank"
          class="inline-flex items-center font-semibold text-primary-500 hover:text-secondary-500"
          >Documentation.
        </RouterLink>
        Click <span class="inline font-semibold">"Upload"</span> to upload. You cannot go back after
        this step. Click <span class="inline font-semibold">"Cancel"</span> to drop the request. In
        the latter case, all information that you entered will be lost.
      </InstructionsText>
      <div class="grid grid-cols-2 gap-y-2 gap-x-8">
        <FormProjectSelection :error="errors.smid" @change="selectProject" />

        <div />

        <FormTempFileUploader
          v-model:file-id="file_id"
          label="Dataset file"
          accept="text/plain,.bed,.bedrmod"
          :error="errors.file_id"
          :maxFileSize="MAX_UPLOAD_SIZE"
        />

        <FormTextInput
          v-model="title"
          :error="errors.title"
          placeholder="Wild type mouse heart (Tech-seq) treatment X ..."
        >
          Dataset title
        </FormTextInput>

        <FormRnaTypeSelect v-model="rnaTypeRef" :error="errors.rna_type" @change="selectRnaType" />

        <FormMultiModificationTypeSelection
          v-model="modificationTypes"
          :rna-type-name="rnaTypeRef?.label"
          :error="errors.modification_id"
          @change="selectModificationTypes"
        />

        <FormCtoSelection
          v-model="ctoRef"
          :modification-ids="modification_id"
          :error="errors.organism_id"
          @change="selectOrganism"
        />

        <FormAssemblySelect
          v-model="assemblyRef"
          :taxa-id="ctoRef?.taxa_id"
          :error="errors.assembly_id"
          @change="selectAssembly"
        />

        <FormTechnologySelection
          v-model="technologyRef"
          :modification-ids="modification_id"
          :organism-id="organism_id"
          :error="errors.technology_id"
          @change="selectTechnology"
        />

        <div />
      </div>
      <div v-if="message" class="flex m-4 justify-center">
        <Message severity="error" :closable="false">{{ message }}</Message>
      </div>
      <div class="flex flow-row justify-center pt-4 gap-4">
        <Button label="Upload" size="large" type="submit" icon="pi pi-sync" :loading="loading" />
        <Button label="Cancel" size="large" severity="danger" @click="dropForm" />
      </div>
      <div class="flex justify-center italic mt-4">
        Do not refresh the page during upload! This may take a few minutes, as we validate,
        annotate, and eventually lift over your data...
      </div>
      <div class="flex justify-center italic">
        You will be redirected to the main page upon successful upload.
      </div>
    </form>
  </div>
</template>
