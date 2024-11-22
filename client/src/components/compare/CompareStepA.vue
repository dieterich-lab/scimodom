<script setup lang="ts">
import { ref, computed } from 'vue'
import TaxaSelection from '@/components/ui/TaxaSelection.vue'
import DatasetSelectionMulti from '@/components/ui/DatasetSelectionMulti.vue'
import { type Dataset, getDatasetsByTaxaId } from '@/services/dataset'
import { type Taxa } from '@/services/selection'
import { type ResultStepA } from '@/utils/comparison'

const model = defineModel<ResultStepA>()

const emit = defineEmits<{
  (e: 'change', datasets: ResultStepA): void
}>()

const selectedTaxa = ref<Taxa>()
const availableDatasets = ref<Dataset[]>([])
const selectedDatasets = ref<Dataset[]>([])

const disabledDatasetSelection = computed(() => !selectedTaxa.value)

const changeTaxa = (value: Taxa) => {
  model.value = undefined
  selectedDatasets.value = []
  getDatasetsByTaxaId(value.taxa_id).then((data) => (availableDatasets.value = [...data]))
}

function changeDataset(datasets: Dataset[]) {
  const datasetIds = datasets.map((x) => x.dataset_id)
  const result: ResultStepA = {
    datasets,
    remainingDatasets: availableDatasets.value.filter((x) => !datasetIds.includes(x.dataset_id))
  }
  model.value = result
  emit('change', result)
}
</script>
<template>
  <div class="mb-4">
    Select one organism and choose up to three reference dataset. Use the dataset search bar to find
    records.
  </div>
  <div class="grid grid-cols-4 gap-6">
    <TaxaSelection
      v-model="selectedTaxa"
      placeholder="1. Select one organism"
      @change="changeTaxa"
    />
    <DatasetSelectionMulti
      v-model="selectedDatasets"
      :datasets="availableDatasets"
      placeholder="2. Select dataset"
      :selectionLimit="3"
      :maxSelectedLabels="3"
      :disabled="disabledDatasetSelection"
      @change="changeDataset"
    />
  </div>
</template>
