<script setup lang="ts">
const props = defineProps<{
  label?: string
  taxaName: string
  chrom: string
  start: number
  end: number
}>()

const text = props.label || props.start
const cookedTaxaName = props.taxaName.replace(/ /g, '_')
const link = `https://jul2023.archive.ensembl.org/${cookedTaxaName}/Location/View?r=${
  props.chrom
}:${props.start}:${props.end + 1};db=core`
</script>
<template>
  <a
    class="text-primary-500 hover:text-secondary-500"
    :href="link"
    target="_blank"
    rel="noopener noreferrer"
    >{{ text }}
  </a>
</template>
