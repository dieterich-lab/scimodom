<script setup lang="ts">
import MultiSelect, { type MultiSelectChangeEvent } from 'primevue/multiselect'
import DatasetItem from '@/components/ui/DatasetItem.vue'
import type { Dataset } from '@/services/dataset'

const props = withDefaults(
  defineProps<{
    datasets: Dataset[]
    myDatasetsOnly?: boolean
    refresh?: boolean
    selectLimit?: number
    maxSelectedLabels?: number
    placeholder?: string
    disabled?: boolean
  }>(),
  {
    myDatasetsOnly: false,
    refresh: true,
    placeholder: 'Select a dataset',
    disabled: false
  }
)

const model = defineModel<Dataset[]>()

const emit = defineEmits<{
  (e: 'change', datasets: Dataset[]): void
}>()

function getEmptyMessage() {
  return props.myDatasetsOnly
    ? 'Your projects have no dataset - either get associated with a project or upload a bedRMod'
    : 'No datasets found'
}

function change(event: MultiSelectChangeEvent) {
  emit('change', event.value)
}
</script>
<template>
  <MultiSelect
    v-model="model"
    :options="datasets"
    :selectionLimit="selectLimit"
    :emptyMessage="getEmptyMessage()"
    filter
    :filterFields="[
      'dataset_id',
      'dataset_title',
      'project_title',
      'project_id',
      'rna',
      'modomics_sname',
      'cto',
      'tech'
    ]"
    optionLabel="dataset_id"
    :placeholder="placeholder"
    :maxSelectedLabels="maxSelectedLabels"
    display="chip"
    :pt="{
      root: { class: 'col-span-3 w-full md:w-full' }
    }"
    :ptOptions="{ mergeProps: true }"
    :disabled="disabled"
    @change="change"
  >
    <template #option="slotProps">
      <DatasetItem :dataset="slotProps.option" />
    </template>
  </MultiSelect>
</template>
