<script setup>
const props = defineProps({
  small: {
    type: Boolean,
    required: false,
    default: false
  }
})
</script>

<template>
  <p
    :class="[
      small ? 'text-sm lg:text-base' : 'text-lg lg:text-xl',
      'font-normal text-gray-500 dark:text-surface-400'
    ]"
  >
    <slot></slot>
  </p>
</template>
