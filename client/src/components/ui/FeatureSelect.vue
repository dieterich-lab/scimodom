<script setup lang="ts">
import { ref, watch } from 'vue'
import MultiSelect from 'primevue/multiselect'
import { useDialogState } from '@/stores/DialogState'
import { getFeaturesByRnaType } from '@/services/feature'
import { trashRequestErrors } from '@/services/API'

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
const model = defineModel<string[]>()
const features = ref<string[]>()

watch(
  () => props.rnaType,
  () => {
    if (!props.rnaType) {
      return
    }
    getFeaturesByRnaType(props.rnaType, dialogState)
      .then((data) => (features.value = data))
      .catch((e) => {
        features.value = []
        trashRequestErrors(e)
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
