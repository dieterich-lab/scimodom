<script setup lang="ts">
const props = defineProps<{
  name: string
  referenceId: number
}>()
const link = `https://www.genesilico.pl/modomics/modifications/${props.referenceId}`
</script>
<template>
  <a
    class="text-primary-500 hover:text-secondary-500"
    :href="link"
    target="_blank"
    rel="noopener noreferrer"
  >
    {{ name }}
  </a>
</template>
