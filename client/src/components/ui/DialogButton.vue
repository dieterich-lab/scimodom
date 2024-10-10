<script setup lang="ts">
import Button from 'primevue/button'
import { type UiStyle, DEFAULT_STYLE } from '@/utils/ui_style'

const props = withDefaults(
  defineProps<{
    type?: 'button' | 'submit'
    onClick?: () => void
    uiStyle?: UiStyle
  }>(),
  {
    type: 'button',
    uiStyle: () => DEFAULT_STYLE
  }
)
const classes = props.uiStyle.buttonClasses
const severity = props.uiStyle.severity
</script>
<template>
  <Button @click="$emit('onClick')" :type="type" :class="classes" :severity="severity">
    <slot></slot>
  </Button>
</template>
