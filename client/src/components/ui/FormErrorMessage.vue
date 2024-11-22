<script setup lang="ts">
import { type UiStyle, DEFAULT_STYLE } from '@/utils/ui_style'

withDefaults(defineProps<{ uiStyle?: UiStyle }>(), { uiStyle: () => DEFAULT_STYLE })
</script>
<template>
  <p :class="uiStyle.errorTextClasses" style="white-space: pre">
    <slot></slot>
  </p>
</template>
