<script setup lang="ts">
import Dropdown from 'primevue/dropdown'
import { onMounted, ref } from 'vue'
import DatasetItem from '@/components/ui/DatasetItem.vue'
import {
  type Dataset,
  allDatasetsByIdCache,
  allDatasetsCache,
  myDatasetsByIdCache,
  myDatasetsCache
} from '@/services/dataset'

const props = withDefaults(
  defineProps<{
    myDatasetsOnly?: boolean
    refresh?: boolean
  }>(),
  {
    myDatasetsOnly: false,
    refresh: true
  }
)

const model = defineModel<Dataset>()
const datasets = ref<Dataset[]>([])
const datasetsById = ref<Map<string, Dataset>>(new Map())

function getLabel(dataset: Dataset) {
  return `${dataset.dataset_title} ${dataset.dataset_id}`
}

function getEmptyMessage() {
  return props.myDatasetsOnly
    ? 'Your projects have no dataset - either get associated with a project or upload a bedRMod'
    : 'No datasets found'
}

onMounted(() => {
  const cache = props.myDatasetsOnly ? myDatasetsCache : allDatasetsCache
  const byIdCache = props.myDatasetsOnly ? myDatasetsByIdCache : allDatasetsByIdCache
  cache.getData().then((data) => {
    datasets.value = [...data]
  })
  byIdCache.getData().then((data) => (datasetsById.value = data))
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
