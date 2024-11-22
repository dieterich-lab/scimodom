<script setup lang="ts">
import { ref, watch } from 'vue'
import MultiSelect from 'primevue/multiselect'

import { useDialogState } from '@/stores/DialogState'
import { getBioTypes } from '@/services/biotype'
import { trashRequestErrors } from '@/services/API'

const props = withDefaults(
  defineProps<{
    rnaType: string
    placeholder: string
    disabled: boolean
  }>(),
  {
    rnaType: '',
    placeholder: 'Select biotype',
    disabled: false
  }
)

const dialogState = useDialogState()
const model = defineModel()
const biotypes = ref<string[]>([])

watch(
  () => props.rnaType,
  () => {
    if (props.rnaType) {
      getBioTypes(props.rnaType, dialogState)
        .then((data) => {
          biotypes.value = data
        })
        .catch((e) => {
          biotypes.value = []
          trashRequestErrors(e)
        })
    } else {
      biotypes.value = []
    }
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
