<script setup lang="ts">
import { type InputTypeHTMLAttribute } from 'vue'
import InputText, { type InputTextPassThroughOptions } from 'primevue/inputtext'
import { type UiStyle, DEFAULT_STYLE } from '@/utils/UiStyle'

const model = defineModel<string>()
const props = withDefaults(
  defineProps<{
    error: string
    type: InputTypeHTMLAttribute
    disabled: boolean
    placeholder: string
    uiStyle: UiStyle
  }>(),
  {
    error: '',
    type: 'text',
    disabled: false,
    placeholder: '',
    uiStyle: () => DEFAULT_STYLE
  }
)

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
</script>

<template>
  <div class="inline-flex flex-col gap-2">
    <label for="field" :class="props.uiStyle.labelClasses">
      <slot></slot>
    </label>
    <InputText
      id="field"
      v-model="model"
      :type="type"
      :placeholder="props.placeholder"
      :disabled="props.disabled"
      :pt="pt"
      :ptOptions="{ mergeProps: true }"
      :class="error ? props.uiStyle.errorClasses : ''"
    />
    <span class="inline-flex items-baseline">
      <i :class="error ? props.uiStyle.errorIconClasses : ''" />
      <span :class="['pl-1 place-self-center', props.uiStyle.errorTextClasses]"
        >{{ error }}&nbsp;</span
      >
    </span>
  </div>
</template>
