<script setup>
import AbstractStyle from '@/ui_styles/AbstractStyle.js'
import DefaultStyle from '@/ui_styles/DefaultStyle.js'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  uiStyle: {
    type: AbstractStyle,
    required: false,
    default: DefaultStyle
  }
})
</script>

<template>
  <div class="inline-flex flex-col gap-2">
    <span :class="props.uiStyle.labelClasses()">
      {{ props.label }}
    </span>
    <span :class="props.uiStyle.textClasses()">
      <slot></slot>
    </span>
  </div>
</template>
