<script setup>
import { ref, computed } from 'vue'
import { toTree, toIds } from '@/utils/index.js'

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
const species = computed(() => toTree(props.options, ['domain', 'taxa_sname'], 'taxa_sname'))
const selectedSpecies = ref()
const organism = ref()
const selectedOrganism = ref()
const updDataset = ref()
const selectedDataset = ref()

const emit = defineEmits(['selectedSpecies', 'selectedDataset'])

const updateOrganism = () => {
  selectedOrganism.value = undefined
  selectedModification.value = undefined
  selectedTechnology.value = undefined
  selectedDataset.value = undefined
  var options = props.options.filter((item) => item.taxa_sname === selectedSpecies.value.label)
  organism.value = toTree(options, ['cto'], 'organism_id')
  updateDataset()
  emit('selectedSpecies', selectedSpecies.value.label)
  emit('selectedDataset', undefined)
}

const updateModification = () => {
  selectedModification.value = undefined
  selectedTechnology.value = undefined
  selectedDataset.value = undefined
  var selectedOrganismIds = selectedOrganism.value.map((item) => item.key)
  var options = props.options.filter((item) => selectedOrganismIds.includes(item.organism_id))
  modification.value = toTree(options, ['rna', 'modomics_sname'], 'modification_id')
  updateDataset()
}

const updateTechnology = () => {
  selectedTechnology.value = undefined
  selectedDataset.value = undefined
  var selectedModificationIds = toIds(
    selectedModification.value,
    Array.from(new Set(props.options.map((item) => item.modification_id)))
  )
  var selectedOrganismIds = selectedOrganism.value.map((item) => item.key)
  var options = props.options.filter(
    (item) =>
      selectedModificationIds.includes(item.modification_id) &&
      selectedOrganismIds.includes(item.organism_id)
  )
  technology.value = toTree(options, ['cls', 'meth', 'tech'], 'technology_id')
  updateDataset()
}

function updateDataset() {
  selectedDataset.value = undefined
  var selectedModificationIds = toIds(
    selectedModification.value,
    Array.from(new Set(props.options.map((item) => item.modification_id)))
  )
  var selectedTechnologyIds = toIds(
    selectedTechnology.value,
    Array.from(new Set(props.options.map((item) => item.technology_id)))
  )
  var selectedOrganismIds =
    Object.is(selectedOrganism.value, undefined) || selectedOrganism.value.length === 0
      ? organism.value.map((item) => item.key)
      : selectedOrganism.value.map((item) => item.key)
  var options = props.dataset.filter(
    (item) =>
      selectedModificationIds.includes(item.modification_id) &&
      selectedTechnologyIds.includes(item.technology_id) &&
      selectedOrganismIds.includes(item.organism_id)
  )
  updDataset.value = [...new Map(options.map((item) => [item['dataset_id'], item])).values()].map(
    (item) => {
      return { dataset_id: item.dataset_id, dataset_title: item.dataset_title }
    }
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
        root: { class: 'w-full md:w-full' }
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
        root: { class: 'w-full md:w-full' }
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
        root: { class: 'w-full md:w-full' }
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
        root: { class: 'w-full md:w-full' }
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
      :options="updDataset"
      filter
      optionLabel="dataset_title"
      placeholder="5. Select dataset"
      :maxSelectedLabels="3"
      :pt="{
        root: { class: 'col-span-4 md:w-full' }
      }"
    />
  </div>
</template>
