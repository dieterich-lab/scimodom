<script setup>
import { ref } from 'vue'

const modification = ref()
const selectedModification = ref()
const technology = ref()
const selectedTechnology = ref()
const species = ref()
const selectedSpecies = ref()
const organism = ref()
const selectedOrganism = ref()
const dataset = ref()
const selectedDataset = ref()

const props = defineProps({
  selectOptions: {
    type: Array,
    required: true
  },
  selectDataset: {
    type: Array,
    required: true
  }
})

species.value = toTree(props.selectOptions, ['domain', 'taxa_sname'], 'taxa_sname')

const emit = defineEmits(['selectedSpecies', 'selectedDataset'])

const emitSelectedSpecies = () => {
  emit('selectedSpecies', selectedSpecies.value.label)
}

const emitSelectedDataset = (event) => {
  let datasetIds = event.value.map((item) => item.dataset_id)
  emit('selectedDataset', datasetIds)
}

const updateOrganism = () => {
  selectedOrganism.value = undefined
  selectedModification.value = undefined
  selectedTechnology.value = undefined
  selectedDataset.value = undefined
  var options = props.selectOptions.filter(
    (item) => item.taxa_sname === selectedSpecies.value.label
  )
  organism.value = toTree(options, ['cto'], 'organism_id')
  updateDataset()
  emitSelectedSpecies()
}

const updateModification = () => {
  selectedModification.value = undefined
  selectedTechnology.value = undefined
  selectedDataset.value = undefined
  var selectedOrganismIds = selectedOrganism.value.map((item) => item.key)
  var options = props.selectOptions.filter((item) => selectedOrganismIds.includes(item.organism_id))
  modification.value = toTree(options, ['rna', 'modomics_sname'], 'modification_id')
  updateDataset()
}

const updateTechnology = () => {
  selectedTechnology.value = undefined
  selectedDataset.value = undefined
  var selectedModificationIds = toIds(
    selectedModification.value,
    Array.from(new Set(props.selectOptions.map((item) => item.modification_id)))
  )
  var selectedOrganismIds = selectedOrganism.value.map((item) => item.key)
  var options = props.selectOptions.filter(
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
    Array.from(new Set(props.selectOptions.map((item) => item.modification_id)))
  )
  var selectedTechnologyIds = toIds(
    selectedTechnology.value,
    Array.from(new Set(props.selectOptions.map((item) => item.technology_id)))
  )
  var selectedOrganismIds =
    Object.is(selectedOrganism.value, undefined) || selectedOrganism.value.length === 0
      ? organism.value.map((item) => item.key)
      : selectedOrganism.value.map((item) => item.key)
  var options = props.selectDataset.filter(
    (item) =>
      selectedModificationIds.includes(item.modification_id) &&
      selectedTechnologyIds.includes(item.technology_id) &&
      selectedOrganismIds.includes(item.organism_id)
  )
  dataset.value = [...new Map(options.map((item) => [item['dataset_id'], item])).values()].map(
    (item) => {
      return { dataset_id: item.dataset_id, dataset_title: item.dataset_title }
    }
  )
}

function toTree(data, keys, id) {
  var len = keys.length - 1
  var tree = data.reduce((r, o) => {
    keys.reduce((t, k, idx) => {
      var jdx = idx === len ? id : k
      var tmp = (t.children = t.children || []).find((p) => p.key === o[jdx])
      if (!tmp) {
        t.children.push((tmp = { key: o[jdx], label: o[k] }))
      }
      return tmp
    }, r)
    return r
  }, {}).children
  return tree
}

function toIds(array, defaultArray) {
  if (!(array === undefined || Object.keys(array).length === 0)) {
    return Object.keys(array)
      .map(Number)
      .filter((value) => !Number.isNaN(value))
  }
  return defaultArray
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
        root: { class: 'w-full md:w-full' },
        item: ({ context }) => ({
          class: [
            {
              'text-gray-700 hover:text-gray-700 hover:bg-[#72bf84]':
                !context.focused && !context.selected,
              'bg-[#ffffff] text-gray-700 hover:text-gray-700 hover:bg-[#00b051]':
                context.focused && !context.selected,
              'bg-[#00b051] text-gray-50': context.focused && context.selected,
              'bg-[#ffffff] text-gray-800': !context.focused && context.selected
            }
          ]
        })
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
        root: { class: 'w-full md:w-full' },
        item: ({ props, state, context }) => ({
          class: [
            {
              'text-gray-700 hover:text-gray-700 hover:bg-[#72bf84]':
                !context.focused && !context.selected,
              'bg-[#ffffff] text-gray-700 hover:text-gray-700 hover:bg-[#00b051]':
                context.focused && !context.selected,
              'bg-[#fffffe] text-gray-800': context.focused && context.selected,
              'bg-[#ffffff] text-gray-800': !context.focused && context.selected
            }
          ]
        }),
        headerCheckbox: ({ context }) => ({
          class: [
            'hover:border-crmapgreen1 focus:outline-none focus:outline-offset-0 focus:shadow-[0_0_0_0.2rem_rgba(114,191,132,1)]',
            {
              'border-gray-300 bg-white': !context?.selected,
              'border-crmapgreen1 bg-crmapgreen1': context?.selected
            }
          ]
        }),
        checkbox: ({ context }) => ({
          class: [
            'hover:border-crmapgreen1 focus:outline-none focus:outline-offset-0 focus:shadow-[0_0_0_0.2rem_rgba(114,191,132,1)]',
            {
              'border-gray-300 bg-white': !context?.selected,
              'border-crmapgreen1 bg-crmapgreen1': context?.selected
            }
          ]
        })
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
      @change="emitSelectedDataset"
      v-model="selectedDataset"
      :options="dataset"
      filter
      optionLabel="dataset_title"
      placeholder="5. Select dataset"
      :maxSelectedLabels="3"
      :pt="{
        root: { class: 'col-span-4 md:w-full' },
        item: ({ props, state, context }) => ({
          class: [
            {
              'text-gray-700 hover:text-gray-700 hover:bg-[#72bf84]':
                !context.focused && !context.selected,
              'bg-[#ffffff] text-gray-700 hover:text-gray-700 hover:bg-[#00b051]':
                context.focused && !context.selected,
              'bg-[#fffffe] text-gray-800': context.focused && context.selected,
              'bg-[#ffffff] text-gray-800': !context.focused && context.selected
            }
          ]
        }),
        headerCheckbox: ({ context }) => ({
          class: [
            'hover:border-crmapgreen1 focus:outline-none focus:outline-offset-0 focus:shadow-[0_0_0_0.2rem_rgba(114,191,132,1)]',
            {
              'border-gray-300 bg-white': !context?.selected,
              'border-crmapgreen1 bg-crmapgreen1': context?.selected
            }
          ]
        }),
        checkbox: ({ context }) => ({
          class: [
            'hover:border-crmapgreen1 focus:outline-none focus:outline-offset-0 focus:shadow-[0_0_0_0.2rem_rgba(114,191,132,1)]',
            {
              'border-gray-300 bg-white': !context?.selected,
              'border-crmapgreen1 bg-crmapgreen1': context?.selected
            }
          ]
        }),
        filtercontainer: { class: 'md:w-full' },
        filtericon: {
          class: 'relative float-right mt-[1.15rem] mr-2'
        }
      }"
    />
  </div>
</template>
