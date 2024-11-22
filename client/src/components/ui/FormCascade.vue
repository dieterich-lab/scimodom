<script setup lang="ts" generic="T, K extends keyof T">
import { ref, useId, watch } from 'vue'
import { type CascadeSelectProps, type CascadeSelectChangeEvent } from 'primevue/cascadeselect'
import { DEFAULT_STYLE, type FormFieldProps, type FormFieldWrapperProps } from '@/utils/ui_style'
import FormFieldWrapper from '@/components/ui/FormFieldWrapper.vue'
import { type CascadeItem, getOptionsForPrimvueCascadeSelect } from '@/utils/primevue'

interface Props extends CascadeSelectProps, FormFieldProps {
  options: T[]
  optionGroupKeys: K[]
}

const props = withDefaults(defineProps<Props>(), {
  optionGroupLabel: 'label',
  uiStyle: () => DEFAULT_STYLE
})

const model = defineModel<T>()

const emit = defineEmits<{
  (e: 'change', data: T): void
}>()

const cascadeOptions = ref<CascadeItem<T>[]>([])

watch(
  () => props.options,
  () => {
    cascadeOptions.value = getOptionsForPrimvueCascadeSelect(props.options, props.optionGroupKeys)
  }
)

const fieldId = useId()

const optionLabel = String(props.optionGroupKeys[-1])
const optionGroupChildren = props.optionGroupKeys.slice(0, -1).map(() => 'cChildren')
const pt = { root: { class: 'w-full md:w-full' }, sublist: { class: 'w-full sm:w-80' } }
const ptOptions = { mergeProps: true }
const cascadeProps: CascadeSelectProps = {
  ...props,
  optionGroupChildren,
  optionLabel,
  pt,
  ptOptions,
  options: cascadeOptions.value
}
const wrapperProps: FormFieldWrapperProps = { ...props, fieldId: fieldId }

function change(event: CascadeSelectChangeEvent): void {
  emit('change', event.value)
}
</script>

<template>
  <FormFieldWrapper v-bind="wrapperProps">
    <template v-slot:label>
      <slot></slot>
    </template>
    <template v-slot:field>
      <CascadeSelect
        id="field"
        v-model="model"
        v-bind="cascadeProps"
        @change="change"
        :class="error ? props.uiStyle.errorClasses : ''"
      />
    </template>
  </FormFieldWrapper>
</template>
