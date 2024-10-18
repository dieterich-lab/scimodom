<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DatasetSelectionMulti from '@/components/ui/DatasetSelectionMulti.vue'
import { type Dataset, allDatasetsCache } from '@/services/dataset'
import { getOptionsForPrimvueCascadeSelect } from '@/utils/primevue'
import { selectionsCache } from '@/services/selection'

const emit = defineEmits<{
  datasetsUpdated: [value: Dataset[]]
}>()
const selectedDatasets = defineModel()

const selectedTaxid = ref()
const datasets = ref<Dataset[]>([])
const filteredDatasets = ref<Dataset[]>([])
const taxidOptions = ref()

const updateFilteredDatasets = (value: number) => {
  selectedDatasets.value = []
  filteredDatasets.value = [...datasets.value.filter((item) => item.taxa_id === value)]
  emit('datasetsUpdated', filteredDatasets.value)
}
onMounted(async () => {
  datasets.value = [...(await allDatasetsCache.getData())]
  const rawSelections = await selectionsCache.getData()
  const cookedSelections = rawSelections.map((x) => {
    return { ...x, kingdom: x.kingdom ? x.kingdom : x.domain }
  })
  taxidOptions.value = getOptionsForPrimvueCascadeSelect(cookedSelections, [
    'kingdom',
    'taxa_sname'
  ])
})
</script>

<template>
  <div class="grid grid-cols-4 gap-6">
    <CascadeSelect
      @change="updateFilteredDatasets($event.value)"
      v-model="selectedTaxid"
      :options="taxidOptions"
      optionValue="taxa_id"
      optionLabel="label"
      optionGroupLabel="label"
      :optionGroupChildren="['cChildren']"
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
