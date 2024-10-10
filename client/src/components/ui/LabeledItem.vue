<script setup lang="ts">
import { type UiStyle, DEFAULT_STYLE } from '@/utils/ui_style'

const props = withDefaults(
  defineProps<{
    label: string
    uiStyle?: UiStyle
  }>(),
  {
    uiStyle: () => DEFAULT_STYLE
  }
)
</script>

<template>
  <div class="inline-flex flex-col gap-2">
    <span :class="props.uiStyle.labelClasses">
      {{ props.label }}
    </span>
    <span :class="props.uiStyle.textClasses">
      <slot></slot>
    </span>
  </div>
</template>
