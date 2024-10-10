<script setup lang="ts">
withDefaults(
  defineProps<{
    small?: boolean
    padding?: boolean
  }>(),
  {
    small: false,
    padding: false
  }
)
</script>

<template>
  <p
    :class="[
      small ? 'text-sm lg:text-base' : 'text-lg lg:text-xl',
      padding ? 'pt-8' : 'pt-0',
      'font-normal text-gray-500 dark:text-surface-400'
    ]"
  >
    <slot></slot>
  </p>
</template>
