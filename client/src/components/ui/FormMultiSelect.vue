<script setup lang="ts" generic="T">
import { useId } from 'vue'
import { type MultiSelectProps } from 'primevue/multiselect'
import { DEFAULT_STYLE, type FormFieldProps, type FormFieldWrapperProps } from '@/utils/ui_style'
import FormFieldWrapper from '@/components/ui/FormFieldWrapper.vue'

interface Props extends MultiSelectProps, FormFieldProps {
  options: T[]
}

const props = withDefaults(defineProps<Props>(), { uiStyle: () => DEFAULT_STYLE })

defineEmits<{
  (e: 'change', data: T[]): void
}>()
const model = defineModel<T>()

const fieldId = useId()

const multiSelectProps: MultiSelectProps = { ...props }
const wrapperProps: FormFieldWrapperProps = { ...props, fieldId }
</script>
<template>
  <FormFieldWrapper v-bind="wrapperProps">
    <template v-slot:label>
      <slot></slot>
    </template>
    <template v-slot:field>
      <MultiSelect
        v-model="model"
        :id="fieldId"
        :class="error ? props.uiStyle.errorClasses : ''"
        v-bind="multiSelectProps"
        @change="$emit('change', $event.value)"
      />
    </template>
  </FormFieldWrapper>
</template>
