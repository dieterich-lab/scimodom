<script setup>
import AbstractStyle from '@/ui_styles/AbstractStyle'
import DefaultStyle from '@/ui_styles/DefaultStyle'

const props = defineProps({
  type: {
    required: false,
    default: 'button'
  },
  onClick: {
    type: Function,
    required: false,
    default: () => null
  },
  uiStyle: {
    type: AbstractStyle,
    required: false,
    default: DefaultStyle
  }
})
const classes = props.uiStyle.buttonClasses()
</script>
<template>
  <Button @click="$emit('onClick')" :type="type" :class="classes">
    <slot></slot>
  </Button>
</template>
