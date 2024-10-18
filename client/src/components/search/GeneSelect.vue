<script setup lang="ts">
import { useDialogState } from '@/stores/DialogState'
import { ref, watch } from 'vue'
import { getGenesForSelectionIds } from '@/services/gene'
import type { AutoCompleteCompleteEvent } from 'primevue/autocomplete'

const props = withDefaults(
  defineProps<{
    selectionIds: number[]
    placeholder: string
    disabled: boolean
  }>(),
  {
    selectionIds: () => [],
    placeholder: 'Select gene',
    disabled: false
  }
)

defineEmits(['change'])

const dialogState = useDialogState()
const model = defineModel()
const filteredGenes = ref<string[]>([])
const genes = ref<string[]>([])

watch(
  () => props.selectionIds,
  () => {
    if (props.selectionIds.length === 0) {
      genes.value = []
      filteredGenes.value = []
      return
    }
    getGenesForSelectionIds(props.selectionIds, dialogState)
  },
  { immediate: true }
)

function searchGene(e: AutoCompleteCompleteEvent) {
  setTimeout(() => {
    if (!e.query.trim().length) {
      filteredGenes.value = [...genes.value]
    } else {
      filteredGenes.value = genes.value.filter((g) => {
        return g.toLowerCase().startsWith(e.query.toLowerCase())
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
