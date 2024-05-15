<script setup>
import { ref, watch } from 'vue'
import { HTTP } from '@/services/API.js'
import DatasetSelectionMulti from '@/components/ui/DatasetSelectionMulti.vue'

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
  var ext = event.files[0].name.split('.').pop()
  isEUF.value = ext.toLowerCase() == 'bedrmod' ? true : false
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
      placeholder="filename.bed or filename.bedrmod"
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
        chooseLabel="Select a file"
        class="w-[8rem]"
        @upload="onUpload($event)"
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
