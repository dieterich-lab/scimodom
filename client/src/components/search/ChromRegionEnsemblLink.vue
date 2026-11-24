<script setup lang="ts">
import { computed } from 'vue'

// browseUrl is the page of the annotation source for the release
// the records were annotated with, cf. services/annotation. Null
// while it is being resolved, or if the source serves no browsable
// page: the position is then shown unlinked rather than pointing
// at a release it does not belong to.
const props = defineProps<{
  browseUrl: string | null
  chrom: string
  start: number
  end: number
}>()

const link = computed(() =>
  props.browseUrl
    ? `${props.browseUrl}/Location/View?r=${props.chrom}:${props.start}:${props.end + 1};db=core`
    : null
)
</script>
<template>
  <a
    v-if="link"
    class="text-primary-500 hover:text-secondary-500"
    :href="link"
    target="_blank"
    rel="noopener noreferrer"
    >{{ start }}</a
  >
  <span v-else>{{ start }}</span>
</template>
