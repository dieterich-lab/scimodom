<script setup>
const props = defineProps({
  secondary: {
    type: Boolean,
    default: false
  }
})

function sectionClass() {
  let classes = []
  if (props.secondary) classes.push('section--secondary')
  return classes
}
</script>

<template>
  <section class="section" :class="sectionClass()">
    <div class="section--inner container mx-auto">
      <slot></slot>
    </div>
  </section>
</template>

<style scoped>
.section {
  @apply p-[calc(2%+25px)] relative w-full flex-1 bg-transparent dark:bg-surface-900;
}
.section--secondary {
  @apply mt-px bg-gradient-to-t from-surface-50 to-transparent dark:from-surface-900 dark:to-surface-800 border-b border-solid border-surface-50 dark:border-surface-900;
}
.section--inner {
  @apply relative z-10;
}
</style>
