<script setup lang="ts">
import { useId } from 'vue'
import FormFieldWrapper from '@/components/ui/FormFieldWrapper.vue'
import TempFileUploader, { type TmpUploadExtraProps } from '@/components/ui/TempFileUploader.vue'
import { type FormFieldProps, FORM_FIELD_DEFAULTS } from '@/utils/ui_style'

interface Props extends FormFieldProps, TmpUploadExtraProps {
  label: string
}

const props = withDefaults(defineProps<Props>(), FORM_FIELD_DEFAULTS)
const extraProps: TmpUploadExtraProps = { ...props }

const fileName = defineModel<string>('fileName')
const fileId = defineModel<string>('fileId')

defineEmits<{
  (e: 'change', fileName: string, fileId: string): void
}>()

const id = useId()
</script>
<template>
  <FormFieldWrapper :field-id="id" :error="error" :ui-style="uiStyle">
    <template v-slot:label>{{ label }}</template>
    <template v-slot:field>
      <TempFileUploader
        v-model:fileName="fileName"
        v-model:file-id="fileId"
        v-bind="extraProps"
        :id="id"
        :markAsError="!!error"
        :ui-style="uiStyle"
        @change="(n, i) => $emit('change', n, i)"
      />
    </template>
  </FormFieldWrapper>
</template>
