<script setup lang="ts">
import Textarea from 'primevue/textarea'
import { type UiStyle, DEFAULT_STYLE } from '@/utils/ui_style'

const model = defineModel<string>()
const props = withDefaults(
  defineProps<{
    error?: string
    rows?: number
    cols?: number
    placeholder?: string
    uiStyle?: UiStyle
  }>(),
  {
    error: '',
    rows: 5,
    cols: 50,
    placeholder: '',
    uiStyle: () => DEFAULT_STYLE
  }
)
</script>

<template>
  <div class="inline-flex flex-col gap-2">
    <label for="field" :class="props.uiStyle.labelClasses">
      <slot></slot>
    </label>
    <Textarea
      id="field"
      v-model="model"
      autoResize
      rows="props.rows"
      cols="props.cols"
      :placeholder="props.placeholder"
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
