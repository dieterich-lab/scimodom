<script setup lang="ts">
import FileUpload, { type FileUploadUploaderEvent } from 'primevue/fileupload'
import { type UiStyle, DEFAULT_STYLE } from '@/utils/ui_style'
import LabeledItem from '@/components/ui/LabeledItem.vue'

const props = withDefaults(
  defineProps<{
    accept?: string
    label?: string
    multiple?: boolean
    uiStyle?: UiStyle
    disabled?: boolean
    placeholder?: string
    handleFile?: (file: File) => void
  }>(),
  {
    accept: 'application/octet-stream,*',
    label: 'Upload ...',
    multiple: false,
    uiStyle: () => DEFAULT_STYLE,
    disabled: false,
    placeholder: 'Either choose or drag and drop ...',
    handleFile: () => {}
  }
)

async function uploader(event: FileUploadUploaderEvent): Promise<void> {
  const rawFiles = event.files
  const files: File[] = Array.isArray(rawFiles) ? rawFiles : [rawFiles]
  return files.forEach((file) => props.handleFile(file))
}
</script>
<template>
  <LabeledItem :label="label" :ui-style="props.uiStyle" class="w-full">
    <FileUpload
      customUpload
      @uploader="uploader"
      :multiple="props.multiple"
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
