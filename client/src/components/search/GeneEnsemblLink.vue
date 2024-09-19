<script setup>
const props = defineProps({
  taxaName: { type: String },
  geneName: { type: [String, null] },
  geneId: { type: [String, null] }
})

const cookedTaxaName = props.taxaName.replace(/ /g, '_')
const link = `https://jul2023.archive.ensembl.org/${cookedTaxaName}/Gene/Summary?db=core;g=`
const geneLinkArray = props.geneId != null ? props.geneId.split(',').map((id) => link + id) : []
const geneNameArray = props.geneName != null ? props.geneName.split(',') : []
</script>

<template>
  <a
    v-for="(name, index) in geneNameArray"
    :key="index"
    class="text-primary-500 hover:text-secondary-500"
    :href="geneLinkArray[index]"
    target="_blank"
    rel="noopener noreferrer"
    >{{ name }}<span v-if="index != geneNameArray.length - 1">,</span>
  </a>
</template>
