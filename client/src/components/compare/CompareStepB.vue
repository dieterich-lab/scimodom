<script setup>
import { ref, watch } from 'vue'
import { HTTPSecure } from '@/services/API.js'
import DatasetSelectionMulti from '@/components/ui/DatasetSelectionMulti.vue'
import { handleRequestWithErrorReporting } from '@/utils/request'
import { useDialogState } from '@/stores/DialogState'

const emit = defineEmits(['datasetUploaded'])
const model = defineModel()
const isEUF = defineModel('isEUF')
const props = defineProps({
  selectedDatasets: {
    type: Array,
    required: true
  },
  datasets: {
    type: Array,
    required: true
  }
})

const MAX_UPLOAD_SIZE = 50 * 1024 * 1024
const dialogState = useDialogState()
const remainingDatasets = ref()
const disabled = ref(false)
const uploadedFile = ref()

watch(
  () => props.selectedDatasets,
  () => {
    model.value = []
    remainingDatasets.value = props.datasets.filter(
      (item) => !props.selectedDatasets.includes(item.dataset_id)
    )
  },
  { immediate: true }
)

function uploader(event) {
  const file = event.files[0]
  console.log(`File: ${typeof file}`)
  handleRequestWithErrorReporting(
    HTTPSecure.post('transfer/tmp_upload', file),
    `Failed to upload '${file.name}'`,
    dialogState
  ).then((data) => {
    disabled.value = true
    model.value = []
    uploadedFile.value = file.name
    let ext = file.name.split('.').pop()
    isEUF.value = ext.toLowerCase() === 'bedrmod'
    emit('datasetUploaded', data.file_id)
  })
}

const clear = () => {
  disabled.value = false
  uploadedFile.value = undefined
  emit('datasetUploaded', undefined)
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
        :maxFileSize="MAX_UPLOAD_SIZE"
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
