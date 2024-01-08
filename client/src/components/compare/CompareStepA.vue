<script setup>
import { ref, computed } from 'vue'
import {
  updSpecies,
  updOrganismFromSpec,
  updModificationFromOrg,
  updTechnologyFromOrgAndMod,
  updDataset
} from '@/utils/selection.js'

const props = defineProps({
  options: {
    type: Array,
    required: true
  },
  dataset: {
    type: Array,
    required: true
  }
})

const modification = ref()
const selectedModification = ref()
const technology = ref()
const selectedTechnology = ref()
const species = computed(() => updSpecies(props.options))
const selectedSpecies = ref()
const organism = ref()
const selectedOrganism = ref()
const datasetSelection = ref()
const selectedDataset = ref()

const emit = defineEmits(['selectedSpecies', 'selectedDataset'])

const updateOrganism = () => {
  selectedOrganism.value = undefined
  selectedModification.value = undefined
  selectedTechnology.value = undefined
  selectedDataset.value = undefined
  organism.value = updOrganismFromSpec(props.options, selectedSpecies.value.label)
  updateDataset()
  emit('selectedSpecies', selectedSpecies.value.label)
}

const updateModification = () => {
  selectedModification.value = undefined
  selectedTechnology.value = undefined
  selectedDataset.value = undefined
  modification.value = updModificationFromOrg(props.options, selectedOrganism.value)
  updateDataset()
}

const updateTechnology = () => {
  selectedTechnology.value = undefined
  selectedDataset.value = undefined
  technology.value = updTechnologyFromOrgAndMod(
    props.options,
    selectedOrganism.value,
    selectedModification.value
  )
  updateDataset()
}

function updateDataset() {
  selectedDataset.value = undefined
  emit('selectedDataset', undefined)
  datasetSelection.value = updDataset(
    props.options,
    organism.value,
    selectedOrganism.value,
    selectedModification.value,
    selectedTechnology.value,
    props.dataset
  )
}
</script>

<template>
  <div class="grid grid-flow-row-dense grid-cols-4 gap-6">
    <Dropdown
      @change="updateOrganism"
      v-model="selectedSpecies"
      :options="species"
      optionLabel="label"
      optionGroupLabel="label"
      optionGroupChildren="children"
      placeholder="1. Select one organism"
      :pt="{
        root: { class: 'w-full md:w-full shadow' }
      }"
    />
    <MultiSelect
      @change="updateModification"
      v-model="selectedOrganism"
      :options="organism"
      optionLabel="label"
      placeholder="2. Select cell/tissue"
      :maxSelectedLabels="3"
      :pt="{
        root: { class: 'w-full md:w-full shadow' }
      }"
    />
    <TreeSelect
      @change="updateTechnology"
      v-model="selectedModification"
      :options="modification"
      selectionMode="checkbox"
      :metaKeySelection="false"
      placeholder="3. Select RNA modifications"
      :pt="{
        root: { class: 'w-full md:w-full shadow' }
      }"
    />
    <TreeSelect
      @change="updateDataset"
      v-model="selectedTechnology"
      :options="technology"
      selectionMode="checkbox"
      :metaKeySelection="false"
      placeholder="4. Select technologies"
      :pt="{
        root: { class: 'w-full md:w-full shadow' }
      }"
    />
    <MultiSelect
      @change="
        emit(
          'selectedDataset',
          $event.value.map((d) => d.dataset_id)
        )
      "
      v-model="selectedDataset"
      :options="datasetSelection"
      filter
      optionLabel="dataset_display"
      placeholder="5. Select dataset"
      :maxSelectedLabels="3"
      :pt="{
        root: { class: 'col-span-4 md:w-full shadow' }
      }"
    />
  </div>
</template>
