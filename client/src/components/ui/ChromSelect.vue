<script setup lang="ts">
import { ref, watch } from 'vue'
import Dropdown from 'primevue/dropdown'
import { useDialogState } from '@/stores/DialogState'
import { type Chrom, getChromsByTaxaId } from '@/services/chrom'
import type { DropdownChangeEvent } from 'primevue/dropdown'
import { trashRequestErrors } from '@/services/API'

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
const model = defineModel<Chrom>()
const chroms = ref<Chrom[]>([])

function change(e: DropdownChangeEvent) {
  emit('change', e.value)
}

watch(
  () => props.taxaId,
  () => {
    if (!props.taxaId) {
      return
    }
    getChromsByTaxaId(props.taxaId, dialogState)
      .then((data) => (chroms.value = data))
      .catch((e) => {
        chroms.value = []
        trashRequestErrors(e)
      })
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
