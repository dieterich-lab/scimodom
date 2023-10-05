<script setup>
defineProps({
  icon: {
    type: String,
    required: true
  }
})
</script>

<template>
  <button class="button-icon">
    <i :class="icon" class="w-5 h-5 mr-2 -ml-1" />
    <slot></slot>
  </button>
</template>

<style scoped>
.button-icon {
  @apply focus:ring-4 focus:outline-none font-medium rounded-lg text-sm px-5 py-2.5 text-center inline-flex items-center mr-2;
}
</style>
