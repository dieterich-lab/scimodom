<script setup>
import { ref, watch } from 'vue'
import { HTTP } from '@/services/API.js'

const emit = defineEmits(['datasetUploaded'])
const model = defineModel()
const props = defineProps({
  selected: {
    type: Array,
    required: true
  },
  dataset: {
    type: Array,
    required: true
  }
})
const isEUF = ref()
const dataset = ref()
const disabled = ref(false)
const uploadURL = HTTP.getUri() + '/upload'
const uploadedFile = ref()

watch(
  () => props.selected,
  () => {
    model.value = []
    dataset.value = props.dataset.filter((item) => !props.selected.includes(item.dataset_id))
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
      <ToggleButton v-model="isEUF" onLabel="bedRMod" offLabel="BED6" class="w-[8rem] mr-4" />
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
        class="ml-4 max-h-[1.9rem] place-self-center text-nowrap"
      />
    </div>
    <MultiSelect
      v-model="model"
      :options="dataset"
      :disabled="disabled"
      :selectionLimit="3"
      filter
      :filterFields="['dataset_id', 'dataset_title', 'dataset_info']"
      optionValue="dataset_id"
      optionLabel="dataset_id"
      placeholder="Select dataset"
      :maxSelectedLabels="3"
      display="chip"
      :pt="{
        root: { class: 'col-span-2 w-full md:w-full' }
      }"
      :ptOptions="{ mergeProps: true }"
    >
      <template #option="slotProps">
        <div class="flex">
          <div class="pr-2 text-surface-500">{{ slotProps.option.dataset_id }}</div>
          <div class="pr-2 font-semibold">{{ slotProps.option.dataset_title }}</div>
          <div class="italic">{{ slotProps.option.dataset_info }}</div>
        </div>
      </template>
    </MultiSelect>
  </div>
</template>
