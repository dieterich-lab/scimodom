<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import ToggleButton from 'primevue/togglebutton'
import InputText from 'primevue/inputtext'
import FileUpload from 'primevue/fileupload'
import Button from 'primevue/button'
import DatasetSelectionMulti from '@/components/ui/DatasetSelectionMulti.vue'
import { useDialogState } from '@/stores/DialogState'
import type { Dataset } from '@/services/dataset'
import type { FileUploadUploaderEvent } from 'primevue/fileupload'
import { uploadTemporaryDataset } from '@/services/dataset_upload'
import { type ResultStepA, type ResultStepB } from '@/utils/comparison'
import { trashRequestErrors } from '@/services/API'

const props = defineProps<{
  resultStepA?: ResultStepA
}>()
const model = defineModel<ResultStepB>()
const emit = defineEmits<{
  (e: 'change', result?: ResultStepB): void
}>()

const dialogState = useDialogState()

const selectedDatasets = ref<Dataset[]>([])
const isEUF = ref<boolean>(false)
const disableDatasetSelection = ref<boolean>(false)
const uploadedFileName = ref<string>('')

const doneWithStepA = computed(() => !!props.resultStepA?.datasets.length)
const datasets = computed(() => (props?.resultStepA ? props.resultStepA.remainingDatasets : []))

function uploader(event: FileUploadUploaderEvent) {
  const file = Array.isArray(event.files) ? event.files[0] : event.files
  uploadedFileName.value = file.name
  uploadTemporaryDataset(file, dialogState)
    .then((uploadedFile) => {
      disableDatasetSelection.value = true
      selectedDatasets.value = []
      isEUF.value = file.name.toLowerCase().endsWith('.bedrmod')
      const result: ResultStepB = {
        ...uploadedFile,
        isEUF: isEUF.value
      }
      model.value = result
      emit('change', result)
    })
    .catch((e) => {
      reset()
      trashRequestErrors(e)
    })
}

function update() {
  if (model.value !== undefined) {
    if ('isEUF' in model.value) {
      const result: ResultStepB = {
        ...model.value,
        isEUF: isEUF.value
      }
      model.value = result
      emit('change', result)
    }
  }
}

function reset() {
  disableDatasetSelection.value = false
  uploadedFileName.value = ''
  selectedDatasets.value = []
  model.value = undefined
  emit('change')
}

function changeDatasets(datasets: Dataset[]) {
  const result: ResultStepB = {
    datasets: datasets
  }
  model.value = result
  emit('change', result)
}

watch(
  () => props.resultStepA,
  () => {
    if (model.value !== undefined) {
      reset()
    }
  }
)
</script>

<template>
  <div v-if="doneWithStepA">
    <div class="mb-4">Select up to three dataset for comparison or upload your own data.</div>
    <div class="grid grid-cols-3 gap-6">
      <InputText
        v-model="uploadedFileName"
        :disabled="true"
        placeholder="filename.bed or filename.bedrmod"
        class="col-span-2 w-full"
      >
        Dataset file
      </InputText>
      <div class="flex flex-row">
        <FileUpload
          mode="basic"
          customUpload
          @uploader="uploader"
          accept="text/plain,.bed,.bedrmod"
          :auto="true"
          chooseLabel="Select a file"
          class="w-[8rem]"
        >
        </FileUpload>
        <ToggleButton
          v-model="isEUF"
          onLabel="bedRMod"
          offLabel="BED6"
          @change="update"
          class="w-[8rem] ml-4"
        />
        <Button
          label="Clear selection"
          @click="reset"
          icon="pi pi-times"
          severity="danger"
          class="ml-4 max-h-[1.9rem] place-self-center text-nowrap"
        />
      </div>
      <DatasetSelectionMulti
        v-model="selectedDatasets"
        :datasets="datasets"
        placeholder="Select dataset"
        :selectionLimit="3"
        :maxSelectedLabels="3"
        :disabled="disableDatasetSelection"
        @change="changeDatasets"
      />
    </div>
  </div>
  <div v-else>
    <div class="mb-4">Select reference dataset in step 1 to continue.</div>
  </div>
</template>
