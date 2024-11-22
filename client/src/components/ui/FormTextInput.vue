<script setup lang="ts">
import InputText, { type InputTextPassThroughOptions } from 'primevue/inputtext'
import FormFieldWrapper from '@/components/ui/FormFieldWrapper.vue'
import { FORM_FIELD_DEFAULTS, type FormFieldProps } from '@/utils/ui_style'
import { useId } from 'vue'

interface Props extends FormFieldProps {
  type?: 'text' | 'password' | 'date'
  disabled?: boolean
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  ...FORM_FIELD_DEFAULTS,
  type: 'text',
  disabled: false,
  placeholder: ''
})

const model = defineModel<string>()

const emit = defineEmits<{ (e: 'change', text: string): void }>()

// pt style for login and sign in
const pt: InputTextPassThroughOptions = {
  root: ({ parent }) => ({
    class: [
      parent.instance.$name === 'InputGroup'
        ? props.uiStyle.inputTextGroupClasses
        : props.uiStyle.inputTextDefaultClasses
    ]
  })
}

function change(text: string): void {
  emit('change', text)
}

const id = useId()
</script>

<template>
  <FormFieldWrapper :field-id="id" :error="error" :ui-style="uiStyle">
    <template v-slot:label>
      <slot></slot>
    </template>
    <template v-slot:field>
      <InputText
        id="field"
        v-model="model"
        :type="type"
        :placeholder="placeholder"
        :disabled="disabled"
        :pt="pt"
        :ptOptions="{ mergeProps: true }"
        :class="error ? props.uiStyle.errorClasses : ''"
        @update="change"
      />
    </template>
  </FormFieldWrapper>
</template>
