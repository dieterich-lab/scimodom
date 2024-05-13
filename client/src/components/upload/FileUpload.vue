<script setup>
import FileUpload from 'primevue/fileupload'
import AbstractStyle from '@/ui_styles/AbstractStyle'
import DefaultStyle from '@/ui_styles/DefaultStyle'
import LabeledItem from '@/components/ui/LabeledItem.vue'

const props = defineProps({
  accept: {
    type: String,
    required: false,
    default: 'application/octet-stream,*'
  },
  label: {
    type: String,
    required: false,
    default: 'Upload ...'
  },
  multiple: {
    type: Boolean,
    required: false,
    default: false
  },
  uiStyle: {
    type: AbstractStyle,
    required: false,
    default: DefaultStyle
  },
  disabled: {
    type: Boolean,
    required: false,
    default: false
  },
  placeholder: {
    type: String,
    required: false,
    default: 'Either choose or drag and drop ...'
  },
  handleFile: {
    type: Function,
    required: false,
    default: (_file) => {}
  }
})

const MAX_FILE_SIZE = 1024 * 1024 * 1024

async function uploader(event) {
  return await event.files.forEach((file) => props.handleFile(file))
}
</script>
<template>
  <LabeledItem :label="label" :ui-style="props.uiStyle" class="w-full">
    <FileUpload
      customUpload
      name="files[]"
      url="/api/upload"
      @uploader="uploader"
      :multiple="props.multiple"
      :maxFileSize="MAX_FILE_SIZE"
      :accept="props.accept"
      :disabled="props.disabled"
      :auto="true"
      :showUploadButton="false"
      :showCancelButton="false"
    >
      <template #empty>
        <p>{{ props.placeholder }}</p>
      </template>
    </FileUpload>
  </LabeledItem>
</template>
