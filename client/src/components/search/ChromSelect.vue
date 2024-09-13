<script setup>
import { useDialogState } from '@/stores/DialogState'
import { ref, watch } from 'vue'
import { handleRequestWithErrorReporting } from '@/utils/request'
import { HTTP } from '@/services/API'

const props = defineProps({
  taxaId: {
    type: Number,
    required: false
  },
  placeholder: {
    type: String,
    default: 'Select chromosome'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})
defineEmits(['change'])

const dialogState = useDialogState()
const model = defineModel()
const chroms = ref()

watch(
  () => props.taxaId,
  () => {
    if (!props.taxaId) {
      return
    }
    handleRequestWithErrorReporting(
      HTTP.get(`/chroms/${props.taxaId}`),
      'Failed to load chromes',
      dialogState
    ).then(function (data) {
      chroms.value = data
    })
  },
  { immediate: true }
)
</script>
<template>
  <Dropdown
    @change="$emit('change')"
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
