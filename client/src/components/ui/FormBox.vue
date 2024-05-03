<script setup>
import { useDialogState } from '@/stores/DialogState.js'
import AbstractStyle from '@/ui_styles/AbstractStyle.js'
import DefaultStyle from '@/ui_styles/DefaultStyle.js'
import FormErrorMessage from '@/components/ui/FormErrorMessage.vue'

const props = defineProps({
  uiStyle: {
    type: AbstractStyle,
    required: false,
    default: DefaultStyle
  }
})

const dialogState = useDialogState()

const style = props.uiStyle.backgroundStyle()
</script>
<template>
  <div class="flex flex-col px-8 py-8 gap-4 min-w-[30em]" :style="style">
    <FormErrorMessage>{{ dialogState.message }}</FormErrorMessage>
    <slot></slot>
  </div>
</template>
