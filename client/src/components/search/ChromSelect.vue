<script setup lang="ts">
import { useDialogState } from '@/stores/DialogState'
import { ref, watch } from 'vue'
import { type Chrom, getChromsByTaxaId } from '@/services/chrom'
import type { DropdownChangeEvent } from 'primevue/dropdown'

const props = withDefaults(
  defineProps<{
    taxaId?: number
    placeholder: string
    disabled: boolean
  }>(),
  {
    placeholder: 'Select chromosome',
    disabled: false
  }
)

const emit = defineEmits<{
  (e: 'change', value: Chrom): void
}>()

const dialogState = useDialogState()
const model = defineModel()
const chroms = ref()

function change(e: DropdownChangeEvent) {
  emit('change', e.value)
}

watch(
  () => props.taxaId,
  () => {
    if (!props.taxaId) {
      return
    }
    chroms.value = getChromsByTaxaId(props.taxaId, dialogState)
  },
  { immediate: true }
)
</script>
<template>
  <Dropdown
    @change="change"
    v-model="model"
    :options="chroms"
    optionLabel="chrom"
    showClear
    :disabled="disabled"
    :placeholder="placeholder"
    v-tooltip.top="'Chromosome or gene (mutually exclusive)'"
    :pt="{
      root: { class: 'w-full md:w-full' }
    }"
    :ptOptions="{ mergeProps: true }"
  />
</template>
