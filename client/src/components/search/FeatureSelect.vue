<script setup>
import { useDialogState } from '@/stores/DialogState'
import { ref, watch } from 'vue'
import { handleRequestWithErrorReporting } from '@/utils/request'
import { HTTP } from '@/services/API'

const props = defineProps({
  rnaType: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Select feature'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const dialogState = useDialogState()
const model = defineModel()
const features = ref()

watch(
  () => props.rnaType,
  () => {
    if (!props.rnaType) {
      return
    }
    handleRequestWithErrorReporting(
      HTTP.get(`/features/${props.rnaType}`),
      'Failed to load features',
      dialogState
    ).then(function (data) {
      features.value = data.features
    })
  },
  { immediate: true }
)
</script>
<template>
  <MultiSelect
    v-model="model"
    :options="features"
    :placeholder="placeholder"
    :maxSelectedLabels="3"
    :disabled="disabled"
    :pt="{
      root: { class: 'w-full md:w-full' }
    }"
    :ptOptions="{ mergeProps: true }"
  />
</template>
