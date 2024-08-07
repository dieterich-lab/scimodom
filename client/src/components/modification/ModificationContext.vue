<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { HTTP } from '@/services/API.js'

const props = defineProps({
  coords: {
    type: Object,
    required: true
  }
})

const router = useRouter()

const defaultContext = ref(5)
const sequence = ref([])

watch(
  () => props.coords,
  () => {
    load(defaultContext.value)
  },
  { immediate: true }
)

function load(context) {
  HTTP.get(`/modification/genomic-context/${context}`, {
    params: {
      taxaId: props.coords.taxa_id,
      chrom: props.coords.chrom,
      start: props.coords.start,
      end: props.coords.end,
      strand: props.coords.strand
    },
    paramsSerializer: {
      indexes: null
    }
  })
    .then(function (response) {
      sequence.value = splitContext(response.data.context)
    })
    .catch((error) => {
      console.log(error)
    })
}

function splitContext(str, index = defaultContext.value) {
  const span = index + props.coords.end - props.coords.start
  return [str.slice(0, index), str.slice(index, span), str.slice(span)]
}
</script>

<template>
  <span class="font-semibold"
    >{{ sequence[0] }}<span class="text-red-500">{{ sequence[1] }}</span
    >{{ sequence[2] }}</span
  >
</template>
