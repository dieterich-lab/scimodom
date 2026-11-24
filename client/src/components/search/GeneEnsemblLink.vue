<script setup lang="ts">
import { computed } from 'vue'

// cf. ChromRegionEnsemblLink for browseUrl
const props = defineProps<{
  browseUrl: string | null
  geneName: string | null
  geneId: string | null
}>()

const geneNameArray = computed(() => (props.geneName != null ? props.geneName.split(',') : []))
const geneLinkArray = computed(() =>
  props.browseUrl != null && props.geneId != null
    ? props.geneId.split(',').map((id) => `${props.browseUrl}/Gene/Summary?db=core;g=${id}`)
    : []
)
</script>
<template>
  <template v-for="(name, index) in geneNameArray" :key="index">
    <a
      v-if="geneLinkArray[index]"
      class="text-primary-500 hover:text-secondary-500"
      :href="geneLinkArray[index]"
      target="_blank"
      rel="noopener noreferrer"
      >{{ name }}</a
    >
    <span v-else>{{ name }}</span>
    <span v-if="index != geneNameArray.length - 1">,</span>
  </template>
</template>
