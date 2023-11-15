<script setup>
import { ref, watch, watchEffect } from 'vue'

const modification = ref()
const selectedModification = ref()
const technology = ref()
const selectedTechnology = ref()
const organism = ref()
const selectedOrganism = ref()
const dataset = ref()
const selectedDataset = ref()

const props = defineProps({
  selectedSpecies: {
    type: String,
    required: true
  },
  selectOptions: {
    type: Array,
    required: true
  },
  referenceDataset: {
    type: Array,
    required: true
  }
})

watch(
  () => props.selectedSpecies,
  () => {
    var options = props.selectOptions.filter((item) => item.taxa_sname === props.selectedSpecies)
    organism.value = toTree(options, ['cto'], 'organism_id')
    modification.value = undefined
    technology.value = undefined
    selectedOrganism.value = undefined
    selectedModification.value = undefined
    selectedTechnology.value = undefined
    updateDataset()
  },
  { immediate: true }
)

// watch(selectedSpecies, () => {
//   var options = props.selectOptions.filter(
//     (item) => item.taxa_sname === props.selectedSpecies
//   )
//   organism.value = toTree(options, ['cto'], 'organism_id')
//   updateDataset()
//   selectedOrganism.value = undefined
//   selectedModification.value = undefined
//   selectedTechnology.value = undefined
//   // selectedDataset.value = undefined
//   console.log('prop value changed', props.selectedSpecies)
//   modification.value = undefined
//   technology.value = undefined
// })

// watchEffect(() => {
//   var options = props.selectOptions.filter(
//     (item) => item.taxa_sname === props.selectedSpecies
//   )
//   organism.value = toTree(options, ['cto'], 'organism_id')
//   updateDataset()
//   selectedOrganism.value = undefined
//   selectedModification.value = undefined
//   selectedTechnology.value = undefined
//   // selectedDataset.value = undefined
//   console.log('prop value changed', props.selectedSpecies)
//   modification.value = undefined
//   technology.value = undefined
//   // updateDataset()
// }
// )

const emit = defineEmits(['selectedDataset'])

const emitSelectedDataset = (event) => {
  let datasetIds = event.value.map((item) => item.dataset_id)
  emit('selectedDataset', datasetIds)
}

// const updateOrganism = () => {
//   var options = props.selectOptions.filter(
//     (item) => item.taxa_sname === props.selectedSpecies
//   )
//   organism.value = toTree(options, ['cto'], 'organism_id')
// }
// updateOrganism()

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
  var options = props.referenceDataset.filter(
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
  <div class="grid grid-flow-row-dense grid-cols-6 grid-row-2 gap-6">
    <FileUpload
      name="file"
      url="http://127.0.0.1:5000/api/v0/upload"
      :multiple="false"
      accept="text/plain,.bed,.bedrmod"
      :maxFileSize="1000000"
      :pt="{
        content: { class: 'surface-ground' }
      }"
    >
      <template #empty>
        <p>Drag and drop files to here to upload.</p>
      </template>
    </FileUpload>
    <MultiSelect
      @change="updateModification"
      v-model="selectedOrganism"
      :options="organism"
      optionLabel="label"
      placeholder="1. Select cell/tissue"
      :maxSelectedLabels="3"
    />
    <div class="col-span-2">
      <TreeSelect
        @change="updateTechnology"
        v-model="selectedModification"
        :options="modification"
        selectionMode="checkbox"
        :metaKeySelection="false"
        placeholder="2. Select RNA modifications"
      />
    </div>
    <div class="cold-span-2">
      <TreeSelect
        @change="updateDataset"
        v-model="selectedTechnology"
        :options="technology"
        selectionMode="checkbox"
        :metaKeySelection="false"
        placeholder="3. Select technologies"
      />
    </div>
    <div class="col-span-6 w-full">
      <MultiSelect
        @change="emitSelectedDataset"
        v-model="selectedDataset"
        :options="dataset"
        filter
        optionLabel="dataset_title"
        placeholder="4. Select dataset"
        :maxSelectedLabels="3"
        :pt="{
          root: { class: 'md:w-full' },
          item: ({ props, state, context }) => ({
            class: context.selected ? 'bg-blue-300' : context.focused ? 'bg-blue-100' : undefined
          })
        }"
      />
    </div>
  </div>
</template>
