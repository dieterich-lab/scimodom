<script setup>
const props = defineProps({
  dataset: {
    type: Object,
    required: true
  }
})
const info = `(${props.dataset.rna},  ${props.dataset.modomics_sname} ${props.dataset.cto}, ${props.dataset.tech})`
</script>
<template>
  <div class="flex">
    <div class="pr-2 font-semibold">{{ dataset.dataset_title }}</div>
    <div class="pr-2 italic">{{ info }}</div>
    <div class="text-surface-500">{{ dataset.dataset_id }}</div>
  </div>
</template>
