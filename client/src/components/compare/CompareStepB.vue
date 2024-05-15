<script setup>
import { ref, watch } from 'vue'
import { HTTP } from '@/services/API.js'
import DatasetSelectionMulti from '@/components/ui/DatasetSelectionMulti.vue'

const emit = defineEmits(['datasetUploaded'])
const model = defineModel()
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

const remainingDatasets = ref()
const disabled = ref(false)
const uploadURL = HTTP.getUri() + '/upload'
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

const onUpload = (event) => {
  disabled.value = true
  model.value = []
  uploadedFile.value = event.xhr.response
  emit('datasetUploaded', uploadedFile.value)
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
      placeholder="filename.bedrmod"
      class="col-span-2 w-full"
      >Dataset file
    </InputText>
    <div class="flex flex-row">
      <FileUpload
        mode="basic"
        name="file"
        :url="uploadURL"
        accept="text/plain,.bed,.bedrmod"
        :maxFileSize="50000000"
        :auto="true"
        chooseLabel="Select a file (bedRMod)"
        @upload="onUpload($event)"
      >
      </FileUpload>
      <Button
        label="Clear selection"
        @click="clear"
        icon="pi pi-times"
        severity="danger"
        class="ml-4 max-h-[1.9rem] place-self-center"
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
