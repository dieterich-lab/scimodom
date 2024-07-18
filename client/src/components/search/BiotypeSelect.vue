<script setup>
import { ref, watch } from 'vue'
import { HTTP } from '@/services/API'

import { handleRequestWithErrorReporting } from '@/utils/request'
import { useDialogState } from '@/stores/DialogState'

const props = defineProps({
  rnaType: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Select biotype'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const dialogState = useDialogState()
const model = defineModel()
const biotypes = ref([])

watch(
  () => props.rnaType,
  () => {
    if (!props.rnaType) {
      return
    }
    handleRequestWithErrorReporting(
      HTTP.get(`/biotypes/${props.rnaType}`),
      'Failed to load biotypes',
      dialogState
    ).then(function (data) {
      biotypes.value = data.biotypes
    })
  },
  { immediate: true }
)
</script>
<template>
  <MultiSelect
    v-model="model"
    :options="biotypes"
    :placeholder="placeholder"
    :maxSelectedLabels="3"
    :disabled="disabled"
    :pt="{
      root: { class: 'w-full md:w-full' }
    }"
    :ptOptions="{ mergeProps: true }"
  >
  </MultiSelect>
</template>
