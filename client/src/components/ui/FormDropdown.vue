<script setup lang="ts" generic="T">
import { useId } from 'vue'
import Select, { type SelectProps } from 'primevue/select'
import { DEFAULT_STYLE, type FormFieldProps, type FormFieldWrapperProps } from '@/utils/ui_style'
import FormFieldWrapper from '@/components/ui/FormFieldWrapper.vue'

interface Props extends SelectProps, FormFieldProps {
  options: T[]
}

const props = withDefaults(defineProps<Props>(), { uiStyle: () => DEFAULT_STYLE })

defineEmits<{
  (e: 'change', option: T): void
}>()

const model = defineModel<T>()
const fieldId = useId()
const selectProps: SelectProps = { ...props }
const wrapperProps: FormFieldWrapperProps = { ...props, fieldId }
</script>
<template>
  <FormFieldWrapper v-bind="wrapperProps">
    <template v-slot:label>
      <slot></slot>
    </template>
    <template v-slot:field>
      <Select
        v-bind="selectProps"
        v-model="model"
        :id="fieldId"
        :class="error ? props.uiStyle.errorClasses : ''"
        @change="$emit('change', $event.value)"
      />
    </template>
  </FormFieldWrapper>
</template>
