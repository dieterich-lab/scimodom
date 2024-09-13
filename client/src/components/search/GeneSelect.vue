<script setup>
import { useDialogState } from '@/stores/DialogState'
import { ref, watch } from 'vue'
import { handleRequestWithErrorReporting } from '@/utils/request'
import { HTTP } from '@/services/API'

const props = defineProps({
  selectionIds: {
    type: Object,
    default() {
      return []
    }
  },
  placeholder: {
    type: String,
    default: 'Select gene'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})
defineEmits(['change'])

const dialogState = useDialogState()
const model = defineModel()
const filteredGenes = ref()
const genes = ref()

watch(
  () => props.selectionIds,
  () => {
    if (props.selectionIds.length === 0) {
      genes.value = null
      filteredGenes.value = null
      return
    }
    handleRequestWithErrorReporting(
      HTTP.get('/genes', { params: { selection: props.selectionIds } }),
      'Failed to load genes',
      dialogState
    ).then((data) => {
      genes.value = data.sort()
    })
  },
  { immediate: true }
)

function searchGene(event) {
  setTimeout(() => {
    if (!event.query.trim().length) {
      filteredGenes.value = [...genes.value]
    } else {
      filteredGenes.value = genes.value.filter((g) => {
        return g.toLowerCase().startsWith(event.query.toLowerCase())
      })
    }
  }, 250)
}
</script>
<template>
  <AutoComplete
    v-model="model"
    :suggestions="filteredGenes"
    @complete="searchGene"
    @change="$emit('change')"
    forceSelection
    :placeholder="placeholder"
    :disabled="disabled"
    v-tooltip.top="'Gene or chromosome (mutually exclusive)'"
    :pt="{
      root: { class: 'w-full md:w-full' },
      input: { class: 'w-full md:w-full' }
    }"
    :ptOptions="{ mergeProps: true }"
  />
</template>
