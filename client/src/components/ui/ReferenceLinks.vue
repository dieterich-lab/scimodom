<script setup lang="ts">
const props = defineProps<{
  type: 'DOI' | 'PMID'
  data?: string
}>()

const urlPrefix = props.type === 'DOI' ? 'https://doi.org/' : 'http://www.ncbi.nlm.nih.gov/pubmed/'
function splitStr(str?: string) {
  if (str) {
    return str.split(',')
  } else {
    return []
  }
}
</script>
<template>
  <ul class="list-none" v-for="item in splitStr(data)" v-bind:key="item">
    <a class="text-secondary-500 pr-12" target="_blank" :href="`${urlPrefix}${item}`">{{ item }}</a>
  </ul>
</template>
