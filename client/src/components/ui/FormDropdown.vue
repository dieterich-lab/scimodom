<script setup lang="ts" generic="T">
import { useId } from 'vue'
import Dropdown, { type DropdownProps } from 'primevue/dropdown'
import { DEFAULT_STYLE, type FormFieldProps, type FormFieldWrapperProps } from '@/utils/ui_style'
import FormFieldWrapper from '@/components/ui/FormFieldWrapper.vue'

interface Props extends DropdownProps, FormFieldProps {
  options: T[]
}

const props = withDefaults(defineProps<Props>(), { uiStyle: () => DEFAULT_STYLE })

defineEmits<{
  (e: 'change', option: T): void
}>()

const model = defineModel<T>()
const fieldId = useId()
const dropdownProps: DropdownProps = { ...props }
const wrapperProps: FormFieldWrapperProps = { ...props, fieldId }
</script>
<template>
  <FormFieldWrapper v-bind="wrapperProps">
    <template v-slot:label>
      <slot></slot>
    </template>
    <template v-slot:field>
      <Dropdown
        v-bind="dropdownProps"
        v-model="model"
        :id="fieldId"
        :class="error ? props.uiStyle.errorClasses : ''"
        @change="$emit('change', $event.value)"
      />
    </template>
  </FormFieldWrapper>
</template>
