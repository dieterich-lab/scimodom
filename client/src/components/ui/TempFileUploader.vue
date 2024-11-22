<script setup lang="ts">
import FileUpload from 'primevue/fileupload'
import InputText, { type InputTextPassThroughOptions } from 'primevue/inputtext'
import type { FileUploadUploaderEvent } from 'primevue/fileupload'
import { postTemporaryFile } from '@/services/transfer'
import { useDialogState } from '@/stores/DialogState'
import { GENERIC_FIELD_DEFAULTS, type GenericFieldProps } from '@/utils/ui_style'
import { ref } from 'vue'
import { trashRequestErrors } from '@/services/API'

export interface TmpUploadExtraProps {
  accept: string
  maxFileSize?: number
  placeholder?: string
  chooseLabel?: string
}
interface Props extends GenericFieldProps, TmpUploadExtraProps {}

const props = withDefaults(defineProps<Props>(), {
  ...GENERIC_FIELD_DEFAULTS,
  placeholder: '',
  chooseLabel: 'Select a file'
})

const emits = defineEmits<{
  (e: 'change', fileName: string, fileId: string): void
}>()

const dialogState = useDialogState()

const fileName = defineModel<string>('fileName')
const fileId = defineModel<string>('fileId')

const fileNameRef = ref<string>('') // Why not using the fileName model instead ? Because it does not work.

function uploader(event: FileUploadUploaderEvent) {
  const file = Array.isArray(event.files) ? event.files[0] : event.files
  fileName.value = file.name
  fileNameRef.value = file.name
  postTemporaryFile(file, dialogState)
    .then((data) => {
      fileId.value = data.file_id
      emits('change', file.name, data.file_id)
    })
    .catch((e) => trashRequestErrors(e))
}

const pt: InputTextPassThroughOptions = {
  root: () => ({
    class: [props.uiStyle.inputTextDefaultClasses]
  })
}
</script>
<template>
  <div class="flex flex-row">
    <InputText
      id="field"
      v-model="fileNameRef"
      :placeholder="placeholder"
      :disabled="true"
      class="w-full"
      :pt="pt"
      :ptOptions="{ mergeProps: true }"
      :class="markAsError ? props.uiStyle.errorClasses : ''"
    />
    <div class="ml-4 place-self-center">
      <FileUpload
        mode="basic"
        customUpload
        @uploader="uploader"
        :accept="accept"
        :maxFileSize="maxFileSize"
        :auto="true"
        :chooseLabel="chooseLabel"
      />
    </div>
  </div>
</template>
