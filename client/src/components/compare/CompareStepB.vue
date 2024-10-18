<script setup lang="ts">
import { ref, watch } from 'vue'
import ToggleButton from 'primevue/togglebutton'
import DatasetSelectionMulti from '@/components/ui/DatasetSelectionMulti.vue'
import { useDialogState } from '@/stores/DialogState'
import type { Dataset } from '@/services/dataset'
import type { FileUploadUploaderEvent } from 'primevue/fileupload'
import { uploadTemporaryDataset, type UploadedFile } from '@/services/dataset_upload'

const emit = defineEmits<{
  datasetUploaded: [file: UploadedFile | null]
}>()
const model = defineModel()
const isEUF = defineModel<boolean>('isEUF')
const props = defineProps<{
  selectedDatasets: Dataset[]
  datasets: Dataset[]
}>()

const dialogState = useDialogState()
const remainingDatasets = ref<Dataset[]>([])
const disabled = ref<boolean>(false)
const uploadedFile = ref()

watch(
  () => props.selectedDatasets,
  () => {
    model.value = []
    const selectedDatasetIds = props.selectedDatasets.map((x) => x.dataset_id)
    remainingDatasets.value = props.datasets.filter(
      (d) => !selectedDatasetIds.includes(d.dataset_id)
    )
  },
  { immediate: true }
)

function uploader(event: FileUploadUploaderEvent) {
  const file = Array.isArray(event.files) ? event.files[0] : event.files
  uploadTemporaryDataset(file, dialogState)
    .then((result) => {
      disabled.value = true
      model.value = []
      uploadedFile.value = file.name
      isEUF.value = file.name.toLowerCase().endsWith('.bedrmod')
      emit('datasetUploaded', result)
    })
    .catch(() => clear())
}

function clear() {
  disabled.value = false
  uploadedFile.value = undefined
  emit('datasetUploaded', null)
}
</script>

<template>
  <div class="grid grid-cols-3 gap-6">
    <InputText
      v-model="uploadedFile"
      :disabled="true"
      placeholder="filename.bed or filename.bedrmod"
      class="col-span-2 w-full"
      >Dataset file
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
      <ToggleButton v-model="isEUF" onLabel="bedRMod" offLabel="BED6" class="w-[8rem] ml-4" />
      <Button
        label="Clear selection"
        @click="clear"
        icon="pi pi-times"
        severity="danger"
        class="ml-4 max-h-[1.9rem] place-self-center text-nowrap"
      />
    </div>
    <DatasetSelectionMulti
      v-model="model"
      :datasets="remainingDatasets"
      placeholder="Select dataset"
      :selectionLimit="3"
      :maxSelectedLabels="3"
      :disabled="disabled"
    />
  </div>
</template>
