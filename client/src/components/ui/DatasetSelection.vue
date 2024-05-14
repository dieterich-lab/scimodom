<script setup>
import { onMounted, ref } from 'vue'
import DatasetItem from '@/components/ui/DatasetItem.vue'
import { loadDatasets } from '@/services/dataset'

const props = defineProps({
  myDatasetsOnly: {
    type: Boolean,
    required: false,
    default: false
  },
  refresh: {
    type: Boolean,
    required: false,
    default: true
  }
})

const model = defineModel()
const datasets = ref([])
const datasetsById = ref(new Map())

function getLabel(dataset) {
  return `${dataset.dataset_title} ${dataset.dataset_id}`
}

function getEmptyMessage() {
  return props.myDatasetsOnly
    ? 'Your projects have no dataset - either get associated with a project or upload a bedRMod'
    : 'No datasets found'
}

onMounted(() => {
  loadDatasets(datasets, datasetsById, props.myDatasetsOnly, true)
})
</script>
<template>
  <Dropdown
    v-model="model"
    :options="datasets"
    filter
    :optionLabel="getLabel"
    placeholder="Select a dataset"
    :empty-message="getEmptyMessage()"
    class="w-full"
  >
    <template #value="slotProps">
      <div v-if="slotProps.value">
        <DatasetItem :dataset="slotProps.value" />
      </div>
      <span v-else>
        {{ slotProps.placeholder }}
      </span>
    </template>
    <template #option="slotProps">
      <DatasetItem :dataset="slotProps.option" />
    </template>
  </Dropdown>
</template>
