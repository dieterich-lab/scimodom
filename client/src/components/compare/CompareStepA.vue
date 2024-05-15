<script setup>
import { ref, onMounted } from 'vue'
import DatasetSelectionMulti from '@/components/ui/DatasetSelectionMulti.vue'
import { loadDatasets } from '@/services/dataset'
import { HTTP } from '@/services/API'
import { nestedSort, toCascade, toTree } from '@/utils'

const emit = defineEmits(['datasetUpdated'])
const selectedDatasets = defineModel()

const selectedTaxid = ref()
const datasets = ref()
const filteredDatasets = ref([])
const taxid = ref()

const updateFilteredDatasets = (value) => {
  selectedDatasets.value = []
  filteredDatasets.value = datasets.value.filter((item) => item.taxa_id === value)
  emit('datasetUpdated', filteredDatasets.value)
}
onMounted(() => {
  loadDatasets(datasets, null, false)

  HTTP.get('/selection')
    .then(function (response) {
      let opts = response.data
      opts = opts.map((item) => {
        const kingdom = Object.is(item.kingdom, null) ? item.domain : item.kingdom
        return { ...item, kingdom }
      })
      taxid.value = toCascade(toTree(opts, ['kingdom', 'taxa_sname'], 'taxa_id'))
      nestedSort(taxid.value, ['child1'])
    })
    .catch((error) => {
      console.log(error)
    })
})
</script>

<template>
  <div class="grid grid-cols-4 gap-6">
    <CascadeSelect
      @change="updateFilteredDatasets($event.value)"
      v-model="selectedTaxid"
      :options="taxid"
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
    <DatasetSelectionMulti
      v-model="selectedDatasets"
      :datasets="filteredDatasets"
      placeholder="2. Select dataset"
      :selectionLimit="3"
      :maxSelectedLabels="3"
    />
  </div>
</template>
