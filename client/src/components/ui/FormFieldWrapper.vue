<script setup lang="ts">
import { DEFAULT_STYLE, type FormFieldWrapperProps } from '@/utils/ui_style'

const props = withDefaults(defineProps<FormFieldWrapperProps>(), {
  error: '',
  uiStyle: () => DEFAULT_STYLE
})
</script>
<template>
  <div class="inline-flex flex-col gap-2">
    <label :for="fieldId" :class="props.uiStyle.labelClasses">
      <slot name="label"></slot>
    </label>
    <slot name="field"></slot>
    <span class="inline-flex items-baseline">
      <i :class="error ? props.uiStyle.errorIconClasses : ''" />
      <span :class="['pl-1 place-self-center', props.uiStyle.errorTextClasses]"
        >{{ error }}&nbsp;</span
      >
    </span>
  </div>
</template>
