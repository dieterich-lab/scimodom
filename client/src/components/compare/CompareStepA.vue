<script setup>
import { ref, computed } from 'vue'

const emit = defineEmits(['datasetUpdated'])
const model = defineModel()
const props = defineProps({
  organism: {
    type: Object,
    required: true
  },
  dataset: {
    type: Array,
    required: true
  }
})

const selectedTaxid = ref()
const dataset = ref()

const updateDataset = (value) => {
  model.value = []
  let opts = props.dataset.filter((item) => item.taxa_id == value)
  dataset.value = [...new Map(opts.map((item) => [item['dataset_id'], item])).values()].map(
    (item) => {
      return {
        dataset_id: item.dataset_id,
        dataset_title: item.dataset_title,
        dataset_info:
          '(' + item.rna + ', ' + item.modomics_sname + ', ' + item.cto + ', ' + item.tech + ')'
      }
    }
  )
  emit('datasetUpdated', dataset.value)
}
</script>

<template>
  <div class="grid grid-cols-4 gap-6">
    <CascadeSelect
      @change="updateDataset($event.value)"
      v-model="selectedTaxid"
      :options="props.organism"
      optionValue="key"
      optionLabel="label"
      optionGroupLabel="label"
      :optionGroupChildren="['child1']"
      placeholder="1. Select one organism"
      :pt="{
        root: { class: 'w-full md:w-full' }
      }"
      :ptOptions="{ mergeProps: true }"
    />
    <MultiSelect
      v-model="model"
      :options="dataset"
      :selectionLimit="3"
      filter
      :filterFields="['dataset_id', 'dataset_title', 'dataset_info']"
      optionValue="dataset_id"
      optionLabel="dataset_id"
      placeholder="2. Select dataset"
      :maxSelectedLabels="3"
      display="chip"
      :pt="{
        root: { class: 'col-span-3 w-full md:w-full' }
      }"
      :ptOptions="{ mergeProps: true }"
    >
      <template #option="slotProps">
        <div class="flex">
          <div class="pr-2 text-surface-500">{{ slotProps.option.dataset_id }}</div>
          <div class="pr-2 font-semibold">{{ slotProps.option.dataset_title }}</div>
          <div class="italic">{{ slotProps.option.dataset_info }}</div>
        </div>
      </template>
    </MultiSelect>
  </div>
</template>
