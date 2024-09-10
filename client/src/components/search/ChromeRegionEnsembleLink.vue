<script setup>
const props = defineProps({
  label: { type: String, required: false },
  taxaName: { type: String },
  chrom: { type: String },
  start: { type: Number },
  end: { type: Number }
})

const text = props.label || props.start
const cookedTaxaName = props.taxaName.replace(/ /g, '_')
const link = `https://www.ensembl.org/${cookedTaxaName}/Location/View?r=${props.chrom}:${
  props.start
}:${props.end + 1};db=core`
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
