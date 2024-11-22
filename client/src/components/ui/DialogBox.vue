<script setup lang="ts">
import { useDialogState } from '@/stores/DialogState.js'
import { type UiStyle, DEFAULT_STYLE } from '@/utils/ui_style'
import FormErrorMessage from '@/components/ui/FormErrorMessage.vue'

const props = withDefaults(
  defineProps<{
    uiStyle: UiStyle
  }>(),
  {
    uiStyle: () => DEFAULT_STYLE
  }
)

const dialogState = useDialogState()

const style = props.uiStyle.backgroundStyle
</script>
<template>
  <div class="flex flex-col px-8 py-8 gap-4 min-w-[30em]" :style="style">
    <FormErrorMessage :ui-style="uiStyle">{{ dialogState.message }}</FormErrorMessage>
    <slot></slot>
  </div>
</template>
