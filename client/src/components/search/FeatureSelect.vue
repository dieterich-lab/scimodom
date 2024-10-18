<script setup lang="ts">
import { useDialogState } from '@/stores/DialogState'
import { ref, watch } from 'vue'
import { handleRequestWithErrorReporting } from '@/utils/request'
import { HTTP } from '@/services/API'
import { getFeaturesByRnaType } from '@/services/feature'

const props = withDefaults(
  defineProps<{
    rnaType: string
    placeholder: string
    disabled: boolean
  }>(),
  {
    rnaType: '',
    placeholder: 'Select feature',
    disabled: false
  }
)

const dialogState = useDialogState()
const model = defineModel()
const features = ref()

watch(
  () => props.rnaType,
  () => {
    if (!props.rnaType) {
      return
    }
    getFeaturesByRnaType(props.rnaType, dialogState).then((data) => {
      features.value = data
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
