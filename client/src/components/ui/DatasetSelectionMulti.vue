<script setup>
import DatasetItem from '@/components/ui/DatasetItem.vue'

const props = defineProps({
  datasets: {
    type: Object,
    required: true
  },
  myDatasetsOnly: {
    type: Boolean,
    required: false,
    default: false
  },
  refresh: {
    type: Boolean,
    required: false,
    default: true
  },
  selectLimit: {
    type: Number,
    required: false
  },
  maxSelectedLabels: {
    type: Number,
    required: false
  },
  placeholder: {
    type: String,
    required: false,
    default: 'Select a dataset'
  },
  disabled: {
    type: Boolean,
    required: false,
    default: false
  }
})

const model = defineModel()

function getEmptyMessage() {
  return props.myDatasetsOnly
    ? 'Your projects have no dataset - either get associated with a project or upload a bedRMod'
    : 'No datasets found'
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
    optionValue="dataset_id"
    optionLabel="dataset_id"
    :placeholder="placeholder"
    :maxSelectedLabels="maxSelectedLabels"
    display="chip"
    :pt="{
      root: { class: 'col-span-3 w-full md:w-full' }
    }"
    :ptOptions="{ mergeProps: true }"
    :disabled="disabled"
  >
    <template #option="slotProps">
      <DatasetItem :dataset="slotProps.option" />
    </template>
  </MultiSelect>
</template>
